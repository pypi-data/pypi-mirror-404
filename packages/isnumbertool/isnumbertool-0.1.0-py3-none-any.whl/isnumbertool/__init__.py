"""Auto-generated tool: IsNumberTool"""

import os
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
            return "False"

__version__ = "0.1.0"
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
