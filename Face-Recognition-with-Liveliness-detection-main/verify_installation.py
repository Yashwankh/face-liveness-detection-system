#!/usr/bin/env python
"""
Installation Verification Script
Run this to verify all dependencies are properly installed
"""

import sys

def check_import(module_name, package_name=None):
    """Try to import a module and report status"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {package_name:25} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name:25} - FAILED: {e}")
        return False

def main():
    print("=" * 60)
    print("Face Recognition with Liveness Detection")
    print("Installation Verification")
    print("=" * 60)
    print()
    
    # Check Python version
    print(f"Python Version: {sys.version}")
    print()
    
    print("Checking Core Dependencies:")
    print("-" * 60)
    
    # Core libraries
    results = []
    results.append(check_import("cv2", "opencv-python"))
    results.append(check_import("face_recognition", "face_recognition"))
    results.append(check_import("tensorflow", "tensorflow"))
    results.append(check_import("numpy", "numpy"))
    results.append(check_import("sklearn", "scikit-learn"))
    results.append(check_import("imutils", "imutils"))
    results.append(check_import("matplotlib", "matplotlib"))
    results.append(check_import("PIL", "Pillow"))
    
    print()
    print("=" * 60)
    
    if all(results):
        print("✅ ALL DEPENDENCIES INSTALLED SUCCESSFULLY!")
        print()
        print("You can now run:")
        print("  - python src\\FaceRecogOnFeed.py")
        print("  - python src\\LivelinessOnFeed.py")
        print()
        print("Don't forget to add faces to the 'known_faces' directory!")
    else:
        print("❌ SOME DEPENDENCIES ARE MISSING!")
        print("Please run: pip install -r requirements.txt")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
