from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    message: str = Field(..., description="Assistant's response")
    has_active_analysis: bool = Field(..., description="Whether user has uploaded and analyzed a document")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Diabetes is a chronic condition...",
                "has_active_analysis": False
            }
        }
