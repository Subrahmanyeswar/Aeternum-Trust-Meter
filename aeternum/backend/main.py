from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import exams, ws, phone, reports
from services.yolo_detector import detector
import torch

app = FastAPI(title="Aeternum API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exams.router)
app.include_router(ws.router)
app.include_router(reports.router)

@app.get("/api/detector/status")
def get_detector_status():
    return {
        "status": "online",
        "using_tensorrt": detector.using_tensorrt,
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None",
        "current_device": str(next(detector.model.model.parameters()).device)
    }

@app.get("/")
def read_root():
    return {"message": "Aeternum API is running"}
