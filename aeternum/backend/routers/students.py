from fastapi import APIRouter, HTTPException
from services.supabase_client import supabase_client as supabase

router = APIRouter()

@router.get("/exams")
async def get_student_exams(student_id: str):
    """Get all exams assigned to a student."""
    try:
        # In a real app we would have an exam_enrollments table
        # For demo purposes, returning all active exams
        result = supabase.table("exams").select("*").eq("status", "active").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
