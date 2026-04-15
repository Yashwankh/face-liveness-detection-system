import face_recognition
import os
import cv2
import csv
from datetime import datetime

KNOWN_FACES_DIR = 'known_faces'
TOLERANCE = 0.6
FRAME_THICKNESS = 3
FONT_THICKNESS = 2
MODEL = 'hog'
ATTENDANCE_FILE = 'attendance.csv'

# Color codes
GREEN = (0, 255, 0)
RED = (0, 0, 255)
BLUE = (255, 0, 0)
WHITE = (255, 255, 255)

# Track who has been marked present today
marked_today = set()

def mark_attendance(name):
    """Mark attendance in CSV file"""
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    time_string = now.strftime('%H:%M:%S')
    
    # Create unique key for today
    today_key = f"{name}_{date_string}"
    
    # Check if already marked today
    if today_key in marked_today:
        return False  # Already marked
    
    # Mark as present
    marked_today.add(today_key)
    
    # Write to CSV
    file_exists = os.path.isfile(ATTENDANCE_FILE)
    
    with open(ATTENDANCE_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(['Name', 'Date', 'Time', 'Status'])
        
        # Write attendance
        writer.writerow([name, date_string, time_string, 'Present'])
    
    return True  # Successfully marked

def load_existing_attendance():
    """Load today's attendance to avoid duplicates"""
    if not os.path.exists(ATTENDANCE_FILE):
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        with open(ATTENDANCE_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == today:
                    marked_today.add(f"{row['Name']}_{today}")
    except Exception as e:
        print(f"Note: Could not load existing attendance: {e}")

# Returns (R, G, B) from name
def name_to_color(name):
    color = [(ord(c.lower())-97)*8 for c in name[:3]]
    return color

print('='*60)
print('FACE RECOGNITION ATTENDANCE SYSTEM')
print('='*60)
print()
print('Loading known faces...')

# Load existing attendance
load_existing_attendance()

known_faces = []
known_names = []

# Check if known_faces directory exists and has content
if not os.path.exists(KNOWN_FACES_DIR):
    print(f"❌ Error: '{KNOWN_FACES_DIR}' directory not found!")
    print("Please create the directory and add face images.")
    exit()

face_folders = [d for d in os.listdir(KNOWN_FACES_DIR) 
                if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]

if not face_folders:
    print(f"❌ Error: No person folders found in '{KNOWN_FACES_DIR}'!")
    print("Please add folders with face images.")
    exit()

total_photos = 0

# Load known faces
for name in face_folders:
    person_dir = os.path.join(KNOWN_FACES_DIR, name)
    photos = [f for f in os.listdir(person_dir) 
             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
    
    if not photos:
        print(f"⚠️  Warning: No photos found for {name}")
        continue
    
    for filename in photos:
        filepath = os.path.join(person_dir, filename)
        
        try:
            # Load image
            image = face_recognition.load_image_file(filepath)
            
            # Get face encodings
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) == 0:
                print(f"⚠️  No face found in: {filename}")
                continue
            
            # Use first face
            encoding = encodings[0]
            
            # Append to known faces
            known_faces.append(encoding)
            known_names.append(name)
            total_photos += 1
            
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")

if total_photos == 0:
    print("❌ No valid face photos found!")
    print("Please add clear photos with visible faces.")
    exit()

print(f"✅ Loaded {len(set(known_names))} people with {total_photos} photos")
print()
print('Starting camera...')
print('='*60)
print()
print('INSTRUCTIONS:')
print('- Face the camera for recognition')
print('- Attendance will be marked automatically')
print('- Press "Q" to quit')
print()
print('='*60)

# Start webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam!")
    print("Please check if your camera is connected.")
    exit()

# Success notification timer
success_notifications = {}  # {name: frame_count}
NOTIFICATION_DURATION = 90  # Show for 3 seconds at 30fps

frame_count = 0

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("❌ Error reading from camera")
        break
    
    frame_count += 1
    
    # Process every frame for smooth detection
    locations = face_recognition.face_locations(frame, model=MODEL)
    encodings = face_recognition.face_encodings(frame, locations)
    
    # Draw on frame
    for face_encoding, face_location in zip(encodings, locations):
        # Compare with known faces
        results = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)
        match = None
        
        if True in results:
            # Get the matched name
            match = known_names[results.index(True)]
            
            # Try to mark attendance
            if mark_attendance(match):
                success_notifications[match] = frame_count
                print(f"✅ ATTENDANCE MARKED: {match} at {datetime.now().strftime('%H:%M:%S')}")
            
            # Face location coordinates
            top, right, bottom, left = face_location
            
            # Draw green rectangle around face
            cv2.rectangle(frame, (left, top), (right, bottom), GREEN, FRAME_THICKNESS)
            
            # Draw name label
            cv2.rectangle(frame, (left, bottom), (right, bottom + 35), GREEN, cv2.FILLED)
            cv2.putText(frame, match, (left + 6, bottom + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, FONT_THICKNESS)
            
            # Check if we should show success notification
            if match in success_notifications:
                frames_since = frame_count - success_notifications[match]
                if frames_since <= NOTIFICATION_DURATION:
                    # Show success message
                    msg = "SUCCESSFULLY VERIFIED!"
                    msg_size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                    msg_x = (frame.shape[1] - msg_size[0]) // 2
                    msg_y = 80
                    
                    # Background rectangle
                    cv2.rectangle(frame, (msg_x - 10, msg_y - 40), 
                                (msg_x + msg_size[0] + 10, msg_y + 10), 
                                GREEN, cv2.FILLED)
                    
                    # Success text
                    cv2.putText(frame, msg, (msg_x, msg_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, WHITE, 3)
                    
                    # Checkmark symbol
                    cv2.putText(frame, "✓", (msg_x - 50, msg_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2, GREEN, 4)
                else:
                    # Remove from notifications
                    del success_notifications[match]
        else:
            # Unknown face
            top, right, bottom, left = face_location
            
            # Draw red rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), RED, FRAME_THICKNESS)
            
            # Draw unknown label
            cv2.rectangle(frame, (left, bottom), (right, bottom + 35), RED, cv2.FILLED)
            cv2.putText(frame, "Unknown", (left + 6, bottom + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, FONT_THICKNESS)
    
    # Display instructions
    cv2.putText(frame, "Press 'Q' to quit", (10, frame.shape[0] - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
    
    # Display frame
    cv2.imshow("Face Recognition Attendance System", frame)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

print()
print('='*60)
print('SESSION SUMMARY')
print('='*60)
print(f"Total people recognized today: {len(marked_today)}")
print(f"Attendance saved to: {ATTENDANCE_FILE}")
print()
print("Thank you for using the Face Recognition Attendance System!")
print('='*60)
