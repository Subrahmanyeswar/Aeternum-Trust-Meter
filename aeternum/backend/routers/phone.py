from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict
import uuid
import asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

# In-memory storage for active heartbeats (session_id -> last_seen)
active_heartbeats: Dict[str, datetime] = {}

@router.post("/api/sessions/{session_id}/phone-token")
async def create_phone_token(session_id: str):
    token = str(uuid.uuid4())
    expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
    
    try:
        data = supabase.table("phone_tokens").insert({
            "session_id": session_id,
            "token": token,
            "expires_at": expires_at
        }).execute()
        
        return {"token": token, "expires_at": expires_at}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/phone/{token}/validate")
async def validate_phone_token(token: str):
    try:
        res = supabase.table("phone_tokens").select("*").eq("token", token).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Token not found")
        
        token_data = res.data[0]
        expires_at = datetime.fromisoformat(token_data["expires_at"].replace("Z", "+00:00"))
        
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            raise HTTPException(status_code=410, detail="Token expired")
            
        return {"valid": True, "session_id": token_data["session_id"]}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/phone/{token}")
async def phone_websocket(websocket: WebSocket, token: str):
    await websocket.accept()
    
    # Validate token and get session
    res = supabase.table("phone_tokens").select("*").eq("token", token).execute()
    if not res.data:
        await websocket.close(code=4004)
        return
    
    token_data = res.data[0]
    session_id = token_data["session_id"]
    
    # Update status
    supabase.table("phone_tokens").update({"connected": True}).eq("token", token).execute()
    supabase.table("sessions").update({"phone_verified": True}).eq("id", session_id).execute()
    
    active_heartbeats[session_id] = datetime.utcnow()
    
    # Monitor heartbeat in background
    async def check_heartbeat():
        while True:
            await asyncio.sleep(5)
            last_seen = active_heartbeats.get(session_id)
            if not last_seen or (datetime.utcnow() - last_seen).total_seconds() > 10:
                # Disconnected!
                await handle_disconnection(session_id)
                break

    heartbeat_task = asyncio.create_task(check_heartbeat())
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "heartbeat":
                active_heartbeats[session_id] = datetime.utcnow()
    except WebSocketDisconnect:
        await handle_disconnection(session_id)
    finally:
        heartbeat_task.cancel()
        active_heartbeats.pop(session_id, None)

async def handle_disconnection(session_id: str):
    # Log event
    supabase.table("events").insert({
        "session_id": session_id,
        "event_type": "phone_disconnected",
        "severity": "danger",
        "metadata": {"alert": "Secondary device connection lost. Integrity -30%"}
    }).execute()
    
    # Apply deduction
    session_res = supabase.table("sessions").select("integrity_score").eq("id", session_id).execute()
    if session_res.data:
        new_score = max(0, session_res.data[0]["integrity_score"] - 30)
        supabase.table("sessions").update({
            "integrity_score": new_score,
            "phone_verified": False
        }).eq("id", session_id).execute()
