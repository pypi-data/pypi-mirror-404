"""Auto-generated tool: CalculateCircleAreaTool"""

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
