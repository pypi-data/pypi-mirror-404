"""Auto-install script for IsFloatTool"""
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

class IsFloatArgs(BaseModel):
    input_string: str = Field(..., description="The string to check if it represents a float number.")

class IsFloatTool(Tool):
    name = "is_float"
    description = "Checks if the input string can be successfully converted into a float number."
    args_schema = IsFloatArgs

    def run(self, input_string: str) -> str:
        try:
            float(input_string)
            return "True"
        except ValueError:
            return "False"
        except Exception as e:
            return f"Error checking float: {str(e)}"
"""

TOOL_METADATA = {
    "class_name": "IsFloatTool",
    "file_name": "isfloattool.py",
    "description": "tool to check if input is float number",
    "tags": ["validation", "type_check", "float", "number"],
    "input_types": ["string"],
    "output_types": ["string"],
    "domain": "text",
    "pypi_package": "isfloattool"
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
    print(f"[isfloattool] Installed tool to: {target_file}")
    
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
        print(f"[isfloattool] Added to registry: {class_name}")
    else:
        print(f"[isfloattool] Already in registry: {class_name}")
    
    return target_file

if __name__ == "__main__":
    install()
