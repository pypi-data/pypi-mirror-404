"""Base model class for all data models."""

from typing import Any, Dict, Union

from pydantic import BaseModel as PydanticBaseModel, ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model class with common configuration."""
    
    model_config = ConfigDict(
        # Allow extra fields to be ignored
        extra="ignore",
        # Use enum values instead of names
        use_enum_values=True,
        # Validate assignment
        validate_assignment=True,
        # Allow population by field name
        populate_by_name=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model from dictionary."""
        return cls(**data)


class BaseResponse(BaseModel):
    """Base response model for all CUFinder API responses."""
    query: Union[str, dict]
    credit_count: int


class BaseErrorResponse(BaseModel):
    """Base error response model."""
    query: str
    credit_count: int


class ApiResponse(BaseModel):
    """API response wrapper."""
    status: int
    data: Any
    message: str = None
    error: str = None
