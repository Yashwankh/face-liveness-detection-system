# 🚀 Quick Start Guide

## Your project is ready to use! Follow these simple steps:

---

## Step 1: Verify Installation ✅

Check that all dependencies are installed:
```bash
pip list
```

You should see packages like:
- face_recognition
- opencv-python
- tensorflow
- numpy
- scikit-learn

---

## Step 2: Add Known Faces 📸

Create folders inside `known_faces/` directory for each person:

```
known_faces/
├── John/
│   ├── john1.jpg
│   ├── john2.jpg
│   └── john3.jpg
└── Sarah/
    ├── sarah1.jpg
    └── sarah2.jpg
```

**Tips for best results:**
- Use clear, well-lit photos
- Face should be clearly visible
- Add 2-3 photos per person
- Different angles/expressions help improve accuracy

---

## Step 3: Run the Application 🎥

### Option A: Face Recognition with Liveness Detection (Recommended)
```bash
python src\LivelinessOnFeed.py
```
This will:
- Detect faces in real-time
- Check if the face is real (not a photo/video)
- Recognize the person
- Mark attendance automatically

### Option B: Simple Face Recognition
```bash
python src\FaceRecogOnFeed.py
```
This will:
- Detect and recognize faces
- Show names on screen
- No liveness detection

### Option C: Test on a Single Image
```bash
python src\FaceRecogOnImage.py
```

---

## Step 4: Exit the Application 🛑

Press **'q'** key to quit the video feed

---

## 📊 View Attendance Records

Attendance is automatically saved in: `attendance.csv`

Open it with Excel or any text editor to see:
- Person Name
- Date
- Time
- Registration Number (if configured)

---

## 🎯 Next Steps

### Customize Settings

Edit `src\FaceRecogOnFeed.py`:

```python
TOLERANCE = 0.6  # Lower = stricter matching (0.0-1.0)
MODEL = 'hog'    # Use 'cnn' for better accuracy (needs GPU)
```

### Train Your Own Liveness Model

If you want to improve liveness detection:

1. **Collect videos**:
   - Real faces: Record video of real people
   - Fake faces: Record video of photos/screens

2. **Generate dataset**:
```bash
python src/gather_examples.py --input videos/real.mov --output dataset/real --detector face_detector --skip 1
python src/gather_examples.py --input videos/fake.mp4 --output dataset/fake --detector face_detector --skip 4
```

3. **Train the model**:
```bash
python src/trainModel.py --dataset dataset --model liveness.model --le le.pickle
```

---

## 🐛 Common Issues & Solutions

### Issue: Camera not working
**Solution**: 
- Check if camera is connected
- Try changing camera index in code: `cv2.VideoCapture(0)` → `cv2.VideoCapture(1)`

### Issue: Face not detected
**Solution**:
- Ensure good lighting
- Move closer to camera
- Face camera directly

### Issue: Wrong person recognized
**Solution**:
- Add more photos of the correct person
- Lower the TOLERANCE value
- Ensure good quality training images

### Issue: Import errors
**Solution**:
```bash
pip install --upgrade -r requirements.txt
```

---

## 📝 Project Files Overview

| File | Purpose |
|------|---------|
| `FaceRecogOnFeed.py` | Basic face recognition on webcam |
| `LivelinessOnFeed.py` | Face recognition + anti-spoofing |
| `FaceRecogOnImage.py` | Test on static images |
| `trainModel.py` | Train custom liveness model |
| `gather_examples.py` | Create training dataset |
| `attendance.csv` | Attendance records |
| `liveness.model` | Pre-trained anti-spoofing model |
| `known_faces/` | Store face images here |

---

## 🎓 Usage Examples

### Example 1: Basic Attendance System
1. Add employee photos in `known_faces/`
2. Run: `python src\FaceRecogOnFeed.py`
3. Employees face the camera
4. Check `attendance.csv` for records

### Example 2: Secure Access with Anti-Spoofing
1. Add authorized user photos
2. Run: `python src\LivelinessOnFeed.py`
3. System checks if person is real (not a photo)
4. Only real faces are recognized and granted access

### Example 3: Classroom Attendance
1. Add student photos in `known_faces/StudentName/`
2. Run the liveness detection version
3. Students face camera one by one
4. Automatic attendance marking with timestamps

---

## 💡 Pro Tips

1. **Better Accuracy**: Use multiple photos per person with different expressions
2. **Faster Processing**: Use 'hog' model instead of 'cnn' if speed is priority
3. **Lighting**: Ensure consistent lighting for best results
4. **Distance**: Stay 1-3 feet from camera for optimal detection
5. **Background**: Plain backgrounds work better for face detection

---

## 📞 Need Help?

- Check `README.md` for detailed documentation
- Check `PROJECT_SETUP_SUMMARY.md` for technical details
- Review project GitHub: https://github.com/Atharva-Gundawar/Face-Recognition-with-Liveliness-detection

---

**Ready to go! Start by adding faces to `known_faces/` folder! 🎉**
