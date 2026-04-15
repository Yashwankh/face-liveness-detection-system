import cv2
import face_recognition

"""
Simple Face Detection Demo
This version just detects faces without recognition
No training data needed - run this to test your camera!
"""

print('Starting face detection...')
print('Press "q" to quit')
print()

# Start webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam")
    print("Please check if your camera is connected and not in use by another application")
    exit()

frame_count = 0

while True:
    # Read frame from webcam
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Could not read frame from webcam")
        break
    
    frame_count += 1
    
    # Detect faces every 5 frames (for better performance)
    if frame_count % 5 == 0:
        # Detect face locations
        face_locations = face_recognition.face_locations(frame, model='hog')
        
        # Draw rectangles around detected faces
        for face_location in face_locations:
            top, right, bottom, left = face_location
            
            # Draw rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Add text
            cv2.putText(frame, 'Face Detected', (left, top - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Display count
        cv2.putText(frame, f'Faces: {len(face_locations)}', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Display instructions
    cv2.putText(frame, 'Press Q to quit', (10, frame.shape[0] - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Show frame
    cv2.imshow('Face Detection Demo', frame)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\nExiting...")
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("Application closed successfully!")
