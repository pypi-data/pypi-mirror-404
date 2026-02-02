"""Auto-generated tool: CheckEvenOddTool"""

import os
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from pydantic import BaseModel, Field

class Tool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass

class CheckEvenOddArgs(BaseModel):
    number: int = Field(..., description="The integer to check if it is even or odd.")

class CheckEvenOddTool(Tool):
    name = "check_even_odd"
    description = "Checks if an integer input is even or odd."
    args_schema = CheckEvenOddArgs

    def run(self, number: int) -> str:
        if not isinstance(number, int):
            return "Error: Input must be an integer."
        if number % 2 == 0:
            return f"The number {number} is Even."
        else:
            return f"The number {number} is Odd."

__version__ = "0.1.0"
