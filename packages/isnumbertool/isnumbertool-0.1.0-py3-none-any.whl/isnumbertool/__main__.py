"""Auto-install script for IsNumberTool"""
import os
import sys
import json

TOOL_CODE = """import os
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from pydantic import BaseModel, Field
import sys

class Tool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass

class IsNumberArgs(BaseModel):
    text: str = Field(..., description="The string to check if it's a number.")

class IsNumberTool(Tool):
    name = "is_number"
    description = "Checks if a given string can be interpreted as a number (integer or float)."
    args_schema = IsNumberArgs

    def run(self, text: str) -> str:
        try:
            float(text)
            return "True"
        except ValueError:
            return "False""""

TOOL_METADATA = {
    "class_name": "IsNumberTool",
    "file_name": "isnumbertool.py",
    "description": "a tool to check if input is num or not",
    "tags": ["type_check", "validation", "string", "number"],
    "input_types": ["string"],
    "output_types": ["string"],
    "domain": "text",
    "pypi_package": "isnumbertool"
}

def install():
    """Install this tool to workspace/tools/ folder and update registry.json."""
    # Find workspace/tools directory
    cwd = os.getcwd()
    tools_dir = os.path.join(cwd, "workspace", "tools")
    
    if not os.path.exists(tools_dir):
        # Try to find it relative to agentic_system
        for parent in [cwd] + list(os.path.abspath(cwd).split(os.sep)):
            candidate = os.path.join(parent, "workspace", "tools")
            if os.path.exists(candidate):
                tools_dir = candidate
                break
        else:
            os.makedirs(tools_dir, exist_ok=True)
    
    # Write the tool file
    target_file = os.path.join(tools_dir, TOOL_METADATA["file_name"])
    with open(target_file, "w") as f:
        f.write(TOOL_CODE)
    print(f"[isnumbertool] Installed tool to: {target_file}")
    
    # Update registry.json
    registry_path = os.path.join(tools_dir, "registry.json")
    
    # Load existing registry or create new
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r") as f:
                registry = json.load(f)
        except:
            registry = {}
    else:
        registry = {}
    
    # Check if tool already exists in registry
    class_name = TOOL_METADATA["class_name"]
    if class_name not in registry:
        registry[class_name] = {
            "file": TOOL_METADATA["file_name"],
            "description": TOOL_METADATA["description"],
            "tags": TOOL_METADATA["tags"],
            "input_types": TOOL_METADATA["input_types"],
            "output_types": TOOL_METADATA["output_types"],
            "domain": TOOL_METADATA["domain"],
            "pypi_package": TOOL_METADATA["pypi_package"]
        }
        
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
        print(f"[isnumbertool] Added to registry: {class_name}")
    else:
        print(f"[isnumbertool] Already in registry: {class_name}")
    
    return target_file

if __name__ == "__main__":
    install()
