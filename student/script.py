import cv2
import torch
from ultralytics import YOLO

# Load the YOLO model (e.g., YOLOv8)
model = YOLO('yolov8n.pt')  # Load a pre-trained model

def detect_objects(frame):
    # Run YOLO model on the frame
    results = model(frame)
    
    # Process results
    detections = results.pandas().xyxy[0]  # Get the detection results as pandas dataframe
    
    suspicious_activities = []
    for index, row in detections.iterrows():
        if row['name'] == 'person':  # Detecting a person (could be used for face detection)
            # Implement logic to check for suspicious activities
            suspicious_activities.append(row)

    return suspicious_activities

def start_proctoring():
    cap = cv2.VideoCapture(0)  # Capture video from the webcam
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect objects in the frame
        suspicious_activities = detect_objects(frame)

        # Logic to handle detected suspicious activities
        if len(suspicious_activities) > 1:
            print("Multiple people detected! Possible cheating detected.")
            # Trigger an event to record suspicious activity

        # Display the frame
        cv2.imshow('Proctoring', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_proctoring()
