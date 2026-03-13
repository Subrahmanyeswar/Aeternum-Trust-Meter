from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from services.yolo_detector import detector
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Supabase setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Thread pool for non-blocking YOLO interference
executor = ThreadPoolExecutor(max_workers=3)

@router.websocket("/ws/integrity/{session_id}")
async def integrity_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    try:
        # 1. Fetch session and proctoring config
        session_res = supabase.table("sessions").select("*, exams(proctoring_config)").eq("id", session_id).single().execute()
        if not session_res.data:
            await websocket.close(code=1008, reason="Session not found")
            return
            
        session = session_res.data
        config = session["exams"]["proctoring_config"]
        current_score = session.get("integrity_score", 100)
        
        loop = asyncio.get_event_loop()
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            face_count = message.get("faceCount", 1)
            gaze_away = message.get("gazeAway", False)
            audio_level = message.get("audioLevel", 0)
            frame_base64 = message.get("frameBase64")
            
            total_deduction = 0
            new_events = []
            
            # (A) Rule-based deductions from MediaPipe/Audio
            if face_count == 0:
                deduction = config.get("face_missing", 10)
                total_deduction += deduction
                new_events.append({"event_type": "Face Missing", "severity": "warning", "deduction": deduction})
            elif face_count > 1:
                deduction = config.get("multiple_faces", 20)
                total_deduction += deduction
                new_events.append({"event_type": "Multiple Faces detected", "severity": "danger", "deduction": deduction})
                
            if gaze_away:
                deduction = config.get("gaze_diversion", 5)
                total_deduction += deduction
                new_events.append({"event_type": "Gaze Diversion", "severity": "low", "deduction": deduction})
                
            if audio_level > 0.4:
                deduction = config.get("audio_spike", 10)
                total_deduction += deduction
                new_events.append({"event_type": "High Audio Level", "severity": "warning", "deduction": deduction})

            # (B) AI Object Detection (YOLO)
            detections = {}
            if frame_base64:
                # Run YOLO in thread pool as it's CPU/GPU intensive and blocking
                detections = await loop.run_in_executor(executor, detector.detect_frame, frame_base64)
                
                if detections.get("phone_detected"):
                    deduction = config.get("phone_detected", 25)
                    total_deduction += deduction
                    new_events.append({"event_type": "Phone Detected", "severity": "danger", "deduction": deduction})
                    
                if detections.get("book_detected"):
                    # Not explicitly in user deduction list but implied / good for robust detector
                    deduction = 15 
                    total_deduction += deduction
                    new_events.append({"event_type": "Unallowed Resource (Book) detected", "severity": "warning", "deduction": deduction})

            # Update score
            if total_deduction > 0:
                current_score = max(0, current_score - total_deduction)
                
                # Log events to Supabase
                for event in new_events:
                    supabase.table("events").insert({
                        "session_id": session_id,
                        "event_type": event["event_type"],
                        "severity": event["severity"],
                        "alert": f"System detected {event['event_type']}. -{event['deduction']} pts",
                        "metadata": {"detections": detections, "faceCount": face_count, "audioLevel": audio_level}
                    }).execute()
                
                # Update session score
                supabase.table("sessions").update({"integrity_score": current_score}).eq("id", session_id).execute()

            # Send back status
            await websocket.send_text(json.dumps({
                "score": current_score,
                "events": new_events,
                "detections": detections,
                "status": "active" if current_score > config.get("min_integrity", 70) else "flagged"
            }))

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close()
