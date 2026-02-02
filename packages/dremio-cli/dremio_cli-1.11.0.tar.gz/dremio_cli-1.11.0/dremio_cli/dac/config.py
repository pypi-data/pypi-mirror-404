
import os
import yaml
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Scope:
    path: str
    type: str  # SPACE, ICEBERGCATALOG, SOURCE

@dataclass
class DremioConfig:
    version: str
    scope: Scope
    ignore: List[str]

    @classmethod
    def load(cls, path: str = "dremio.yaml") -> 'DremioConfig':
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file {path} not found.")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            
        scope_data = data.get("scope", {})
        if not scope_data.get("path") or not scope_data.get("type"):
            raise ValueError("dremio.yaml must define scope.path and scope.type")

        # Validate type
        valid_types = ["SPACE", "ICEBERGCATALOG", "SOURCE"]
        if scope_data["type"] not in valid_types:
             raise ValueError(f"Invalid scope.type: {scope_data['type']}. Must be one of {valid_types}")

        return cls(
            version=data.get("version", "1.0"),
            scope=Scope(
                path=scope_data["path"],
                type=scope_data["type"]
            ),
            ignore=data.get("ignore", [])
        )
