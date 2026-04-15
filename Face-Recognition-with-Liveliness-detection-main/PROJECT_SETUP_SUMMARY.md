# Face Recognition with Liveliness Detection - Project Setup Summary

## ✅ Setup Status: COMPLETE

All dependencies and libraries have been successfully installed and the project is ready to use.

---

## 📁 Project Structure

```
Face-Recognition-with-Liveliness-detection-main/
├── .gitignore                          # Gitignore file
├── attendance.csv                      # Recorded attendance database
├── face_detector/                      # Face detector models
│   ├── deploy.prototxt                 
│   └── res10_300x300_ssd_iter_140000.caffemodel
├── known_faces/                        # Store faces to be recognized (EMPTY - add your faces here)
├── le.pickle                           # Supporting pickle file for face detection
├── LICENSE                             
├── livelinessModel/                    
│   └── livenessnet.py                  # Liveness detection model class
├── liveness.model                      # Pre-trained liveness model
├── plot.png                            # Training accuracy plot
├── PROJECTINFO.md                      
├── README.md                           
├── requirements.txt                    # Updated Python dependencies
├── src/                                # Source code directory
│   ├── FaceRecogOnFeed.py              # Face recognition on live webcam feed
│   ├── FaceRecogOnImage.py             # Face recognition on static image
│   ├── gather_examples.py              # Generate dataset for training
│   ├── jsExample.py                    # Face recognition with JavaScript support
│   ├── LivelinessOnFeed.py             # Liveness detection on video feed
│   ├── livenessDemo.py                 # Liveness detection on image
│   └── trainModel.py                   # Train the liveness model
└── videos/                             # Videos for dataset creation
```

---

## 📦 Installed Dependencies

### Core Libraries
- **Python Version**: Python 3.11.x
- **NumPy**: 1.26.4 (numerical computing)
- **OpenCV**: 4.8.1.78 and 4.11.0.86 (computer vision)
- **TensorFlow**: 2.19.0 (deep learning framework)
- **Keras**: 3.9.2 (high-level neural networks API)

### Face Recognition & Detection
- **face_recognition**: 1.3.0 (face recognition library)
- **face_recognition_models**: 0.3.0 (pre-trained models)
- **dlib**: 19.24.8 (machine learning toolkit)
- **imutils**: 0.5.4 (image processing utilities)

### Data Science & Visualization
- **scikit-learn**: 1.3.2 (machine learning algorithms)
- **matplotlib**: 3.10.1 (plotting library)
- **pandas**: 2.2.3 (data manipulation)
- **Pillow**: 10.1.0 (image processing)

### Additional Libraries
- **scipy**: 1.15.2
- **scikit-image**: 0.25.2
- **insightface**: 0.7.3
- **mediapipe**: 0.10.21
- **torch**: 2.7.1+cu118 (PyTorch with CUDA support)

---

## 🚀 How to Use

### 1. Add Known Faces
Before running face recognition, add images of people to recognize:
```
known_faces/
├── person1_name/
│   ├── image1.jpg
│   └── image2.jpg
├── person2_name/
│   ├── image1.jpg
│   └── image2.jpg
```

### 2. Run Face Recognition on Webcam
```bash
python src\FaceRecogOnFeed.py
```
- Press 'q' to quit the video feed

### 3. Run Face Recognition on Image
```bash
python src\FaceRecogOnImage.py
```

### 4. Run Liveness Detection
```bash
python src\LivelinessOnFeed.py
```

### 5. Train Your Own Liveness Model (Optional)

#### Step 1: Gather Training Data
```bash
python src/gather_examples.py --input videos/real.mov --output dataset/real --detector face_detector --skip 1
python src/gather_examples.py --input videos/fake.mp4 --output dataset/fake --detector face_detector --skip 4
```

#### Step 2: Train the Model
```bash
python src/trainModel.py --dataset dataset --model liveness.model --le le.pickle
```

---

## 🎯 Key Features

1. **Face Recognition**: Uses HOG (Histogram of Oriented Gradients) algorithm with 98% accuracy
2. **Liveness Detection**: CNN-based model to prevent spoofing attacks (photos, videos)
3. **Attendance System**: Automatically records attendance with timestamp to CSV
4. **Real-time Processing**: Works with webcam feed in real-time
5. **Multiple Face Detection**: Can detect and recognize multiple faces simultaneously

---

## 🔧 Technical Details

### Algorithms Used
- **Face Detection**: HOG (Histogram of Oriented Gradients)
- **Face Recognition**: SVM (Support Vector Machine) classifier
- **Liveness Detection**: Convolutional Neural Network (CNN)

### Model Performance
- Face Recognition Accuracy: ~98%
- Liveness Detection: Binary classification (real/fake faces)

---

## ⚙️ System Requirements

- **OS**: Windows/Linux/MacOS
- **Python**: 3.8 or higher
- **Webcam**: Required for live feed functionality
- **RAM**: Minimum 4GB recommended
- **GPU**: Optional (for CUDA acceleration with CNN model)

---

## 📝 Notes

1. The `known_faces` directory is currently empty - add face images before running face recognition
2. The project includes a pre-trained liveness model (`liveness.model`)
3. Attendance records are saved in `attendance.csv`
4. For better accuracy, use multiple images per person in different angles/lighting
5. Press 'q' to exit video feeds

---

## 🐛 Troubleshooting

### Common Issues:

**1. Camera not found**
- Check if webcam is connected and not in use by other applications
- Try changing camera index in code: `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`

**2. No faces detected**
- Ensure good lighting
- Face should be clearly visible to the camera
- Try adjusting TOLERANCE value in the code (default: 0.6)

**3. Import errors**
- Ensure all dependencies are installed: `pip list`
- Reinstall if needed: `pip install -r requirements.txt`

---

## 📚 Additional Resources

- Face Recognition Library: https://github.com/ageitgey/face_recognition
- OpenCV Documentation: https://docs.opencv.org/
- TensorFlow Documentation: https://www.tensorflow.org/

---

**Setup Date**: October 16, 2025
**Status**: ✅ Ready to use
