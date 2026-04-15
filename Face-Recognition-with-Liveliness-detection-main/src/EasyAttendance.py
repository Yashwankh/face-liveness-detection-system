"""
Easy Attendance System with Auto-Registration
- First time: Press SPACE to register your face
- After registration: Automatic recognition and attendance marking
"""

import cv2
import face_recognition
import os
import csv
from datetime import datetime

KNOWN_FACES_DIR = 'known_faces'
ATTENDANCE_FILE = 'attendance.csv'
TOLERANCE = 0.6

# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)

# Track attendance
marked_today = set()

def mark_attendance(name):
    """Mark attendance in CSV"""
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    time_string = now.strftime('%H:%M:%S')
    today_key = f"{name}_{date_string}"
    
    if today_key in marked_today:
        return False
    
    marked_today.add(today_key)
    
    file_exists = os.path.isfile(ATTENDANCE_FILE)
    with open(ATTENDANCE_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Name', 'Date', 'Time', 'Status'])
        writer.writerow([name, date_string, time_string, 'Present'])
    
    return True

def load_known_faces():
    """Load all known faces"""
    known_faces = []
    known_names = []
    
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
        return known_faces, known_names
    
    for person_name in os.listdir(KNOWN_FACES_DIR):
        person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
        if not os.path.isdir(person_dir):
            continue
        
        for filename in os.listdir(person_dir):
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            
            filepath = os.path.join(person_dir, filename)
            try:
                image = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_faces.append(encodings[0])
                    known_names.append(person_name)
            except:
                continue
    
    return known_faces, known_names

def save_face(frame, name):
    """Save a face to known_faces"""
    person_dir = os.path.join(KNOWN_FACES_DIR, name)
    os.makedirs(person_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(person_dir, f'photo_{timestamp}.jpg')
    cv2.imwrite(filepath, frame)
    return filepath

print("="*70)
print(" "*15 + "FACE RECOGNITION ATTENDANCE SYSTEM")
print("="*70)
print()

# Load known faces
print("Loading registered faces...")
known_faces, known_names = load_known_faces()

if len(known_faces) == 0:
    print("⚠️  No faces registered yet!")
    print()
    print("="*70)
    print("FIRST TIME SETUP:")
    print("1. Face the camera")
    print("2. Press SPACE to register your face")
    print("3. Enter your name when prompted")
    print("="*70)
else:
    print(f"✅ Found {len(set(known_names))} registered person(s)")
    print()
    print("="*70)
    print("READY FOR ATTENDANCE")
    print("- Face the camera for automatic recognition")
    print("- Press SPACE to register a new person")
    print("- Press Q to quit")
    print("="*70)

print()

# Start camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam!")
    exit()

# Notification system
success_notification = None
notification_start = 0
NOTIFICATION_DURATION = 90  # frames

registration_mode = False
frame_count = 0

print("✅ Camera started successfully!")
print()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # Detect faces
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)
    
    # Process each face
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        
        name = "Unknown"
        color = RED
        
        if len(known_faces) > 0:
            # Compare with known faces
            matches = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)
            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
                color = GREEN
                
                # Try to mark attendance
                if mark_attendance(name):
                    success_notification = name
                    notification_start = frame_count
                    print(f"\n✅ ATTENDANCE MARKED: {name} at {datetime.now().strftime('%H:%M:%S')}")
        
        # Draw rectangle
        cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
        
        # Draw name label
        cv2.rectangle(frame, (left, bottom), (right, bottom + 35), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)
    
    # Show success notification
    if success_notification and (frame_count - notification_start) <= NOTIFICATION_DURATION:
        msg = f"{success_notification} - SUCCESSFULLY VERIFIED!"
        msg_size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        msg_x = (frame.shape[1] - msg_size[0]) // 2
        msg_y = 60
        
        # Green background
        cv2.rectangle(frame, (msg_x - 20, msg_y - 45),
                     (msg_x + msg_size[0] + 20, msg_y + 10),
                     GREEN, cv2.FILLED)
        
        # White text
        cv2.putText(frame, msg, (msg_x, msg_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, WHITE, 2)
        
        # Checkmark
        cv2.circle(frame, (msg_x - 50, msg_y - 20), 25, GREEN, -1)
        cv2.putText(frame, "✓", (msg_x - 65, msg_y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, WHITE, 3)
    
    # Instructions
    if len(known_faces) == 0:
        cv2.putText(frame, "Press SPACE to register your face", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)
    else:
        cv2.putText(frame, "Press SPACE to register new person | Q to quit", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
    
    cv2.imshow('Face Recognition Attendance', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord(' '):
        # Register new face
        if len(face_locations) > 0:
            print("\n" + "="*70)
            name = input("Enter name for this person: ").strip()
            if name:
                filepath = save_face(frame, name)
                print(f"✅ Registered: {name}")
                print(f"📁 Photo saved: {filepath}")
                print("="*70)
                print("\nReloading faces...")
                known_faces, known_names = load_known_faces()
                print(f"✅ Now tracking {len(set(known_names))} person(s)")
                print()
            else:
                print("❌ Registration cancelled (no name entered)")
        else:
            print("\n⚠️  No face detected! Please face the camera and try again.")

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*70)
print("SESSION SUMMARY")
print("="*70)
print(f"Total attendance marked: {len(marked_today)}")
print(f"Attendance file: {ATTENDANCE_FILE}")
print("\nThank you!")
print("="*70)
