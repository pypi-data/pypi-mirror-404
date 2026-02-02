"""Auto-generated tool: IsFloatTool"""

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
