import argparse
import cv2
from ultralytics import YOLO
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Basic YOLO Detection Pipeline")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--store-id", required=True, help="Store ID")
    parser.add_argument("--camera-id", required=True, help="Camera ID")
    args = parser.parse_args()

    # Model
    print("Loading YOLOv8n model...")
    # Downloading or loading the model
    model = YOLO("yolov8n.pt")

    if not os.path.exists(args.video):
        print(f"Error: Video file {args.video} not found")
        sys.exit(1)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Error: Could not open video {args.video}")
        sys.exit(1)

    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_idx += 1
        
        # Process every 5th frame
        if frame_idx % 5 != 0:
            continue
            
        # verbose=False to keep the output clean as required
        results = model(frame, verbose=False)
        
        person_count = 0
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id == 0:  # class 0 is 'person' in COCO dataset
                    person_count += 1
                    
        print(f"frame={frame_idx} people={person_count}")
        
    cap.release()
    print("Processing complete.")

if __name__ == "__main__":
    main()
