"""Auto-generated tool: CalculateSquareRootTool"""

import math
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
            return f"An unexpected error occurred: {str(e)}"

__version__ = "0.1.0"
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
