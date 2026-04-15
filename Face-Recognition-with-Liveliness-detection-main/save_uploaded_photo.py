"""
Script to save uploaded photo to known_faces directory
Usage: Place this script and run it with the photo you want to add
"""

import os
import shutil
from pathlib import Path

# Get the uploaded image
# Note: You'll need to drag and drop your photo into the known_faces/User/ folder
# Or copy it manually

KNOWN_FACES_DIR = 'known_faces'

print("="*60)
print("Photo Upload Helper")
print("="*60)
print()

# Check current setup
user_folder = os.path.join(KNOWN_FACES_DIR, 'User')

if os.path.exists(user_folder):
    print(f"✅ Folder created: {user_folder}")
    print(f"📁 Full path: {os.path.abspath(user_folder)}")
    print()
    print("="*60)
    print("NEXT STEPS:")
    print("="*60)
    print()
    print("1. Copy your photo to this folder:")
    print(f"   {os.path.abspath(user_folder)}")
    print()
    print("2. The photo you uploaded shows a person in formal attire")
    print("   Save it as: user_photo.jpg")
    print()
    print("3. Or drag and drop your photo into that folder")
    print()
    print("="*60)
    print()
    
    # List files in folder
    files = os.listdir(user_folder)
    if files:
        print("Current files in User folder:")
        for f in files:
            file_path = os.path.join(user_folder, f)
            size = os.path.getsize(file_path)
            print(f"  📄 {f} ({size} bytes)")
    else:
        print("⚠️  Folder is empty - add your photo!")
    
    print()
    print("="*60)
else:
    print("❌ User folder not found!")
    
print("\n💡 TIP: You can rename 'User' folder to your actual name")
print("   Right-click folder → Rename → Type your name")
print()
