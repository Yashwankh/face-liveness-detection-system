# 📸 How to Add Your Photos - Complete Guide

## 🎯 Quick Answer: Where to Save Photos

### Your Photo Locations:

**For Ashikka:**
```
C:\Users\91935\OneDrive\Desktop\Face-Recognition-with-Liveliness-detection-main\known_faces\Ashikka\
```

**For David:**
```
C:\Users\91935\OneDrive\Desktop\Face-Recognition-with-Liveliness-detection-main\known_faces\David\
```

**For New Person:**
1. Create new folder in `known_faces\`
2. Name it with person's name (e.g., `John`)
3. Add photos inside that folder

---

## 📝 Step-by-Step Instructions

### Method 1: Using File Explorer (Easiest)

1. **Open Folder:**
   - Press `Win + E` to open File Explorer
   - Navigate to: `Desktop\Face-Recognition-with-Liveliness-detection-main\known_faces`

2. **Choose Your Folder:**
   - Open `Ashikka` folder (or `David` folder)

3. **Add Photos:**
   - Copy/paste your photos into this folder
   - OR drag and drop photos here
   - OR right-click → Paste

4. **Done!** You can now run the application

---

### Method 2: Add New Person

1. **Create New Folder:**
   - Go to: `known_faces\`
   - Right-click → New → Folder
   - Name it: `YourName` (e.g., `John`, `Sarah`, `Mike`)

2. **Add Photos:**
   - Open the new folder
   - Add 2-5 photos of that person

3. **Run App:**
   - App will automatically detect the new person!

---

## 📷 Photo Requirements

### ✅ Good Photos:
- **Face clearly visible** - No sunglasses, hats covering face
- **Good lighting** - Not too dark or too bright
- **Front-facing** - Face looking at camera
- **High quality** - Clear, not blurry
- **Single person** - One face per photo (preferred)
- **Multiple angles** - 2-5 photos from different angles

### ❌ Avoid:
- ❌ Blurry or low-quality images
- ❌ Face covered by mask, sunglasses, or hands
- ❌ Very dark or backlit photos
- ❌ Side profile only (add at least one front-facing)
- ❌ Group photos (better to crop to single person)

---

## 🗂️ Supported Image Formats

✅ **Supported:**
- `.jpg` / `.jpeg`
- `.png`
- `.bmp`
- `.gif` (first frame)

📝 **File Names:** Can be anything
- `photo1.jpg` ✅
- `me.png` ✅
- `IMG_20231016.jpg` ✅
- `selfie.jpeg` ✅

---

## 📊 Folder Structure Examples

### Example 1: Office Attendance System
```
known_faces/
├── John_Smith/
│   ├── john1.jpg
│   ├── john2.jpg
│   └── john3.jpg
├── Sarah_Johnson/
│   ├── sarah_front.jpg
│   ├── sarah_side.jpg
│   └── sarah_smile.jpg
└── Mike_Wilson/
    ├── mike1.png
    └── mike2.png
```

### Example 2: Classroom Attendance
```
known_faces/
├── Student_101_Rahul/
│   ├── photo1.jpg
│   └── photo2.jpg
├── Student_102_Priya/
│   ├── image1.jpg
│   └── image2.jpg
└── Student_103_Amit/
    ├── pic1.jpg
    └── pic2.jpg
```

### Example 3: Your Current Setup
```
known_faces/
├── Ashikka/          ← Add Ashikka's photos here
│   └── (empty - add photos!)
└── David/            ← Add David's photos here
    └── (empty - add photos!)
```

---

## 🚀 After Adding Photos

### Run the Application:

```bash
# Basic face recognition:
python src\FaceRecogOnFeed.py

