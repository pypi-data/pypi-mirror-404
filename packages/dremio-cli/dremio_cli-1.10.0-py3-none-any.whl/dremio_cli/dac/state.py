
import os
import json
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ResourceState:
    id: str
    path: List[str]
    type: str # DATASET, FOLDER, SPACE, SOURCE, VIEW (Specific)
    hash: str # Content hash for change detection
    metadata: Dict[str, Any]

class LocalState:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.state_file = os.path.join(root_path, ".dremio_state.json")
        self.resources: Dict[str, ResourceState] = {} # Keyed by path string "space.folder.view"

    def load(self):
        """Load state from .dremio_state.json"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    for key, item in data.items():
                        self.resources[key] = ResourceState(**item)
            except Exception as e:
                print(f"Warning: Could not load state file: {e}")

    def save(self):
        """Save state to .dremio_state.json"""
        data = {k: asdict(v) for k, v in self.resources.items()}
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update_resource(self, path_list: List[str], type: str, id: str, hash: str, metadata: Dict[str, Any]):
        key = ".".join(path_list)
        self.resources[key] = ResourceState(
            id=id,
            path=path_list,
            type=type,
            hash=hash,
            metadata=metadata
        )
    
    def get_resource(self, path_list: List[str]) -> Optional[ResourceState]:
        key = ".".join(path_list)
        return self.resources.get(key)

    def remove_resource(self, path_list: List[str]):
        key = ".".join(path_list)
        if key in self.resources:
            del self.resources[key]

    def scan_filesystem(self) -> Dict[str, Dict[str, Any]]:
        """
        Scans the root_dir (and children) for .yaml files to build resource state.
        Returns a dict of resource definitions found on disk.
        """
        local_resources = {}
        for root, dirs, files in os.walk(self.root_path):
            # skips
            if ".git" in dirs: dirs.remove(".git")
            
            for file in files:
                if file.endswith(".yaml") and file != "dremio.yaml":
                    full_path = os.path.join(root, file)
                    rel_dir = os.path.relpath(root, self.root_path)
                    if rel_dir == ".": rel_dir = ""

                    try:
                        with open(full_path, 'r') as f:
                            data = yaml.safe_load(f)
                        
                        if not data or "name" not in data or "type" not in data:
                            continue

                        # Determine full path key
                        # Logic: if 'path' explicit in YAML, use it.
                        # Else: derive from valid dremio.yaml scope + subdirs
                        resource_path = []
                        if "path" in data:
                            resource_path = data["path"]
                        else:
                            # We need context/scope to know the root prefix.
                            # For now, we store just the name, assuming sync logic resolves parent
                            # OR ideally: we require 'path' OR we inject it from outside.
                            # Let's rely on 'name' key grouping for now, but sync logic needs full path.
                            # Store relative path for now.
                            resource_path = [data["name"]]

                        path_key = ".".join(resource_path)
                        
                        # Handle SQL
                        if "sql" in data:
                            data["sql_content"] = data["sql"]
                        elif "sql_content" in data:
                             pass # Already there
                        
                        # Handle Wiki (description file)
                        desc = data.get("description", "")
                        if desc and desc.endswith(".md"):
                            md_path = os.path.join(root, desc)
                            if os.path.exists(md_path):
                                with open(md_path, 'r') as md_f:
                                    data["description"] = md_f.read()
                            else:
                                print(f"Warning: Wiki file {md_path} referenced but not found.")

                        # Store dependencies and tags implicitly (passed as is)
                        
                        local_resources[path_key] = data
                        
                    except Exception as e:
                        print(f"Error reading {full_path}: {e}")
        return local_resources
