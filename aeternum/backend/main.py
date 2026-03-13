from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Aeternum API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Aeternum backend running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Import routers safely with try/except so one broken router doesn't kill everything
try:
    from routers import exams
    app.include_router(exams.router, prefix="/api/exams", tags=["exams"])
except Exception as e:
    print(f"Warning: exams router failed to load: {e}")

try:
    from routers import sessions
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
except Exception as e:
    print(f"Warning: sessions router failed to load: {e}")

try:
    from routers import reports
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
except Exception as e:
    print(f"Warning: reports router failed to load: {e}")

try:
    from routers import ws
    app.include_router(ws.router, tags=["websockets"])
except Exception as e:
    print(f"Warning: ws router failed to load: {e}")

try:
    from routers import phone
    app.include_router(phone.router, prefix="/api/phone", tags=["phone"])
except Exception as e:
    print(f"Warning: phone router failed to load: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
