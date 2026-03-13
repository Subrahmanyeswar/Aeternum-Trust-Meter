import os
import shutil
from ultralytics import YOLO

def main():
    print("Loading YOLOv8n model...")
    model = YOLO('yolov8n.pt')
    
    print("Exporting to TensorRT...")
    # This might take a while and requires a GPU
    model.export(format='engine', device=0, half=True)
    
    # The engine file is typically saved next to the original weights
    engine_file = 'yolov8n.engine'
    target_path = os.path.join('models', 'yolov8n.engine')
    
    if os.path.exists(engine_file):
        os.makedirs('models', exist_ok=True)
        shutil.move(engine_file, target_path)
        
    print("TensorRT engine exported successfully")

if __name__ == '__main__':
    main()
