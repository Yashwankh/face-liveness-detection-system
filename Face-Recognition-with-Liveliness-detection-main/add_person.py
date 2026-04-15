#!/usr/bin/env python
"""
Helper Script to Add New Person
Makes it easy to create folders and test if photos work
"""

import os
import cv2
import face_recognition
from pathlib import Path

KNOWN_FACES_DIR = 'known_faces'

def list_current_people():
    """Show who is already in the system"""
    print("\n" + "="*60)
    print("Current People in System:")
    print("="*60)
    
    if not os.path.exists(KNOWN_FACES_DIR):
        print("❌ known_faces directory not found!")
        return
    
    people = [d for d in os.listdir(KNOWN_FACES_DIR) 
              if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]
    
    if not people:
        print("No people added yet.")
        print("\nFolders exist but are empty:")
    else:
        print(f"\nTotal: {len(people)} people\n")
    
    for person in people:
        person_path = os.path.join(KNOWN_FACES_DIR, person)
        photos = [f for f in os.listdir(person_path) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
        
        status = f"✅ {len(photos)} photos" if photos else "⚠️  0 photos (EMPTY)"
        print(f"  📁 {person:<20} {status}")
        
        if photos:
            for photo in photos:
                print(f"     └─ {photo}")
    
    print("="*60 + "\n")

def add_new_person():
    """Create a new folder for a person"""
    print("\n" + "="*60)
    print("Add New Person")
    print("="*60)
    
    name = input("\nEnter person's name (e.g., John, Sarah): ").strip()
    
    if not name:
        print("❌ Name cannot be empty!")
        return
    
    person_dir = os.path.join(KNOWN_FACES_DIR, name)
    
    if os.path.exists(person_dir):
        print(f"\n⚠️  Folder '{name}' already exists!")
        print(f"Location: {os.path.abspath(person_dir)}")
    else:
        os.makedirs(person_dir, exist_ok=True)
        print(f"\n✅ Created folder: {name}")
        print(f"📁 Location: {os.path.abspath(person_dir)}")
        print(f"\n💡 Now add photos to this folder!")
    
    print("="*60 + "\n")

def test_photo(photo_path):
    """Test if a photo is valid and contains a face"""
    print(f"\n🔍 Testing: {photo_path}")
    
    if not os.path.exists(photo_path):
        print(f"❌ File not found!")
        return False
    
    try:
        # Try to load image
        image = face_recognition.load_image_file(photo_path)
        print("✅ Image loaded successfully")
        
        # Try to find faces
        face_locations = face_recognition.face_locations(image)
        
        if len(face_locations) == 0:
            print("❌ No faces detected in this photo!")
            print("💡 Tips:")
            print("   - Make sure face is clearly visible")
            print("   - Check lighting is good")
            print("   - Face should be front-facing")
            return False
        
        elif len(face_locations) == 1:
            print(f"✅ Found 1 face - Perfect!")
            
            # Try to encode
            encodings = face_recognition.face_encodings(image, face_locations)
            if encodings:
                print("✅ Face encoding successful")
                print("✅ This photo will work great!")
                return True
            else:
                print("⚠️  Could not encode face")
                return False
        
        else:
            print(f"⚠️  Found {len(face_locations)} faces")
            print("💡 Photos with single face work best")
            print("   But this will still work")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_photos_menu():
    """Test photos in a folder"""
    print("\n" + "="*60)
    print("Test Photos")
    print("="*60)
    
    list_current_people()
    
    name = input("Enter person's name to test their photos: ").strip()
    person_dir = os.path.join(KNOWN_FACES_DIR, name)
    
    if not os.path.exists(person_dir):
        print(f"❌ Folder '{name}' not found!")
        return
    
    photos = [f for f in os.listdir(person_dir) 
             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
    
    if not photos:
        print(f"\n⚠️  No photos found in {name}'s folder!")
        print(f"📁 Add photos to: {os.path.abspath(person_dir)}")
        return
    
    print(f"\n📸 Found {len(photos)} photos. Testing...\n")
    
    good_photos = 0
    for photo in photos:
        photo_path = os.path.join(person_dir, photo)
        if test_photo(photo_path):
            good_photos += 1
        print()
    
    print("="*60)
    print(f"\nResults: {good_photos}/{len(photos)} photos are good")
    
    if good_photos == len(photos):
        print("🎉 All photos are perfect! Ready to use!")
    elif good_photos > 0:
        print("✅ Some photos are good - app will work")
        print("💡 Consider replacing bad photos for better accuracy")
    else:
        print("❌ No good photos found!")
        print("💡 Please add clear photos with visible faces")
    
    print("="*60 + "\n")

def open_folder():
    """Open known_faces folder in File Explorer"""
    print("\n" + "="*60)
    print("Opening Folder")
    print("="*60)
    
    abs_path = os.path.abspath(KNOWN_FACES_DIR)
    
    try:
        os.startfile(abs_path)
        print(f"\n✅ Opened: {abs_path}")
        print("💡 Add photos to the person's folder")
    except Exception as e:
        print(f"❌ Could not open folder: {e}")
        print(f"\n📁 Manual path: {abs_path}")
    
    print("="*60 + "\n")

def main_menu():
    """Main menu"""
    while True:
        print("\n" + "="*60)
        print("Face Recognition - Add Person Helper")
        print("="*60)
        print("\n1. 📋 List current people")
        print("2. ➕ Add new person")
        print("3. 🔍 Test photos")
        print("4. 📁 Open known_faces folder")
        print("5. ❌ Exit")
        print("\n" + "="*60)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            list_current_people()
            input("Press Enter to continue...")
        elif choice == '2':
            add_new_person()
            input("Press Enter to continue...")
        elif choice == '3':
            test_photos_menu()
            input("Press Enter to continue...")
        elif choice == '4':
            open_folder()
            input("Press Enter to continue...")
        elif choice == '5':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5")

if __name__ == "__main__":
    print("\n🎉 Face Recognition Helper Tool")
    print("This tool helps you add people and test photos\n")
    
    # Check if we're in the right directory
    if not os.path.exists(KNOWN_FACES_DIR):
        print(f"⚠️  Warning: '{KNOWN_FACES_DIR}' directory not found")
        print("Make sure you're running this from the project root directory")
        input("\nPress Enter to continue anyway...")
    
    main_menu()
