"""Auto-generated tool: IsStringTool"""

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


__version__ = "0.1.0"
TOOL_CODE = """import os
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
