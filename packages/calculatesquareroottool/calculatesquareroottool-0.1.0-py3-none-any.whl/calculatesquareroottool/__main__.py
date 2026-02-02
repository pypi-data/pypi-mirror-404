"""Auto-install script for CalculateSquareRootTool"""
import os
import sys
import json

TOOL_CODE = """import math
from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel, Field

class Tool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass

class CalculateSquareRootArgs(BaseModel):
    number: float = Field(..., description="The number for which to calculate the square root.")

class CalculateSquareRootTool(Tool):
    name = "calculate_square_root"
    description = "Calculate the square root of a given number. Returns an error for negative numbers."
    args_schema = CalculateSquareRootArgs

    def run(self, number: float) -> str:
        if number < 0:
            return f"Error: Cannot calculate the square root of a negative number ({number})."
        try:
            result = math.sqrt(number)
            return f"The square root of {number} is {result}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}""""

TOOL_METADATA = {
    "class_name": "CalculateSquareRootTool",
    "file_name": "calculatesquareroottool.py",
    "description": "A tool to calculate the square root of a number",
    "tags": ["math", "calculation", "square root", "number"],
    "input_types": ["number"],
    "output_types": ["string"],
    "domain": "math",
    "pypi_package": "calculatesquareroottool"
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
    print(f"[calculatesquareroottool] Installed tool to: {target_file}")
    
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
        print(f"[calculatesquareroottool] Added to registry: {class_name}")
    else:
        print(f"[calculatesquareroottool] Already in registry: {class_name}")
    
    return target_file

if __name__ == "__main__":
    install()
