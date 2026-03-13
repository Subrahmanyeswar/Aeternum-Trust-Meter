from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from services.supabase_client import supabase_client as supabase

router = APIRouter()

class SessionSubmitRequest(BaseModel):
    answers: Dict[str, Any]
    integrity_score: int
    time_taken_mins: int
    violations: List[Dict[str, Any]]

@router.post("/{session_id}/submit")
async def submit_session(session_id: str, request: SessionSubmitRequest):
    try:
        data = {
            "status": "completed",
            "integrity_score": request.integrity_score,
            "violations": request.violations,
            "answers": request.answers,
            "time_taken_mins": request.time_taken_mins
        }
        result = supabase.table("sessions").update(data).eq("id", session_id).execute()
        return {"status": "success", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
