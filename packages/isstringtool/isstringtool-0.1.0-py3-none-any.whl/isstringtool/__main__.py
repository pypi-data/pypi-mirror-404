"""Auto-install script for IsStringTool"""
import os
import sys

TOOL_CODE = """
import os
from abc import ABC, abstractmethod
from typing import Any, Type
from pydantic import BaseModel, Field

class Tool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass

class IsStringArgs(BaseModel):
    input_value: Any = Field(..., description="The value to check if it's a string.")

class IsStringTool(Tool):
    name = "is_string"
    description = "Checks if the provided input value is a string."
    args_schema = IsStringArgs

    def run(self, input_value: Any) -> str:
        if isinstance(input_value, str):
            return "The input is a string."
        else:
            return f"The input is not a string. Its type is {type(input_value).__name__}."

"""

def install():
    """Install this tool to workspace/tools/ folder."""
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
    
    target_file = os.path.join(tools_dir, "isstringtool.py")
    
    with open(target_file, "w") as f:
        f.write(TOOL_CODE)
    
    print(f"[isstringtool] Installed to: {target_file}")
    return target_file

if __name__ == "__main__":
    install()
