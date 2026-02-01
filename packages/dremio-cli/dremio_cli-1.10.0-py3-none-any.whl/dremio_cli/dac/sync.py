
import os
import yaml
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from dremio_cli.dac.config import DremioConfig
from dremio_cli.dac.state import LocalState
from dremio_cli.dac.graph import DependencyGraph
from dremio_cli.client.software import SoftwareClient
from dremio_cli.client.cloud import CloudClient
from dremio_cli.utils.console import console

class DremioSync:
    def __init__(self, config: DremioConfig, client, root_dir: str):
        self.config = config
        self.client = client
        self.root_dir = root_dir
        self.state = LocalState(root_dir)
        self.state.load()

    def pull(self):
        """Pull state from Dremio to local filesystem."""
        console.print(f"[bold blue]Syncing Pull...[/bold blue]")
        console.print(f"Scope: {self.config.scope.path} ({self.config.scope.type})")
        
        try:
            root_entity = self._fetch_entity_by_path(self.config.scope.path)
            if not root_entity:
                 console.print(f"[red]Could not find entity at path: {self.config.scope.path}[/red]")
                 return

            console.print(f"Found root entity: {root_entity.get('id')} ({root_entity.get('entityType', 'Unknown')})")
            
            # Recursive Traversal
            self._traverse_and_sync(root_entity, parent_local_path=Path(self.root_dir))
            
            self.state.save()
            console.print(f"[bold green]Pull Complete.[/bold green]")

        except Exception as e:
            console.print(f"[red]Sync failed: {e}[/red]")
            # import traceback; traceback.print_exc()

    def push(self, dry_run: bool = False):
        """Push local state to Dremio."""
        console.print(f"[bold blue]Syncing Push (Dry Run: {dry_run})...[/bold blue]")
        
        # 1. Scan Local Files
        local_resources = self.state.scan_filesystem()
        if not local_resources:
            console.print("[yellow]No local resources found to sync.[/yellow]")
            return

        # 2. Build Dependency Graph
        # Convert dict items to list for graph
        # We need to ensure 'name' matches what 'dependencies' refer to.
        # Ideally user uses names in dependencies.
        items = list(local_resources.values())
        
        try:
            graph = DependencyGraph(items)
            sorted_items = graph.get_execution_order()
        except ValueError as e:
            console.print(f"[red]Dependency Error: {e}[/red]")
            return

        # 3. Execution (Sorted)
        changes = 0
        
        for data in sorted_items:
            # Resolve full path first
            # If path not in YAML, derive it from Root + Relative Dir (?)
            # For now, simplistic: We assume 'path' is mostly present or we skip.
            # Ideally scan_filesystem provides 'path' if not in YAML?
            # Let's rely on 'path' being in data (state.py logic or user provided)
            
            path_list = data.get("path")
            if not path_list:
                # If path missing, we can try to guess but better to warn
                # For root items 'name' might be enough if under root.
                if data.get("name"):
                    # Assuming relative to Scope Root?
                    # This is tricky without explicit path.
                    # Let's Skip for now if no path.
                    console.print(f"[yellow]Skipping {data.get('name')}: No 'path' defined.[/yellow]")
                    continue
                continue

            path_key = ".".join(path_list)
            
            # Check existance
            # Try to fetch from Dremio to see if exists (or check state)
            # Checking state is faster but might be stale.
            # Let's check State first.
            # Check existance
            # Try to fetch from Dremio to see if exists (to support adoption)
            existing_state = self.state.get_resource(path_list)
            existing_remote = self._fetch_entity_by_path(path_key)
            
            if existing_remote:
                 # Update / Adopt
                 new_hash = self._calculate_hash(data)
                 # Update if state missing (adoption) or hash changed
                 if not existing_state or existing_state.hash != new_hash:
                      self._apply_update(data, existing_remote["id"], dry_run)
                      changes += 1
                 else:
                      console.print(f"Skipping {path_key}: Up to date.")
            else:
                 # Create
                 self._apply_create(data, dry_run)
                 changes += 1

        if changes == 0:
            console.print("No changes detected.")
        else:
            if not dry_run:
                self.state.save()
            console.print(f"[bold green]Push Complete. {changes} changes applied.[/bold green]")

    def _calculate_hash(self, data):
        """Calculate hash of resource content."""
        content = ""
        content += data.get("sql_content", "")
        content += str(data.get("context", []))
        content += str(data.get("tags", []))
        content += data.get("description", "")
        content += str(data.get("access_control", ""))
        content += str(data.get("governance", ""))
        content += str(data.get("reflections", ""))
        content += str(data.get("config", ""))
        content += str(data.get("create_sql", ""))
        content += str(data.get("update_sql", ""))
        content += str(data.get("validations", ""))
        return str(hash(content))

    def _substitute_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively substitute env vars in config values."""
        import os
        import re
        new_config = {}
        # Pattern: ${VAR_NAME}
        pattern = re.compile(r'\$\{([^}]+)\}')
        
        for k, v in config.items():
            if isinstance(v, dict):
                new_config[k] = self._substitute_env_vars(v)
            elif isinstance(v, str):
                # Replace all occurrences
                def replace_match(match):
                    var_name = match.group(1)
                    val = os.getenv(var_name)
                    if val is None:
                        console.print(f"[yellow]Warning: Env var {var_name} not found.[/yellow]")
                        return match.group(0) # Keep original if not found
                    return val
                new_config[k] = pattern.sub(replace_match, v)
            else:
                new_config[k] = v
        return new_config

    def _apply_create(self, data, dry_run):
        r_type = data.get("type")
        path = data.get("path")
        
        console.print(f"[green]+ CREATE[/green] {'.'.join(path)} ({r_type})")
        if r_type == "ICEBERG_TABLE":
             # console.print(f"DEBUG DATA: {data}")
             pass

        if dry_run: return

        # Ensure parent folders exist (skip if root or Source)
        if len(path) > 1 and r_type not in ["SOURCE", "HOME"]:
             self._ensure_parent_folders(path[:-1])

        try:
            new_id = None
            
            if r_type == "SOURCE":
                source_config = self._substitute_env_vars(data.get("config", {}))
                
                payload = {
                    "name": data.get("name"),
                    "type": data.get("source_type") or data.get("type_code"), # e.g. 'S3', 'NAS'
                    "config": source_config,
                    "metadataPolicy": data.get("metadata_policy")
                }
                # Remove None values
                payload = {k: v for k, v in payload.items() if v is not None}
                
                res = self.client.create_source(payload)
                new_id = res.get("id")

            elif r_type == "SPACE":
                payload = {"name": path[-1]}
                res = self.client.create_space(payload)
                new_id = res.get("id")

            elif r_type in ["FOLDER"]: 
                payload = {"path": path}
                res = self.client.create_folder(payload)
                new_id = res.get("id")
            
            elif r_type in ["VIEW", "VIRTUAL_DATASET", "VIRTUAL"]:
                payload = {
                    "path": path,
                    "sql": data.get("sql_content"),
                    "sqlContext": data.get("context", []),
                    "type": "VIRTUAL_DATASET",
                    "entityType": "dataset"
                }
                # Create methods may differ by client version/type
                if hasattr(self.client, "create_view"):
                     res = self.client.create_view(payload)
                else:
                     res = self.client.create_catalog(payload)
                new_id = res.get("id")

            elif r_type == "ICEBERG_TABLE":
                # Create via SQL (CTAS or CREATE TABLE)
                create_sql = data.get("create_sql")
                if create_sql:
                    console.print(f"Executing Create SQL for {'.'.join(path)}")
                    self.client.execute_sql(create_sql)
                    # Fetch ID after creation
                    try:
                        # Need to wait? SQL might be async. Client.execute_sql usually synchronous-ish or returns job.
                        # We might need a retry or simple fetch.
                        import time
                        time.sleep(1) # Brief pause for reflection in catalog
                        item = self._fetch_entity_by_path(".".join(path))
                        if item: 
                            new_id = item.get("id")
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not fetch ID after create sql: {e}[/yellow]")
                else:
                     console.print("[yellow]Warning: ICEBERG_TABLE missing create_sql. Skipping creation.[/yellow]")
            
            elif r_type == "PHYSICAL_DATASET":
                # Already exists? If we are in _apply_create, it means missing from local state tracking?
                # Or missing from Remote?
                # If Missing Remote: We cannot "Create" a PDS usually without format promotion.
                # Assuming user ensures it exists or we support 'format'.
                # For now: Try to fetch. If not found, warn.
                item = self._fetch_entity_by_path(".".join(path))
                if item:
                    new_id = item.get("id")
                else:
                    console.print("[yellow]PDS not found. Promoting PDS via API not fully implemented. Please ensure PDS exists.[/yellow]")
            
            # Apply Tags & Wiki & Governance
            if new_id:
                if "tags" in data:
                    self.client.set_tags(new_id, data["tags"])
                if "description" in data:
                    self.client.set_wiki(new_id, data["description"])
                
                # Governance
                if "access_control" in data:
                    self._apply_access_control(new_id, data)
                if "governance" in data:
                    self._apply_governance(path, data)
                
                # Reflections
                if "reflections" in data:
                    self._manage_reflections(new_id, data)
                
                # Validations (Run last)
                if "validations" in data:
                    self._run_validations(data)

                # Update State
                if new_id:
                    new_hash = self._calculate_hash(data)
                    self.state.update_resource(path, r_type, new_id, new_hash, data)

        except Exception as e:
            console.print(f"[red]Failed to create {path}: {e}[/red]")

    def _apply_update(self, data, id, dry_run):
        path = data.get("path")
        console.print(f"[yellow]* UPDATE[/yellow] {'.'.join(path)}")
        
        if dry_run: return

        try:
            r_type = data.get("type")
            
            if r_type == "SOURCE":
                # Update Source
                # Need tag?
                current = self.client.get_catalog_item(id)
                tag = current.get("tag")
                source_config = self._substitute_env_vars(data.get("config", {}))
                
                payload = {
                    "id": id,
                    "tag": tag, 
                    "name": data.get("name"),
                    "type": data.get("source_type") or data.get("type_code"),
                    "config": source_config,
                    "metadataPolicy": data.get("metadata_policy")
                }
                payload = {k: v for k, v in payload.items() if v is not None}
                self.client.update_source(id, payload)

            elif r_type == "ICEBERG_TABLE":
                # Run Update SQL (Incremental Load)
                update_sql = data.get("update_sql")
                if update_sql:
                    console.print(f"Executing Update SQL for {'.'.join(path)}")
                    self.client.execute_sql(update_sql)
                # No content update API for iceberg, just SQL.

            elif r_type == "PHYSICAL_DATASET":
                 pass # Read-only nature usually. Just tags/gov.

            # Update Content
            elif r_type in ["VIEW", "VIRTUAL_DATASET", "VIRTUAL"]:
                # Get Tag for optimistic lock
                current = self.client.get_catalog_item(id)
                tag = current.get("tag")
                
                payload = {
                    "id": id,
                    "path": path,
                    "entityType": "dataset",
                    "type": "VIRTUAL_DATASET",
                    "sql": data.get("sql_content"),
                    "sqlContext": data.get("context", []),
                    "tag": tag
                }
                
                self.client.update_view(id, payload)

            # Update Tags & Wiki (Always applied on update to ensure sync)
            if "tags" in data:
                self.client.set_tags(id, data["tags"])
            if "description" in data:
                self.client.set_wiki(id, data["description"])
            
            # Update Governance
            if "access_control" in data:
                self._apply_access_control(id, data)
            if "governance" in data:
                self._apply_governance(path, data)

            # Update Reflections
            if "reflections" in data:
                self._manage_reflections(id, data)

            # Validations
            if "validations" in data:
                self._run_validations(data)

            # Update State
            new_hash = self._calculate_hash(data)
            self.state.update_resource(path, data.get("type"), id, new_hash, data)

        except Exception as e:
            console.print(f"[red]Failed to update {path}: {e}[/red]")

    def _apply_access_control(self, entity_id: str, data: Dict[str, Any]):
        """Apply RBAC grants."""
        ac = data.get("access_control")
        if not ac: return

        # Need to resolve names to IDs.
        # This is expensive if done per item. Should cache.
        if not hasattr(self, "_user_cache"):
            self._build_principal_cache()
            
        grants = []
        
        # Roles
        for role_def in ac.get("roles", []):
            rid = self._role_name_to_id.get(role_def["name"])
            if rid:
                grants.append({
                    "granteeType": "ROLE",
                    "granteeId": rid,
                    "privileges": role_def["privileges"]
                })
            else:
                console.print(f"[yellow]Warning: Role '{role_def['name']}' not found. Skipping grant.[/yellow]")

        # Users
        for user_def in ac.get("users", []):
            uid = self._user_name_to_id.get(user_def["name"])
            if uid:
                grants.append({
                    "granteeType": "USER",
                    "granteeId": uid,
                    "privileges": user_def["privileges"]
                })
            else:
                 console.print(f"[yellow]Warning: User '{user_def['name']}' not found. Skipping grant.[/yellow]")
                 
        if grants:
            try:
                # Payload structure depends on API. 
                # Software: {"grants": [...], "version": ...}
                # Cloud: might be similar.
                # Client set_grants expects 'grants_data'.
                # Let's verify existing grants to get version (for optimistic lock) if needed?
                # set_grants doc says "replaces existing".
                # We construct payload.
                payload = {"grants": grants}
                # Some APIs need "entityId.version" tag? 
                # Software often needs 'tag' parameter effectively.
                # Let's try sending just grants list wrapper.
                self.client.set_grants(entity_id, payload)
                console.print(f"Applied Access Control for {entity_id}")
            except Exception as e:
                console.print(f"[red]Failed to set grants: {e}[/red]")

    def _apply_governance(self, path_list: List[str], data: Dict[str, Any]):
        """Apply Row Access & Masking Policies via SQL."""
        gov = data.get("governance")
        if not gov: return
        
        full_path = f'"{path_list[0]}"'
        for p in path_list[1:]:
            full_path += f'."{p}"'
            
        # Row Access Policy
        rap = gov.get("row_access_policy")
        if rap:
            policy_name = rap["name"]
            args = ",".join(rap.get("args", []))
            sql = f"ALTER VIEW {full_path} ADD ROW ACCESS POLICY {policy_name}({args})"
            try:
                self.client.execute_sql(sql)
                console.print(f"Applied Row Access Policy: {policy_name}")
            except Exception as e:
                console.print(f"[red]Failed to apply RAP: {e}[/red]")

        # Masking Policies
        for mask in gov.get("masking_policies", []):
            col = mask["column"]
            policy_name = mask["name"]
            args = ",".join(mask.get("args", []))
            # ALTER VIEW path MODIFY COLUMN col SET MASKING POLICY policy(args)
            sql = f"ALTER VIEW {full_path} MODIFY COLUMN \"{col}\" SET MASKING POLICY {policy_name}({args})"
            try:
                self.client.execute_sql(sql)
                console.print(f"Applied Masking Policy on {col}: {policy_name}")
            except Exception as e:
                console.print(f"[red]Failed to apply Masking on {col}: {e}[/red]")

    def _manage_reflections(self, dataset_id: str, data: Dict[str, Any]):
        """Sync Reflections for a dataset."""
        yaml_reflections = data.get("reflections", [])
        if not yaml_reflections:
            return

        console.print(f"Syncing {len(yaml_reflections)} reflections...")
        
        # 1. Get existing reflections for this dataset
        # Warning: This implementation lists all and filters. 
        # Optimization: Client should support filtering by datasetId parameter if API allows.
        # For now, we assume list_reflections returns a list we can iterate.
        try:
            ignore = self.client.list_reflections() # dummy call to check method? 
            # Ideally we pass params={"datasetId": dataset_id} to underlying call
            # But client methods don't expose params kwarg directly in signatures seen.
            # We will use a hack or assume lightweight catalog for now.
            # If Client base.get supports kwargs, we might need to bypass.
            # Let's try iterating.
            
            all_refs = []
            res = self.client.list_reflections()
            if isinstance(res, dict) and "data" in res:
                all_refs = res["data"]
            elif isinstance(res, list):
                all_refs = res
            
            existing_map = {} # Name -> ID
            for r in all_refs:
                if r.get("datasetId") == dataset_id:
                    existing_map[r.get("name")] = r
            
            # 2. Sync
            for y_ref in yaml_reflections:
                r_name = y_ref.get("name")
                if not r_name:
                    console.print("[yellow]Warning: Reflection missing name in YAML. Skipping.[/yellow]")
                    continue
                
                payload = y_ref.copy()
                payload["datasetId"] = dataset_id
                
                # Check existing
                existing = existing_map.get(r_name)
                
                if existing:
                    # Update
                    # We should check if changed, but for now we Update to ensure state
                    # Need reflection ID
                    rid = existing["id"]
                    # payload["id"] = rid # usually not in body for update but path
                    # Tag required?
                    payload["tag"] = existing.get("tag")
                    try:
                        self.client.update_reflection(rid, payload)
                        console.print(f"Updated Reflection: {r_name}")
                    except Exception as e:
                         console.print(f"[red]Failed update reflection {r_name}: {e}[/red]")
                else:
                    # Create
                    try:
                        self.client.create_reflection(payload)
                        console.print(f"Created Reflection: {r_name}")
                    except Exception as e:
                         console.print(f"[red]Failed create reflection {r_name}: {e}[/red]")
                         
        except Exception as e:
            console.print(f"[yellow]Warning: Reflection sync failed: {e}[/yellow]")

    def _run_validations(self, data: Dict[str, Any]):
        """Run SQL assertions after sync."""
        vals = data.get("validations", [])
        if not vals: return
        
        console.print(f"Running {len(vals)} validations...")
        for v in vals:
            name = v.get("name", "unnamed")
            sql = v.get("sql")
            condition = v.get("condition") # e.g. "gt 0", "eq 0"
            
            try:
                # Execute SQL
                # result is usually dict or job results
                # We need scalar result?
                # Dremio client execute_sql might return jobid or results
                # Need to fetch results
                job = self.client.execute_sql(sql)
                # Assume job is dict with 'id'
                if isinstance(job, dict) and "id" in job:
                     job_id = job["id"]
                     # Fetch results
                     # Usually need to wait for completion.
                     # Sync implementation might need better polling.
                     # Assuming fast execution for validation. 
                     # For now, let's skip complex job polling implementation in 'sync' class unless available.
                     # Client should have 'get_job_results'
                     import time
                     # Simple poll
                     status = "RUNNING"
                     while status in ["RUNNING", "QUEUED", "PENDING"]:
                         j = self.client.get_job(job_id)
                         status = j.get("jobState", "COMPLETED") # fallback
                         if status in ["COMPLETED", "FAILED", "CANCELED"]: break
                         time.sleep(0.5)
                     
                     if status != "COMPLETED":
                         console.print(f"[red][FAIL] {name}: Job failed/canceled[/red]")
                         continue
                     
                     results = self.client.get_job_results(job_id, limit=1)
                     # Dict with 'rows' or list
                     rows = results.get("rows", [])
                     val = 0
                     if rows:
                         # Get first value of first row
                         first_row = rows[0]
                         val = list(first_row.values())[0] # Assume scalar
                     
                     # Check condition
                     parts = condition.split(" ")
                     op = parts[0]
                     target = float(parts[1]) if len(parts)>1 else 0
                     actual = float(val) if val is not None else 0
                     
                     passed = False
                     if op == "gt": passed = actual > target
                     elif op == "lt": passed = actual < target
                     elif op == "eq": passed = actual == target
                     elif op == "neq": passed = actual != target
                     
                     if passed:
                         console.print(f"[green][PASS] {name}[/green]")
                     else:
                         console.print(f"[red][FAIL] {name}: Expected {condition}, got {actual}[/red]")

            except Exception as e:
                 console.print(f"[red][ERR] {name}: {e}[/red]")

    def _build_principal_cache(self):
        console.print("Caching Users and Roles...")
        self._user_name_to_id = {}
        self._role_name_to_id = {}
        
        try:
            # Users
            # API response structure: {"data": [{"id":..., "name":...}]} usually
            u_res = self.client.list_users()
            users = u_res.get("data", []) if "data" in u_res else u_res
            for u in users:
                # Cloud uses email often, Software uses name
                key = u.get("name") or u.get("email")
                if key: self._user_name_to_id[key] = u["id"]
                
            # Roles
            r_res = self.client.list_roles()
            roles = r_res.get("data", []) if "data" in r_res else r_res
            for r in roles:
                self._role_name_to_id[r["name"]] = r["id"]
                
        except Exception as e:
            console.print(f"[yellow]Warning: Could not build principal cache: {e}. RBAC may fail.[/yellow]")

    def _ensure_parent_folders(self, path_list: List[str]):
        """Recursively ensure folders exist."""
        # path_list is full path to parent: e.g. ["source", "f1"]
        # We process incrementally: "source", "source.f1"
        
        if not path_list: return
        
        # Assume Root (first element) exists (Space/Source/Home)
        current_path = [path_list[0]]
        
        for folder in path_list[1:]:
            current_path.append(folder)
            p_str = ".".join(current_path)
            
            # Check existence
            try:
                # We use specific check or assumption
                found = self._fetch_entity_by_path(p_str)
                if found: continue
            except:
                pass
            
            # Not found, create
            console.print(f"Creating implicit folder: {p_str}")
            try:
                self.client.create_folder({"path": current_path})
            except Exception as e:
                # If creating explicitly fails, maybe it exists but fetch failed?
                # Or parent issues.
                console.print(f"[yellow]Warning: Failed to create folder {p_str}: {e}[/yellow]")

    def _fetch_entity_by_path(self, path: str):
         # Normalize path str for API calls (slash delimited for by-path)
         # Hacky: replace . with / but careful with quotes?
         # Testing env paths are simple.
         slash_path = path.replace(".", "/")
         
         # Try client specific by-path if available
         if hasattr(self.client, "get_catalog_item_by_path"):
            try:
                # Need to handle potential leading slash or project prefix
                # console.print(f"DEBUG FETCH {slash_path}: {item}")
                return item
            except Exception as e:
                # console.print(f"DEBUG FETCH ERR {slash_path}: {e}")
                pass
        
         # Fallback to catalog root scan/drilldown (Software V2 / Cloud V0)
         # We need to find the ID by traversing from root.
         parts = path.split(".")
         try:
            # Get Root
            res = self.client.get_catalog()
            items = res.get("data", []) if "data" in res else res.get("children", [])
            current_id = None
            
            # Find first part
            for item in items:
                # Check id or name or path depending on what get_catalog returns
                # Usually: {"id": "...", "path": ["space"], "type": "SPACE"}
                p = item.get("path", [])
                # console.print(f"DEBUG ROOT: {p} vs {parts[0]}")
                if p and p[-1] == parts[0]:
                    current_id = item["id"]
                    break
            
            if not current_id: return None
            
            # Traverse remaining
            for part in parts[1:]:
                # List children of current_id
                # Software: get_catalog_item(id) returns children in data?
                # or children list
                entity = self.client.get_catalog_item(current_id)
                # console.print(f"DEBUG ENTITY {current_id}: {entity}")
                children = entity.get("children", [])
                found_child = False
                for child in children:
                     p = child.get("path", [])
                     # console.print(f"DEBUG CHILD: {p[-1]} vs {part}")
                     if p and p[-1] == part:
                         current_id = child["id"]
                         found_child = True
                         break
                
                if not found_child: return None
                
            # If we are here, current_id is the target
            return self.client.get_catalog_item(current_id)

         except Exception as e:
             # console.print(f"[debug] Lookup failed for {path}: {e}")
             pass
             
         return None

    def _traverse_and_sync(self, entity, parent_local_path: Path):
        entity_type = entity.get("entityType")
        entity_path = entity.get("path", [])
        entity_id = entity.get("id")
        entity_name = entity_path[-1] if entity_path else "unknown"
        
        is_root = ".".join(entity_path) == self.config.scope.path
        
        current_local_path = parent_local_path
        if not is_root and entity_type in ["SPACE", "FOLDER", "SOURCE", "HOME"]:
             current_local_path = parent_local_path / entity_name
             if not current_local_path.exists():
                 current_local_path.mkdir(exist_ok=True)
                 
        if entity_type == "dataset":
             d_type = entity.get("type")
             if d_type in ["VIRTUAL", "VIRTUAL_DATASET"]:
                 self._sync_view(entity, parent_local_path)
             else:
                 # Physical
                 self._sync_physical_dataset(entity, parent_local_path)
            
        elif entity_type in ["space", "folder", "source", "home", "container"]:
            # Fetch children
            # Sometimes 'children' key is missing, fetch by ID
            try:
                full = self.client.get_catalog_item(entity_id)
                children = full.get("children", [])
            except:
                children = []
                
            for child in children:
                self._traverse_and_sync(child, current_local_path)

    def _sync_view(self, view_entity, local_path: Path):
        view_id = view_entity.get("id")
        try:
            full_view = self.client.get_catalog_item(view_id)
            name = full_view.get("path")[-1]
            sql = full_view.get("sql")
            context = full_view.get("sqlContext", [])
            
            # Fetch Tags & Wiki
            tags = []
            try:
                t_res = self.client.get_tags(view_id)
                tags = t_res.get("tags", [])
            except: pass
            
            wiki_text = ""
            try:
                w_res = self.client.get_wiki(view_id)
                wiki_text = w_res.get("text", "")
            except: pass

            # Write Wiki File if exists
            wiki_filename = None
            if wiki_text:
                wiki_filename = f"{name}.md"
                with open(local_path / wiki_filename, "w") as f:
                    f.write(wiki_text)

            # Write YAML
            metadata = {
                "name": name,
                "type": "VIRTUAL_DATASET", # Standardize
                "path": full_view.get("path"),
                "context": context,
                "sql": sql,
                "tags": tags
            }
            if wiki_filename:
                metadata["description"] = wiki_filename
            
            # Note: Governance/Reflections not currently pulled.

            yaml_file = local_path / f"{name}.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(metadata, f, sort_keys=False)
                
            # Update State
            content_hash = self._calculate_hash(metadata)
            self.state.update_resource(full_view.get("path"), "VIEW", view_id, content_hash, metadata)
            console.print(f"Synced View: {name}")

        except Exception as e:
            console.print(f"[red]Error syncing view {view_id}: {e}[/red]")

    def _sync_physical_dataset(self, entity, local_path: Path):
        p_id = entity.get("id")
        try:
            full = self.client.get_catalog_item(p_id)
            name = full.get("path")[-1]
            d_type = full.get("type")
            
            # Determine DAC Type
            dac_type = "PHYSICAL_DATASET"
            
            # Check format for Iceberg
            fmt = full.get("format", {})
            if fmt.get("type") == "Iceberg":
                dac_type = "ICEBERG_TABLE"
            elif d_type == "ICEBERG_TABLE": # Native Cloud type
                dac_type = "ICEBERG_TABLE"

            # Fetch Tags & Wiki
            tags = []
            try:
                t_res = self.client.get_tags(p_id)
                tags = t_res.get("tags", [])
            except: pass
            
            wiki_text = ""
            try:
                w_res = self.client.get_wiki(p_id)
                wiki_text = w_res.get("text", "")
            except: pass
            
            wiki_filename = None
            if wiki_text:
                wiki_filename = f"{name}.md"
                with open(local_path / wiki_filename, "w") as f:
                    f.write(wiki_text)

            # Build YAML
            metadata = {
                "name": name,
                "type": dac_type,
                "path": full.get("path"),
                "tags": tags
            }
            if wiki_filename:
                metadata["description"] = wiki_filename
            
            if dac_type == "ICEBERG_TABLE":
                metadata["create_sql"] = "# CREATE TABLE ..."
                metadata["update_sql"] = "# INSERT INTO ..."
            else:
                if fmt:
                    metadata["format"] = fmt

            yaml_file = local_path / f"{name}.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(metadata, f, sort_keys=False)

            # Update State
            content_hash = self._calculate_hash(metadata)
            self.state.update_resource(full.get("path"), dac_type, p_id, content_hash, metadata)
            console.print(f"Synced Physical: {name} ({dac_type})")
            
        except Exception as e:
            console.print(f"[red]Error syncing physical {p_id}: {e}[/red]")

