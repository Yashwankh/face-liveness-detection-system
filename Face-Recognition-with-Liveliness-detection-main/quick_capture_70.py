"""
Quick Photo Capture for Roll Number 70
"""

import cv2
import os

roll_number = "70"
folder_path = os.path.join('known_faces', roll_number)
os.makedirs(folder_path, exist_ok=True)

print("="*60)
print(f"PHOTO CAPTURE FOR ROLL NUMBER {roll_number}")
print("="*60)
print()
print("Instructions:")
print("  • Position your face in the frame")
print("  • Press SPACE to capture photo")
print("  • Press Q to quit")
print()
print("="*60)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam!")
    input("Press Enter to exit...")
    exit()

print("\n📸 Camera ready! Press SPACE to capture...")

captured = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Error reading from camera")
        break
    
    # Flip for mirror effect
    frame = cv2.flip(frame, 1)
    
    # Add text overlay
    cv2.putText(frame, f"Roll Number: {roll_number}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "Press SPACE to capture photo", (10, 70),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, "Press Q to quit", (10, 100),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Draw a circle in the center for alignment
    height, width = frame.shape[:2]
    cv2.circle(frame, (width//2, height//2), 150, (0, 255, 0), 2)
    cv2.putText(frame, "Align face here", (width//2 - 80, height//2 + 180),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    cv2.imshow('Capture Photo for Roll 70', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord(' '):
        # Save photo
        filepath = os.path.join(folder_path, 'photo.jpg')
        success = cv2.imwrite(filepath, frame)
        
        if success:
            file_size = os.path.getsize(filepath)
            print(f"\n✅ Photo captured successfully!")
            print(f"📁 Saved to: {os.path.abspath(filepath)}")
            print(f"📏 File size: {file_size:,} bytes")
            print()
            
            # Show success message
            cv2.putText(frame, "CAPTURED! Photo saved!", 
                       (width//2 - 150, height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            cv2.imshow('Capture Photo for Roll 70', frame)
            cv2.waitKey(2000)
            
            captured = True
            break
        else:
            print("❌ Error saving photo!")
            
    elif key == ord('q'):
        print("\n❌ Cancelled")
        break

cap.release()
cv2.destroyAllWindows()

if captured:
    print("="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Run: python RollNumberVerification.py")
    print("2. Enter roll number: 70")
    print("3. Face the camera for verification")
    print("4. Get verified!")
    print()
    print("="*60)
else:
    print("\n⚠️  No photo captured. Please run this script again.")

input("\nPress Enter to exit...")
