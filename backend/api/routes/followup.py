from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.followup.followup import followup_agent

router = APIRouter()

class FollowupRequest(BaseModel):
    session_id: str
    summary: str
    chat_history: list
    user_question: str

class FollowupResponse(BaseModel):
    followup_answer: str
    chat_history: list

@router.post("/followup", response_model=FollowupResponse)
def followup_endpoint(request: FollowupRequest):
    try:
        result = followup_agent(request.dict())
        return FollowupResponse(
            followup_answer=result["followup_answer"],
            chat_history=result["chat_history"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