# With liveness detection (anti-spoofing):
python src\LivelinessOnFeed.py
```

### What Happens:
1. App loads all photos from `known_faces/`
2. Creates face encodings for each person
3. Starts webcam
4. Detects faces in real-time
5. Shows name when face matches

---

## 🎬 How It Works

### 1. Training (When App Starts)
```
Loading known faces...
- Found Ashikka with 3 photos
- Found David with 2 photos
Total: 2 people, 5 photos
Ready!
```

### 2. Recognition (During Use)
```
[Webcam shows live video]
[Green box around face]
[Name displayed: "Ashikka"]
```

### 3. Attendance (Auto-saved)
```
Name: Ashikka
Date: 2025-10-16
Time: 16:05:30
```
Saved to: `attendance.csv`

---

## 💡 Pro Tips

### Tip 1: Multiple Photos = Better Accuracy
```
Ashikka/
├── front.jpg        ← Face looking at camera
├── slight_left.jpg  ← Head turned slightly left
├── slight_right.jpg ← Head turned slightly right
├── smiling.jpg      ← Different expression
└── neutral.jpg      ← Normal expression
```

### Tip 2: Test Different Lighting
- Indoor lighting photo
- Natural daylight photo
- Mix of both helps with different conditions

### Tip 3: Use Recent Photos
- Recent photos work best
- Update if appearance changes significantly

### Tip 4: Folder Name = Display Name
- Folder name `John_Smith` → Shows "John_Smith"
- Folder name `Ashikka` → Shows "Ashikka"
- Use clear, readable names

---

## 🔧 Quick Commands

### Check What's in Folders:
```bash
# List all known faces
dir known_faces
```

### Add Multiple People at Once:
```bash
# Create folders
mkdir known_faces\Person1
mkdir known_faces\Person2
mkdir known_faces\Person3
```

---

## 📱 Getting Your Photos

### From Phone:
1. Take photos on phone
2. Transfer via USB/Email/Cloud
3. Save to appropriate folder

### From Webcam:
1. Use Windows Camera app
2. Take photos
3. Save to `known_faces\YourName\`

### Existing Photos:
1. Find photos on computer
2. Copy to `known_faces\YourName\`
3. Done!

---

## ✅ Checklist

Before running the app:
- [ ] Created folder with person's name
- [ ] Added 2-5 clear photos
- [ ] Photos show face clearly
- [ ] Good lighting in photos
- [ ] Photos are .jpg or .png format
- [ ] Ready to run!

---

## 🎯 Example Walkthrough

### Let's Add Ashikka's Photo:

**Step 1:** Open File Explorer
```
Win + E
```

**Step 2:** Navigate to folder
```
Desktop → Face-Recognition-with-Liveliness-detection-main → known_faces → Ashikka
```

**Step 3:** Add photos
```
[Copy your photos here]
- ashikka1.jpg
- ashikka2.jpg
- ashikka3.jpg
```

**Step 4:** Run application
```bash
python src\FaceRecogOnFeed.py
```

**Step 5:** Test!
```
Face camera → App shows "Ashikka" → Success! 🎉
```

---

## 🆘 Troubleshooting

### Problem: "No faces found"
**Solution:** Make sure photo shows face clearly

### Problem: "Wrong person recognized"
**Solution:** Add more photos of correct person

### Problem: "Can't find folder"
**Solution:** Check path:
```
C:\Users\91935\OneDrive\Desktop\Face-Recognition-with-Liveliness-detection-main\known_faces\
```

### Problem: "App crashes on start"
**Solution:** Make sure at least one folder has photos

---

## 📞 Need Help?

See other guides:
- `QUICK_START.md` - How to use the app
- `PROJECT_SETUP_SUMMARY.md` - Technical details
- `README.md` - Full documentation

---

# 🎉 Ready to Start!

1. **Add your photos** to `known_faces\Ashikka\` or `known_faces\David\`
2. **Run the app**: `python src\FaceRecogOnFeed.py`
3. **Face the camera** and see your name appear!

**Current Folders:**
- `known_faces\Ashikka\` ← Add Ashikka's photos here
- `known_faces\David\` ← Add David's photos here
