from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""

    message: str = Field(..., description="Assistant's response")
    limit_reached: bool = Field(
        ..., description="Whether user has reached the limit for the session"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Diabetes is a chronic condition...",
                "limit_reached": False,
            }
        }
