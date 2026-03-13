import os
import uuid
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(URL, KEY)

def seed():
    print("🚀 Seeding Aeternum demo data...")
    
    # 1. Create a demo exam
    exam_id = str(uuid.uuid4())
    exam_data = {
        "id": exam_id,
        "title": "Introduction to AI Ethics",
        "description": "Final examination covering AI safety and ethical alignment.",
        "duration": 60,
        "total_questions": 20,
        "status": "published"
    }
    supabase.table("exams").upsert(exam_data).execute()
    print(f"✅ Created Exam: {exam_data['title']}")

    # 2. Create a demo student session
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "exam_id": exam_id,
        "student_name": "Demo Student",
        "integrity_score": 100,
        "status": "active",
        "start_time": datetime.utcnow().isoformat()
    }
    supabase.table("sessions").upsert(session_data).execute()
    print(f"✅ Created Session for {session_data['student_name']}")

    # 3. Add some sample events
    events = [
        {
            "session_id": session_id,
            "event_type": "face_loss",
            "severity": "warning",
            "metadata": {"alert": "Subject moved out of frame"},
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        },
        {
            "session_id": session_id,
            "event_type": "gaze_deviated",
            "severity": "info",
            "metadata": {"alert": "Frequent side gazes detected"},
            "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat()
        }
    ]
    supabase.table("events").insert(events).execute()
    print("✅ Seeded sample integrity events")

    print("\n🎉 Demo data ready. You can now visit the Live Monitor or Reports page.")

if __name__ == "__main__":
    seed()
