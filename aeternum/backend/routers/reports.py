from services.supabase_client import supabase_client as supabase
import anthropic

# Initialize Anthropic safely
client = None
try:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and "placeholder" not in api_key:
        client = anthropic.Anthropic(api_key=api_key)
except Exception as e:
    print(f"Warning: Anthropic client failed to initialize: {e}")

@router.post("/generate/{session_id}")
async def generate_report(session_id: str):
    try:
        # 1. Fetch Session and Events
        session_res = supabase.table("sessions").select("*, profiles(full_name), exams(title)").eq("id", session_id).single().execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = session_res.data
        events_res = supabase.table("violation_events").select("*").eq("session_id", session_id).order("created_at").execute()
        events = events_res.data

        # 2. Summarize Events
        events_summary = ""
        if not events:
            events_summary = "No violations detected."
        else:
            event_counts = {}
            for e in events:
                etype = e.get("event_type", "unknown")
                event_counts[etype] = event_counts.get(etype, 0) + 1
            events_summary = ", ".join([f"{count} {etype}" for etype, count in event_counts.items()])

        # 3. Build Prompt for Claude
        prompt = f"""You are an academic integrity analyst. Analyze this exam session and write a clear, professional, 3-paragraph report. Be factual, not accusatory.

Session data:
Student: {session['profiles']['full_name']}
Duration: {session.get('duration_minutes', 'Unknown')} mins
Final Integrity Score: {session['integrity_score']}/100
Events detected: {events_summary}

Write:
Paragraph 1: Overall assessment.
Paragraph 2: Specific observations.
Paragraph 3: Recommendation (No Action Required / Flag for Review / Recommend Invalidation).

Return ONLY the report text, no JSON. Do not include any preamble or signature."""

        # 4. Call Claude
        if not client:
            return {"report": "AI Reporting service currently unavailable. Using degraded mode summary: " + events_summary}

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        report_text = message.content[0].text

        # 5. Save Report to Session
        supabase.table("sessions").update({"ai_report": report_text}).eq("id", session_id).execute()

        return {"report": report_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
