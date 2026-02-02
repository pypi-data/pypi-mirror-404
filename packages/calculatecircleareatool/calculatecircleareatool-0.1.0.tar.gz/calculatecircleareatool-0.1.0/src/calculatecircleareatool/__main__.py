"""Auto-install script for CalculateCircleAreaTool"""
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

class CalculateCircleAreaArgs(BaseModel):
    radius: float = Field(..., description="The radius of the circle")

class CalculateCircleAreaTool(Tool):
    name = "calculate_circle_area"
    description = "Calculate the area of a circle given its radius."
    args_schema = CalculateCircleAreaArgs

    def run(self, radius: float) -> str:
        if radius < 0:
            return "Error: Radius cannot be negative."
        area = math.pi * (radius ** 2)
        return f"The area of a circle with radius {radius} is {area:.4f}"
"""

TOOL_METADATA = {
    "class_name": "CalculateCircleAreaTool",
    "file_name": "calculatecircleareatool.py",
    "description": "A tool to calculate area of a circle",
    "tags": ["geometry", "math", "circle", "area", "calculation"],
    "input_types": ["number"],
    "output_types": ["number"],
    "domain": "math",
    "pypi_package": "calculatecircleareatool"
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
    print(f"[calculatecircleareatool] Installed tool to: {target_file}")
    
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
        print(f"[calculatecircleareatool] Added to registry: {class_name}")
    else:
        print(f"[calculatecircleareatool] Already in registry: {class_name}")
    
    return target_file

if __name__ == "__main__":
    install()
