# smile_detector.py

import cv2
import os
import webbrowser
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

def start_server():
    server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()

# Create welcome.html
welcome_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Welcome!</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(45deg, #85FFBD 0%, #FFFB7D 100%);
        }
        .container {
            text-align: center;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 1rem;
        }
        .message {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .timestamp {
            font-size: 0.9rem;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome!</h1>
        <div class="message">Thank you for sharing your beautiful smile!</div>
        <div class="timestamp">Detected at: <span id="time"></span></div>
    </div>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleTimeString();
    </script>
</body>
</html>
"""

# Write the HTML file
with open('welcome.html', 'w') as f:
    f.write(welcome_html)

# Start the local server in a separate thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Get the path to the haar cascade files
cv2_base_dir = os.path.dirname(os.path.abspath(cv2.__file__))
haar_model_path = os.path.join(cv2_base_dir, 'data')

# Load the pre-trained classifiers
face_cascade = cv2.CascadeClassifier(os.path.join(haar_model_path, 'haarcascade_frontalface_default.xml'))
smile_cascade = cv2.CascadeClassifier(os.path.join(haar_model_path, 'haarcascade_smile.xml'))

# Start the video capture
cap = cv2.VideoCapture(0)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# Set window parameters
cv2.namedWindow('Smile Detector', cv2.WINDOW_NORMAL)

# Variables for timing and state management
webpage_opened = False
last_smile_time = 0
SMILE_COOLDOWN = 10  # Increased cooldown to 10 seconds
smile_counter = 0
REQUIRED_SMILE_FRAMES = 15  # Number of consecutive frames with smile needed
processing_frame = 0
PROCESS_EVERY_N_FRAMES = 3  # Only process every 3rd frame

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Can't receive frame")
        break
    
    # Only process every Nth frame
    processing_frame += 1
    if processing_frame % PROCESS_EVERY_N_FRAMES != 0:
        cv2.imshow('Smile Detector', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 
                                        scaleFactor=1.1,  # More conservative scale factor
                                        minNeighbors=5)   # Increased for more stable detection
    
    current_time = time.time()
    smile_detected_in_current_frame = False
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]
        
        smiles = smile_cascade.detectMultiScale(roi_gray, 
                                              scaleFactor=1.7,    # More conservative scale factor
                                              minNeighbors=45)    # Increased for more stable detection
        
        if len(smiles) > 0:
            smile_detected_in_current_frame = True
            for (sx, sy, sw, sh) in smiles:
                cv2.rectangle(roi_color, (sx, sy), (sx + sw, sy + sh), (0, 255, 0), 2)
                
                # Display smile counter progress
                progress = f'Smile Progress: {smile_counter}/{REQUIRED_SMILE_FRAMES}'
                cv2.putText(frame, progress, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    
    # Update smile counter
    if smile_detected_in_current_frame:
        smile_counter += 1
    else:
        smile_counter = max(0, smile_counter - 1)  # Decrease counter if no smile, but don't go below 0
    
    # Check if we've reached the required number of smile frames and cooldown has passed
    if smile_counter >= REQUIRED_SMILE_FRAMES and current_time - last_smile_time > SMILE_COOLDOWN:
        webbrowser.open('http://localhost:8000/welcome.html')
        last_smile_time = current_time
        smile_counter = 0  # Reset counter
        
        # Display "Welcome!" text for a moment
        cv2.putText(frame, 'Welcome!', (frame.shape[1]//2 - 100, frame.shape[0]//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        cv2.imshow('Smile Detector', frame)
        cv2.waitKey(1000)  # Show welcome message for 1 second
    
    # Add a small delay to slow down processing
    time.sleep(0.1)  # 100ms delay between frames
    
    cv2.imshow('Smile Detector', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()