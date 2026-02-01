
from typing import List, Dict, Set, Any
from collections import defaultdict, deque

class DependencyGraph:
    """Manages dependency graph and topological sorting."""

    def __init__(self, items: List[Dict[str, Any]]):
        """Initialize with list of items (dicts).
        
        Each item usually has:
        - name: str (unique identifier if possible, or we assume name matches dependency ref)
        - dependencies: List[str]
        """
        self.items = items
        self.item_map = {item.get("name"): item for item in items if item.get("name")}
        
    def get_execution_order(self) -> List[Dict[str, Any]]:
        """Get topological sort of items.
        
        Returns:
            List of items in execution order.
            
        Raises:
            ValueError: If cycle detected.
        """
        # Build graph
        adj = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize in_degree for all known items
        for name in self.item_map:
            in_degree[name] = 0

        # Create edges
        for item in self.items:
            u = item.get("name")
            if not u: continue
            
            deps = item.get("dependencies", [])
            if not isinstance(deps, list): deps = []
            
            for v in deps:
                # If dependency exists in our local set, add edge v -> u (v must come before u)
                if v in self.item_map:
                    adj[v].append(u)
                    in_degree[u] += 1
                # If dependency is external (not in local set), we ignore it and assume it exists remotely
        
        # Kahn's Algorithm
        queue = deque([node for node in self.item_map if in_degree[node] == 0])
        result = []
        
        while queue:
            u = queue.popleft()
            result.append(self.item_map[u])
            
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
        # Cycle Check
        if len(result) != len(self.item_map):
            # Find missing nodes
            missing = set(self.item_map.keys()) - set(item["name"] for item in result)
            raise ValueError(f"Circular dependency detected involving: {missing}")
            
        return result
