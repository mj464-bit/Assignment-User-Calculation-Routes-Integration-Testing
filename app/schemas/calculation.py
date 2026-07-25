from enum import Enum
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator


class CalculationType(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"


class CalculationBase(BaseModel):
    type: CalculationType = Field(description="addition | subtraction | multiplication | division")
    inputs: List[float] = Field(
        description="Numeric inputs for the calculation (at least 2)", min_length=2
    )

    @field_validator("inputs", mode="before")
    @classmethod
    def check_inputs_is_list(cls, v):
        if not isinstance(v, list):
            raise ValueError("inputs must be a list")
        return v

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationBase":
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        if self.type == CalculationType.DIVISION and any(x == 0 for x in self.inputs[1:]):
            raise ValueError("Cannot divide by zero")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"type": "addition", "inputs": [10.5, 3, 2]}},
    )


class CalculationCreate(CalculationBase):
    """Schema for creating a calculation. user_id is assigned server-side from the token."""

    pass


class CalculationUpdate(BaseModel):
    """Schema for editing a calculation's inputs. Result is recomputed server-side."""

    inputs: Optional[List[float]] = Field(default=None, min_length=2)

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationUpdate":
        if self.inputs is not None and len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        return self

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": {"inputs": [42, 7]}})


class CalculationResponse(CalculationBase):
    id: UUID
    user_id: UUID
    result: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    