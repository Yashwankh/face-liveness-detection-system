"""
Quick setup to capture your photo from webcam
This will take a photo and save it to known_faces/User/
"""

import cv2
import os
from datetime import datetime

KNOWN_FACES_DIR = 'known_faces'
PERSON_NAME = 'User'

def capture_photo():
    """Capture photo from webcam"""
    
    person_dir = os.path.join(KNOWN_FACES_DIR, PERSON_NAME)
    os.makedirs(person_dir, exist_ok=True)
    
    print("="*60)
    print("WEBCAM PHOTO CAPTURE")
    print("="*60)
    print()
    print("Instructions:")
    print("1. Look at the camera")
    print("2. Press SPACE to capture photo")
    print("3. Press Q to quit without capturing")
    print()
    print("="*60)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Could not open webcam!")
        return False
    
    print("\n📸 Camera ready! Press SPACE to capture, Q to quit")
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Error reading frame")
            break
        
        # Display instructions on frame
        cv2.putText(frame, "Press SPACE to capture", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press Q to quit", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Capture Photo', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # Space bar
            # Save photo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'photo_{timestamp}.jpg'
            filepath = os.path.join(person_dir, filename)
            
            cv2.imwrite(filepath, frame)
            
            print(f"\n✅ Photo saved: {filepath}")
            print(f"📁 Size: {os.path.getsize(filepath)} bytes")
            
            # Show captured image
            cv2.putText(frame, "CAPTURED!", (frame.shape[1]//2 - 100, frame.shape[0]//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            cv2.imshow('Capture Photo', frame)
            cv2.waitKey(2000)  # Show for 2 seconds
            
            cap.release()
            cv2.destroyAllWindows()
            return True
            
        elif key == ord('q'):
            print("\n❌ Cancelled")
            cap.release()
            cv2.destroyAllWindows()
            return False
    
    cap.release()
    cv2.destroyAllWindows()
    return False

if __name__ == "__main__":
    print("\n🎯 This will capture your photo for face recognition")
    
    choice = input("\nDo you want to capture a photo now? (y/n): ").lower()
    
    if choice == 'y':
        if capture_photo():
            print("\n✅ Setup complete!")
            print("Now you can run: python src\\AttendanceSystem.py")
        else:
            print("\n⚠️  No photo captured")
    else:
        print("\n💡 Alternative: Manually add your photo to:")
        print(f"   {os.path.abspath(os.path.join(KNOWN_FACES_DIR, PERSON_NAME))}")
