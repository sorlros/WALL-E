import cv2
import time

rtmp_url = "rtmp://1.238.76.151:1935/live/drone"

print(f"Attempting to connect to {rtmp_url}...")
cap = cv2.VideoCapture(rtmp_url)

if not cap.isOpened():
    print("Error: Could not open video stream.")
else:
    print("Success: Video stream opened.")
    ret, frame = cap.read()
    if ret:
        print(f"Frame received. Shape: {frame.shape}")
    else:
        print("Error: Could not read frame.")
    cap.release()
