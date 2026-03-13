import cv2
import numpy as np
import base64
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YOLODetector")

class YOLODetector:
    def __init__(self):
        self.model = None
        self.using_tensorrt = False
        self.device = "cpu"
        self.classes = [67, 73, 76]  # cell phone, book, scissors
        self.class_names = {67: "cell phone", 73: "book", 76: "scissors"}
        
        try:
            import torch
            from ultralytics import YOLO
            
            # Detect device
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("CUDA detected, using GPU acceleration.")
            else:
                self.device = "cpu"
                logger.info("CUDA not available, using CPU.")

            self.model_path_engine = os.path.join("models", "yolov8n.engine")
            self.model_path_pt = "yolov8n.pt"  # Fallback
            
            # Check if TensorRT engine exists
            if os.path.exists(self.model_path_engine) and self.device == "cuda":
                logger.info(f"Loading TensorRT engine: {self.model_path_engine}")
                self.model = YOLO(self.model_path_engine, task="detect")
                self.using_tensorrt = True
            else:
                if not os.path.exists(self.model_path_engine) and self.device == "cuda":
                    logger.info("TensorRT engine not found, using PyTorch on CUDA.")
                
                logger.info(f"Loading PyTorch model: {self.model_path_pt}")
                self.model = YOLO(self.model_path_pt)
                self.using_tensorrt = False
                
            # Warmup
            logger.info("Warming up model...")
            dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            # Use detected device and only half precision if on CUDA
            self.model(dummy_frame, device=self.device, half=(self.device == "cuda"), verbose=False)
            logger.info("Model detection engine initialized.")
            
        except Exception as e:
            logger.error(f"Failed to initialize YOLO detector: {e}")
            self.model = None

    def detect_frame(self, base64_image_string: str):
        if self.model is None:
            return {"error": "AI Model not initialized"}
            
        start_time = time.time()
        
        try:
            # Decode base64
            img_data = base64.b64decode(base64_image_string.split(",")[-1])
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return {"error": "Invalid image data"}

            # Run inference
            results = self.model(frame, device=self.device, half=(self.device == "cuda"), classes=self.classes, verbose=False)
            
            detections = []
            phone_detected = False
            book_detected = False
            
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = self.class_names.get(cls_id, "unknown")
                    detections.append(label)
                    
                    if cls_id == 67:
                        phone_detected = True
                    elif cls_id == 73:
                        book_detected = True

            inference_time_ms = (time.time() - start_time) * 1000
            
            return {
                "phone_detected": phone_detected,
                "book_detected": book_detected,
                "object_labels": detections,
                "inference_time_ms": round(inference_time_ms, 2),
                "using_tensorrt": self.using_tensorrt,
                "device": self.device
            }
            
        except Exception as e:
            logger.error(f"Detection error: {str(e)}")
            return {"error": str(e)}

# Singleton instance - created on import, but now safe
try:
    detector = YOLODetector()
except Exception as e:
    logger.error(f"Critical error creating detector instance: {e}")
    detector = None
