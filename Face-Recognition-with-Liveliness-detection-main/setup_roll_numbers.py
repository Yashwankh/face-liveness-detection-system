"""
Setup Script for Roll Number Based System
Helps organize photos by roll number
"""

import os
import shutil
import cv2

KNOWN_FACES_DIR = 'known_faces'

def create_sample_structure():
    """Create sample folder structure"""
    print("="*70)
    print("ROLL NUMBER FOLDER SETUP")
    print("="*70)
    print()
    
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
        print(f"✅ Created {KNOWN_FACES_DIR}/ directory")
    
    print("\nCurrent folder structure:")
    print(f"{KNOWN_FACES_DIR}/")
    
    existing_folders = [d for d in os.listdir(KNOWN_FACES_DIR) 
                       if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]
    
    if existing_folders:
        for folder in sorted(existing_folders):
            folder_path = os.path.join(KNOWN_FACES_DIR, folder)
            photos = [f for f in os.listdir(folder_path) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            status = f"({len(photos)} photos)" if photos else "(empty)"
            print(f"  ├── {folder}/ {status}")
    else:
        print("  (empty)")
    
    print()
    print("="*70)
    print()

def add_roll_number():
    """Add a new roll number folder"""
    print("ADD NEW STUDENT BY ROLL NUMBER")
    print("-"*70)
    print()
    
    roll_number = input("Enter roll number (e.g., 70, 101): ").strip()
    
    if not roll_number:
        print("❌ Roll number cannot be empty!")
        return
    
    folder_path = os.path.join(KNOWN_FACES_DIR, roll_number)
    
    if os.path.exists(folder_path):
        print(f"\n⚠️  Roll number {roll_number} already exists!")
        print(f"📁 Location: {os.path.abspath(folder_path)}")
        
        choice = input("\nDo you want to add more photos to this roll number? (y/n): ")
        if choice.lower() != 'y':
            return
    else:
        os.makedirs(folder_path)
        print(f"\n✅ Created folder for roll number: {roll_number}")
        print(f"📁 Location: {os.path.abspath(folder_path)}")
    
    print()
    print("="*70)
    print("CAPTURE PHOTO OPTIONS:")
    print("="*70)
    print("1. Capture from webcam now")
    print("2. I'll add photos manually later")
    print()
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == '1':
        capture_photo_from_webcam(roll_number, folder_path)
    else:
        print()
        print("="*70)
        print(f"📸 Please add photo(s) manually to:")
        print(f"   {os.path.abspath(folder_path)}")
        print()
        print("Photo requirements:")
        print("  • Clear, front-facing photo")
        print("  • Good lighting")
        print("  • File format: .jpg, .jpeg, or .png")
        print("  • File name: any name (e.g., photo.jpg, student.jpg)")
        print("="*70)

def capture_photo_from_webcam(roll_number, folder_path):
    """Capture photo from webcam"""
    print()
    print("="*70)
    print("WEBCAM PHOTO CAPTURE")
    print("="*70)
    print("Instructions:")
    print("  • Look at the camera")
    print("  • Press SPACE to capture")
    print("  • Press Q to cancel")
    print("="*70)
    print()
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Could not open webcam!")
        return
    
    print("📸 Camera ready...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Add text
        cv2.putText(frame, f"Roll Number: {roll_number}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, "Press SPACE to capture | Q to quit", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imshow('Capture Photo', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            # Save photo
            filename = f'photo_{roll_number}.jpg'
            filepath = os.path.join(folder_path, filename)
            cv2.imwrite(filepath, frame)
            
            print(f"\n✅ Photo captured and saved!")
            print(f"📁 File: {filepath}")
            print(f"📏 Size: {os.path.getsize(filepath)} bytes")
            
            # Show captured frame
            cv2.putText(frame, "CAPTURED!", (frame.shape[1]//2 - 100, frame.shape[0]//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
            cv2.imshow('Capture Photo', frame)
            cv2.waitKey(2000)
            break
            
        elif key == ord('q'):
            print("\n❌ Cancelled")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print()

def list_all_students():
    """List all registered students"""
    print()
    print("="*70)
    print("REGISTERED STUDENTS")
    print("="*70)
    print()
    
    if not os.path.exists(KNOWN_FACES_DIR):
        print("No students registered yet.")
        return
    
    folders = [d for d in os.listdir(KNOWN_FACES_DIR) 
              if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]
    
    if not folders:
        print("No students registered yet.")
        return
    
    print(f"Total: {len(folders)} students\n")
    
    for i, roll_number in enumerate(sorted(folders), 1):
        folder_path = os.path.join(KNOWN_FACES_DIR, roll_number)
        photos = [f for f in os.listdir(folder_path) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        status = "✅" if photos else "⚠️ "
        print(f"{i:3}. Roll Number: {roll_number:10} | Photos: {len(photos)} {status}")
    
    print()
    print("="*70)

def main_menu():
    """Main menu"""
    while True:
        print()
        print("="*70)
        print("ROLL NUMBER VERIFICATION SYSTEM - SETUP")
        print("="*70)
        print()
        print("1. View current setup")
        print("2. Add new student (by roll number)")
        print("3. List all registered students")
        print("4. Open known_faces folder")
        print("5. Exit")
        print()
        print("="*70)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            create_sample_structure()
        elif choice == '2':
            add_roll_number()
        elif choice == '3':
            list_all_students()
        elif choice == '4':
            try:
                os.startfile(os.path.abspath(KNOWN_FACES_DIR))
                print(f"\n✅ Opened: {os.path.abspath(KNOWN_FACES_DIR)}")
            except:
                print(f"\n📁 Path: {os.path.abspath(KNOWN_FACES_DIR)}")
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print()
    print("="*70)
    print(" "*15 + "ROLL NUMBER SYSTEM SETUP TOOL")
    print("="*70)
    print()
    print("This tool helps you set up the folder structure for the")
    print("Roll Number based Face Verification System")
    print()
    print("Folder structure example:")
    print(f"  {KNOWN_FACES_DIR}/")
    print("    ├── 70/          (Roll number 70)")
    print("    │   └── photo.jpg")
    print("    ├── 101/         (Roll number 101)")
    print("    │   └── photo.jpg")
    print("    └── 205/         (Roll number 205)")
    print("        └── photo.jpg")
    print()
    
    main_menu()
