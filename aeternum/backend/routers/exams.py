from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
import uuid
import httpx
import httpx
from services.supabase_client import supabase_client as supabase

router = APIRouter()

# Gemini API setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"

class Difficulty(BaseModel):
    easy: int
    medium: int
    hard: int

class GenerateExamRequest(BaseModel):
    topics: str
    numQuestions: int
    difficulty: Difficulty
    questionTypes: List[str]

@router.post("/generate")
async def generate_questions(request: GenerateExamRequest):
    prompt = f"""You are an expert exam setter. Generate exactly {request.numQuestions} questions based on these topics: {request.topics}. 
    Distribution: {request.difficulty.easy}% Easy, {request.difficulty.medium}% Medium, {request.difficulty.hard}% Hard. 
    Types allowed: {", ".join(request.questionTypes)}.
    
    Return ONLY a valid JSON array. Each object must have:
    - id (string, uuid)
    - type (string, one of: mcq, short, long)
    - question (string)
    - options (array of 4 strings, only for mcq, else null)
    - correctAnswer (string)
    - marks (integer)
    
    No markdown formatting, no code blocks, no explanation. Just the raw JSON array."""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_URL, json=payload, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            
            # Extract JSON string from Gemini response
            content = result['candidates'][0]['content']['parts'][0]['text']
            questions = json.loads(content)
            
            return questions
    except Exception as e:
        print(f"Gemini Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

class SaveExamRequest(BaseModel):
    title: str
    subject: str
    duration_mins: int
    start_time: str
    end_time: str
    admin_id: str
    questions: List[Dict]
    proctoring_config: Dict
    status: str = "scheduled"

@router.post("/")
async def save_exam(exam: SaveExamRequest):
    try:
        data = {
            "title": exam.title,
            "subject": exam.subject,
            "duration_mins": exam.duration_mins,
            "start_time": exam.start_time,
            "end_time": exam.end_time,
            "admin_id": exam.admin_id,
            "questions": exam.questions,
            "proctoring_config": exam.proctoring_config,
            "status": exam.status
        }
        result = supabase.table("exams").insert(data).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_exams(admin_id: str):
    try:
        result = supabase.table("exams").select("*").eq("admin_id", admin_id).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class InviteRequest(BaseModel):
    emails: List[str]

@router.post("/{exam_id}/invite")
async def invite_students(exam_id: str, request: InviteRequest):
    try:
        # Here we would normally send emails using SendGrid/AWS SES
        # For demonstration, we just return success
        return {"status": "success", "invited": len(request.emails), "exam_id": exam_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
