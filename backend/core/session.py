import uuid
import json
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from redis.asyncio import Redis

class SessionManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 1800  # 30 minutes
        self.sgt = ZoneInfo("Asia/Singapore")
    
    async def get_or_create_session(self, session_id: Optional[str] = None) -> dict:
        if session_id and session_id.strip():
            session = await self.get_session(session_id)
            if session:
                await self.extend_session(session_id, session)
                return session
        
        new_session_id = self._generate_session_id()
        session_data = {
            "session_id": new_session_id,
            "created_at": datetime.now(self.sgt).isoformat(),
            "last_active": datetime.now(self.sgt).isoformat(),
            "conversation_history": [],
            "analysis": [],
            "upload_history": [],
            "has_active_analysis": False,
            "message_count": 0, 
            "upload_count": 0
        }
        await self.save_session(new_session_id, session_data)
        return session_data
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        data = await self.redis.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    async def save_session(self, session_id: str, data: dict):
        await self.redis.setex(
            f"session:{session_id}",
            self.ttl,
            json.dumps(data)
        )
    
    async def extend_session(self, session_id: str, session: dict):
        session["last_active"] = datetime.now(self.sgt).isoformat()
        await self.save_session(session_id, session)
        await self.redis.expire(f"session:{session_id}", self.ttl)
    
    def _generate_session_id(self) -> str:
        return f"sess_{uuid.uuid4().hex}"
