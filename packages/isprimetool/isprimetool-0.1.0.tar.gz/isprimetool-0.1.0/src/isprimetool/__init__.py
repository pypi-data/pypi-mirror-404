"""Auto-generated tool: IsPrimeTool"""

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

class IsPrimeArgs(BaseModel):
    number: int = Field(..., description="The integer number to check for primality.")

class IsPrimeTool(Tool):
    name = "is_prime"
    description = "Checks if a given integer number is a prime number."
    args_schema = IsPrimeArgs

    def run(self, number: int) -> str:
        if not isinstance(number, int):
            return f"Error: Input must be an integer, received {type(number).__name__}."

        if number <= 1:
            return f"{number} is not a prime number."
        if number == 2:
            return f"{number} is a prime number."
        if number % 2 == 0:
            return f"{number} is not a prime number (it is even and greater than 2)."

        # Check for factors from 3 up to sqrt(number) with a step of 2
        limit = int(math.sqrt(number)) + 1
        for i in range(3, limit, 2):
            if number % i == 0:
                return f"{number} is not a prime number (divisible by {i})."

        return f"{number} is a prime number."

__version__ = "0.1.0"
