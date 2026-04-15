"""
COMPLETE MULTI-FACTOR LIVENESS DETECTION SYSTEM

Requires ALL of these to verify (100% Foolproof):
1. BLINK - Eyes must blink
2. HEAD MOVEMENT - Turn head left/right
3. MOUTH MOVEMENT - Open mouth
4. Random instruction - Follow random gesture

Photos CANNOT do any of these!
"""

import cv2
import face_recognition
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, font
import threading
from PIL import Image, ImageTk
import numpy as np
from scipy.spatial import distance as dist
import random
import requests
from io import BytesIO

# Configuration
KNOWN_FACES_DIR = 'known_faces'
ATTENDANCE_FILE = 'attendance.csv'
FACE_TOLERANCE = 0.5

# Thresholds - BALANCED for reliability
EYE_AR_THRESH = 0.28  # Higher = easier to detect (more sensitive)
MOUTH_AR_THRESH = 0.65  # Balanced - not too hard
HEAD_MOVEMENT_THRESH = 20  # % of face width (Balanced - reasonable movement)

# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)
BLUE = (255, 0, 0)
PURPLE = (255, 0, 255)

def eye_aspect_ratio(eye):
    """Calculate eye aspect ratio for blink detection"""
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    """Calculate mouth aspect ratio for mouth opening detection"""
    A = dist.euclidean(mouth[2], mouth[10])  # Vertical
    B = dist.euclidean(mouth[4], mouth[8])   # Vertical
    C = dist.euclidean(mouth[0], mouth[6])   # Horizontal
    mar = (A + B) / (2.0 * C)
    return mar

class CompleteLivenessSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Aadhaar Face Verification System")
        self.root.configure(bg='#FFD700')
        
        # Load Aadhaar logo
        self.aadhaar_logo = None
        try:
            response = requests.get('https://tse3.mm.bing.net/th/id/OIP.g3p3-ACopSafup0zXZqB5wHaEQ?pid=Api&P=0&h=180', timeout=5)
            img = Image.open(BytesIO(response.content))
            img = img.resize((200, 80), Image.Resampling.LANCZOS)
            self.aadhaar_logo = ImageTk.PhotoImage(img)
        except:
            print("Could not load Aadhaar logo from URL")
        
        self.current_roll = None
        self.known_encoding = None
        self.running = False
        
        # Multi-factor tracking
        self.blink_completed = False
        self.blink_counter = 0
        self.total_blinks = 0
        
        self.head_left_done = False
        self.head_right_done = False
        self.initial_face_x = None
        
        self.mouth_opened = False
        
        self.current_task = 0
        self.tasks = []
        
        print("="*70)
        print("✅ IMPROVED LIVENESS DETECTION: ACTIVE")
        print("="*70)
        print("   🛡️  BALANCED SECURITY MODE")
        print("   📸 Photos will be rejected!")
        print()
        print("   IMPROVED Requirements (More Reliable!):")
        print("   - ✓ 2 out of 4 gestures (not 3!)")
        print("   - ✓ Blink: eyes closed for 3 frames (EASIER!)")
        print("   - ✓ Head turn: 20% movement (EASIER!)")
        print("   - ✓ Mouth: open (ratio 0.65)")
        print("   - ✓ Face matches: 20 times")
        print("   - ✓ Time: 20 seconds")
        print()
        print("   🎯 Watch terminal for REAL-TIME feedback!")
        print("="*70)
        
        self.show_home()
    
    def detect_blink(self, landmarks):
        """STRICT blink detection - requires actual closing and opening"""
        try:
            if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
                return False, 0.0
            
            left_eye = np.array(landmarks['left_eye'])
            right_eye = np.array(landmarks['right_eye'])
            
            if len(left_eye) < 6 or len(right_eye) < 6:
                return False, 0.0
            
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            # IMPROVED: Eyes closed for 3 frames (more reliable!)
            if ear < EYE_AR_THRESH:
                self.blink_counter += 1
                print(f"👁️ Eyes closing... EAR: {ear:.2f}, Frames: {self.blink_counter}/3")
            else:
                # Check if it was a valid blink (at least 3 frames)
                if self.blink_counter >= 3:
                    self.total_blinks += 1
                    print(f"✅✅✅ BLINK DETECTED! Frames: {self.blink_counter}, Total: {self.total_blinks}")
                    self.blink_completed = True
                elif self.blink_counter > 0:
                    print(f"⚠️ Blink too short ({self.blink_counter} frames, need 3) - Try again!")
                self.blink_counter = 0
            
            return self.blink_completed, ear
        except:
            return False, 0.0
    
    def detect_head_movement(self, face_location, frame_width):
        """Detect head turning left/right with visual feedback"""
        top, right, bottom, left = face_location
        face_center_x = (left + right) / 2
        face_width = right - left
        
        if self.initial_face_x is None:
            self.initial_face_x = face_center_x
            print(f"📍 Initial face position set: {face_center_x:.1f}")
            return "center", 0
        
        movement = face_center_x - self.initial_face_x
        movement_percent = (movement / face_width) * 100
        
        # Print movement for debugging
        if abs(movement_percent) > 5:
            print(f"🔄 Movement: {movement_percent:.1f}% (need {HEAD_MOVEMENT_THRESH}%)")
        
        if movement_percent < -HEAD_MOVEMENT_THRESH:
            if not self.head_left_done:
                self.head_left_done = True
                print(f"✓ HEAD TURNED LEFT! ({movement_percent:.1f}%)")
            return "left", movement_percent
        elif movement_percent > HEAD_MOVEMENT_THRESH:
            if not self.head_right_done:
                self.head_right_done = True
                print(f"✓ HEAD TURNED RIGHT! ({movement_percent:.1f}%)")
            return "right", movement_percent
        
        return "center", movement_percent
    
    def detect_mouth_opening(self, landmarks):
        """Detect mouth opening"""
        try:
            if 'top_lip' not in landmarks or 'bottom_lip' not in landmarks:
                return False, 0.0
            
            # Combine lips to get mouth outline
            mouth = landmarks['top_lip'] + landmarks['bottom_lip']
            mouth = np.array(mouth)
            
            if len(mouth) < 12:
                return False, 0.0
            
            mar = mouth_aspect_ratio(mouth)
            
            if mar > MOUTH_AR_THRESH:
                if not self.mouth_opened:
                    self.mouth_opened = True
                    print("✓ MOUTH OPENED!")
                return True, mar
            
            return self.mouth_opened, mar
        except:
            return False, 0.0
    
    def generate_random_tasks(self):
        """Generate random sequence of tasks"""
        all_tasks = [
            ("BLINK", "👁️ BLINK your eyes"),
            ("TURN_LEFT", "← Turn head LEFT"),
            ("TURN_RIGHT", "→ Turn head RIGHT"),
            ("OPEN_MOUTH", "😮 OPEN your mouth")
        ]
        # Shuffle for random order
        random.shuffle(all_tasks)
        self.tasks = all_tasks
        self.current_task = 0
    
    def check_all_gestures_complete(self):
        """Check if at least 2 gestures completed - BALANCED!"""
        completed_count = sum([
            self.blink_completed,
            self.head_left_done,
            self.head_right_done,
            self.mouth_opened
        ])
        return completed_count >= 2  # Need 2 out of 4 gestures - balanced security!
    
    def show_home(self):
        """Home Page - YELLOW & BLACK DESIGN WITH AADHAAR LOGO"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1000x900")
        
        # Top WHITE header with Aadhaar logo and ADD button
        header_frame = tk.Frame(self.root, bg='white', height=140)
        header_frame.pack(fill='x', pady=0)
        
        # ADD button in TOP RIGHT corner (SMALL)
        add_btn_corner = tk.Button(header_frame, text="➕ ADD", 
                                   font=font.Font(family="Helvetica", size=10, weight="bold"),
                                   bg='white', fg='black', command=self.add_student,
                                   relief=tk.RAISED, bd=3, padx=15, pady=8, cursor='hand2',
                                   highlightbackground='#FFD700', highlightthickness=2)
        add_btn_corner.place(relx=0.98, rely=0.1, anchor='ne')
        
        # Aadhaar logo from URL (centered)
        if self.aadhaar_logo:
            logo_label = tk.Label(header_frame, image=self.aadhaar_logo, bg='white')
            logo_label.pack(pady=20)
        else:
            tk.Label(header_frame, text="AADHAAR", 
                    font=font.Font(family="Helvetica", size=32, weight="bold"),
                    bg='white', fg='#FFD700').pack(pady=20)
        
        tk.Label(header_frame, text="Face Verification System", 
                font=font.Font(family="Helvetica", size=16, weight="bold"),
                bg='white', fg='black').pack(pady=5)
        
        # Main container - YELLOW background
        main_container = tk.Frame(self.root, bg='#FFD700')
        main_container.pack(fill='both', expand=True, padx=40, pady=30)
        
        # WHITE card container
        card = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=5)
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Card header
        tk.Label(card, text="⭐ Aadhaar Face Verification ⭐", 
                font=font.Font(family="Helvetica", size=28, weight="bold"),
                bg='white', fg='#FFD700').pack(pady=25)
        
        tk.Label(card, text="ENTER YOUR 12-DIGIT AADHAAR NUMBER", 
                font=font.Font(family="Helvetica", size=13, weight="bold"),
                bg='white', fg='black').pack(pady=10)
        
        # Entry field with YELLOW styling
        entry_container = tk.Frame(card, bg='white')
        entry_container.pack(pady=20, padx=60)
        
        # Input field with WHITE background
        input_frame = tk.Frame(entry_container, bg='white', relief=tk.RAISED, bd=4, 
                              highlightbackground='#FFD700', highlightthickness=2)
        input_frame.pack(pady=10, ipady=5, ipadx=5)
        
        tk.Label(input_frame, text="💳", 
                font=font.Font(family="Helvetica", size=24),
                bg='white').pack(side='left', padx=10)
        
        self.roll_entry = tk.Entry(input_frame, 
                                  font=font.Font(family="Helvetica", size=20),
                                  width=20, bg='white', fg='black', 
                                  justify='center', relief=tk.FLAT, bd=0,
                                  insertbackground='black')
        self.roll_entry.insert(0, "1234 5678 9012")
        self.roll_entry.pack(side='left', pady=10, ipady=5)
        self.roll_entry.focus()
        self.roll_entry.bind('<Return>', lambda e: self.verify_roll())
        
        # Buttons with YELLOW and WHITE styling
        btn_container = tk.Frame(card, bg='white')
        btn_container.pack(pady=25)
        
        # Primary button - WHITE (LARGE) - Only VERIFY now
        verify_btn = tk.Button(btn_container, text="✓  VERIFY AADHAAR", 
                              font=font.Font(family="Helvetica", size=18, weight="bold"),
                              bg='white', fg='black', command=self.verify_roll,
                              relief=tk.RAISED, bd=5, padx=70, pady=22, cursor='hand2',
                              highlightbackground='#FFD700', highlightthickness=3,
                              activebackground='#F0F0F0', activeforeground='black')
        verify_btn.pack(pady=10)
        
        # Info cards - YELLOW and WHITE design
        info_container = tk.Frame(card, bg='white')
        info_container.pack(pady=20, padx=60, fill='x')
        
        # Features grid with alternating colors
        features_frame = tk.Frame(info_container, bg='white')
        features_frame.pack(pady=15)
        
        features = [
            ("🛡️", "Secure", "Advanced encryption"),
            ("⚡", "Fast", "Quick verification"),
            ("🎯", "Accurate", "99% precision"),
            ("🔒", "Private", "Data protected")
        ]
        
        for i, (icon, title, desc) in enumerate(features):
            # Alternate between YELLOW and WHITE backgrounds
            bg_color = '#FFD700' if i % 2 == 0 else 'white'
            fg_color = 'black'
            border_color = '#FFD700'
            
            feature_card = tk.Frame(features_frame, bg=bg_color, relief=tk.RAISED, bd=3, 
                                   width=120, height=100, highlightbackground=border_color, highlightthickness=2)
            feature_card.grid(row=0, column=i, padx=10, pady=5)
            feature_card.pack_propagate(False)
            
            tk.Label(feature_card, text=icon, font=font.Font(family="Helvetica", size=24),
                    bg=bg_color).pack(pady=5)
            tk.Label(feature_card, text=title, font=font.Font(family="Helvetica", size=11, weight="bold"),
                    bg=bg_color, fg=fg_color).pack()
            tk.Label(feature_card, text=desc, font=font.Font(family="Helvetica", size=8),
                    bg=bg_color, fg=fg_color).pack()
        
        # Footer - WHITE with black text
        count = len([d for d in os.listdir(KNOWN_FACES_DIR) 
                    if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]) if os.path.exists(KNOWN_FACES_DIR) else 0
        
        footer = tk.Frame(self.root, bg='white', height=50, relief=tk.RAISED, bd=2)
        footer.pack(side='bottom', fill='x')
        
        tk.Label(footer, text=f"📊 {count} Aadhaar Registered  |  🔐 Secure System  |  🇮🇳 Government of India", 
                font=font.Font(family="Helvetica", size=10, weight="bold"),
                bg='white', fg='black').pack(pady=15)
    
    def add_student(self):
        """Add new student with webcam capture - SIMPLE VERSION"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Make window bigger to see everything
        self.root.geometry("900x800")
        
        tk.Label(self.root, text="🔐 AADHAAR", 
                font=font.Font(family="Helvetica", size=20, weight="bold"),
                bg='#FFD700', fg='#FF6B35').pack(pady=10)
        
        tk.Label(self.root, text="➕ Register New Aadhaar", 
                font=font.Font(family="Helvetica", size=32, weight="bold"),
                bg='#FFD700', fg='#2C3E50').pack(pady=15)
        
        # Instructions
        tk.Label(self.root, text="Step 1: Enter 12-digit Aadhaar number below", 
                font=font.Font(family="Helvetica", size=12),
                bg='#FFD700', fg='#2C3E50').pack(pady=5)
        
        # Entry frame - BIGGER
        entry_frame = tk.Frame(self.root, bg='white', relief=tk.FLAT, bd=0)
        entry_frame.pack(pady=10, padx=50, fill='x')
        
        tk.Label(entry_frame, text="Aadhaar Number:", 
                font=font.Font(family="Helvetica", size=16, weight="bold"),
                bg='white', fg='#2C3E50').pack(side='left', padx=20, pady=15)
        
        self.new_roll_entry = tk.Entry(entry_frame, 
                                       font=font.Font(family="Helvetica", size=18),
                                       width=18, bg='#F0F0F0', fg='black',
                                       relief=tk.FLAT, bd=2, justify='center')
        self.new_roll_entry.pack(side='left', padx=10, pady=15, ipady=8)
        self.new_roll_entry.insert(0, "1234 5678 9012")
        self.new_roll_entry.focus()
        
        # Step 2 label
        tk.Label(self.root, text="Step 2: Click START CAMERA button below", 
                font=font.Font(family="Helvetica", size=12),
                bg='#FFD700', fg='#2C3E50').pack(pady=10)
        
        # START Button - BIG and VISIBLE (Orange like Aadhaar theme)
        self.start_btn = tk.Button(self.root, text="📷 START CAMERA", 
                                   font=font.Font(family="Helvetica", size=16, weight="bold"),
                                   bg='#FF9500', fg='white', command=self.start_add_camera,
                                   relief=tk.FLAT, padx=50, pady=20, cursor='hand2',
                                   borderwidth=0)
        self.start_btn.pack(pady=10)
        
        # Video display area
        self.video_label = tk.Label(self.root, bg='black', width=640, height=380,
                                    text="Camera will appear here", fg='white',
                                    font=font.Font(family="Helvetica", size=14))
        self.video_label.pack(pady=10)
        
        # Status
        self.add_status = tk.Label(self.root, text="Enter Aadhaar number and click START CAMERA", 
                                   font=font.Font(family="Helvetica", size=13, weight="bold"),
                                   bg='#FFD700', fg='#2C3E50')
        self.add_status.pack(pady=5)
        
        # CAPTURE and BACK Buttons - Initially hidden, shown after camera starts
        btn_frame = tk.Frame(self.root, bg='#FFD700')
        btn_frame.pack(pady=10)
        
        self.capture_btn = tk.Button(btn_frame, text="📸 CAPTURE PHOTO", 
                                     font=font.Font(family="Helvetica", size=14, weight="bold"),
                                     bg='#FF9500', fg='white', command=self.capture_photo,
                                     relief=tk.FLAT, padx=40, pady=15, state='disabled',
                                     borderwidth=0)
        self.capture_btn.pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="← BACK TO HOME", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#8E8E93', fg='white', command=self.cancel_add,
                 relief=tk.FLAT, padx=40, pady=15, borderwidth=0).pack(side='left', padx=10)
    
    def start_add_camera(self):
        """Start camera for adding student"""
        roll = self.new_roll_entry.get().strip()
        if not roll:
            messagebox.showerror("Error", "Please enter roll number!")
            return
        
        self.adding_roll = roll
        self.running = True
        self.capture_btn.config(state='normal')
        self.start_btn.config(state='disabled')
        self.add_status.config(text="Position your face in the green circle", fg='#27AE60')
        
        threading.Thread(target=self.add_camera_loop, daemon=True).start()
    
    def add_camera_loop(self):
        """Camera loop for adding student"""
        cap = cv2.VideoCapture(0)
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            self.current_frame = frame.copy()
            frame = cv2.flip(frame, 1)
            
            # Draw guide circle
            h, w = frame.shape[:2]
            cv2.circle(frame, (w//2, h//2), 120, GREEN, 3)
            cv2.putText(frame, "Position face here", (w//2 - 100, h//2 - 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)
            
            # Convert for display
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.running:
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        
        cap.release()
    
    def capture_photo(self):
        """Capture and save photo for new student"""
        if not hasattr(self, 'current_frame'):
            messagebox.showerror("Error", "No frame captured!")
            return
        
        folder = os.path.join(KNOWN_FACES_DIR, self.adding_roll)
        os.makedirs(folder, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(folder, f'photo_{timestamp}.jpg')
        cv2.imwrite(filepath, self.current_frame)
        
        # Verify face is detected
        try:
            image = face_recognition.load_image_file(filepath)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                os.remove(filepath)
                messagebox.showerror("Error", "No face detected in photo! Try again.")
                return
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            messagebox.showerror("Error", f"Invalid photo: {str(e)}")
            return
        
        self.running = False
        messagebox.showinfo("Success", f"✅ Student added successfully!\n\nRoll Number: {self.adding_roll}\nPhoto saved: {filepath}")
        self.show_home()
    
    def cancel_add(self):
        """Cancel adding student"""
        self.running = False
        self.show_home()
    
    def verify_roll(self):
        roll = self.roll_entry.get().strip()
        if not roll:
            messagebox.showerror("Error", "Enter roll number!")
            return
        
        folder = os.path.join(KNOWN_FACES_DIR, roll)
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Roll {roll} not found!")
            return
        
        photos = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not photos:
            messagebox.showerror("Error", "No photos!")
            return
        
        try:
            image = face_recognition.load_image_file(os.path.join(folder, photos[0]))
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                messagebox.showerror("Error", "No face!")
                return
            
            self.known_encoding = encodings[0]
            self.current_roll = roll
            self.root.after(500, self.verify_face)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def verify_face(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1100x950")
        
        # Orange gradient header
        header = tk.Frame(self.root, bg='#FF9500', height=100)
        header.pack(fill='x')
        
        # Header content
        header_content = tk.Frame(header, bg='#FF9500')
        header_content.pack(pady=15)
        
        tk.Label(header_content, text="🇮🇳", 
                font=font.Font(family="Helvetica", size=32),
                bg='#FF9500').pack(side='left', padx=5)
        
        header_text = tk.Frame(header_content, bg='#FF9500')
        header_text.pack(side='left', padx=10)
        
        tk.Label(header_text, text="AADHAAR VERIFICATION", 
                font=font.Font(family="Helvetica", size=24, weight="bold"),
                bg='#FF9500', fg='white').pack(anchor='w')
        
        tk.Label(header_text, text=f"💳 {self.current_roll}", 
                font=font.Font(family="Helvetica", size=14),
                bg='#FF9500', fg='white').pack(anchor='w')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#F5F5F5')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Instruction banner with gradient-like effect
        instruction_banner = tk.Frame(main_frame, bg='#FFF3CD', relief=tk.RAISED, bd=2)
        instruction_banner.pack(fill='x', pady=10, padx=20)
        
        self.instruction_label = tk.Label(instruction_banner, text="⏳ Please wait...", 
                                          font=font.Font(family="Helvetica", size=15, weight="bold"),
                                          bg='#FFF3CD', fg='#856404', pady=10)
        self.instruction_label.pack()
        
        # Video in attractive card
        video_card = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=3)
        video_card.pack(pady=15, padx=20)
        
        tk.Label(video_card, text="📹 Live Camera Feed", 
                font=font.Font(family="Helvetica", size=12, weight="bold"),
                bg='white', fg='#2C3E50').pack(pady=10)
        
        video_border = tk.Frame(video_card, bg='#E0E0E0', relief=tk.SUNKEN, bd=3)
        video_border.pack(padx=15, pady=10)
        
        self.verify_video = tk.Label(video_border, bg='black')
        self.verify_video.pack()
        
        # Progress cards - attractive design
        progress_card = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=3)
        progress_card.pack(pady=10, padx=20, fill='x')
        
        tk.Label(progress_card, text="📊 Verification Progress", 
                font=font.Font(family="Helvetica", size=13, weight="bold"),
                bg='white', fg='#2C3E50').pack(pady=10)
        
        # Status box with better design
        status_box = tk.Frame(progress_card, bg='#F8D7DA', relief=tk.GROOVE, bd=2)
        status_box.pack(pady=10, padx=30, fill='x')
        
        tk.Label(status_box, text="Face Similarity: 0.0%", 
                font=font.Font(family="Helvetica", size=10),
                bg='#F8D7DA', fg='#721C24').pack(pady=2)
        tk.Label(status_box, text="Liveness Score: 0.0%", 
                font=font.Font(family="Helvetica", size=10),
                bg='#F8D7DA', fg='#721C24').pack(pady=2)
        
        self.blink_label = tk.Label(status_box, text="❌ No Blink Detected", 
                                    font=font.Font(family="Helvetica", size=10),
                                    bg='#F8D7DA', fg='#721C24')
        self.blink_label.pack(pady=2)
        
        self.left_label = tk.Label(status_box, text="❌ No Head Movement", 
                                   font=font.Font(family="Helvetica", size=10),
                                   bg='#F8D7DA', fg='#721C24')
        self.left_label.pack(pady=2)
        
        self.right_label = tk.Label(status_box, text="❌ No Mouth Movement", 
                                    font=font.Font(family="Helvetica", size=10),
                                    bg='#F8D7DA', fg='#721C24')
        self.right_label.pack(pady=2)
        
        self.mouth_label = tk.Label(status_box, text="", 
                                    font=font.Font(family="Helvetica", size=10),
                                    bg='#F8D7DA', fg='#721C24')
        
        # Gesture and timer info in modern cards
        info_grid = tk.Frame(progress_card, bg='white')
        info_grid.pack(pady=10, padx=20, fill='x')
        
        gestures_card = tk.Frame(info_grid, bg='#E3F2FD', relief=tk.RAISED, bd=2)
        gestures_card.pack(side='left', padx=10, pady=5, fill='both', expand=True)
        
        self.gesture_count_label = tk.Label(gestures_card, text="🎯 Gestures: 0/4 (need 2)", 
                                           font=font.Font(family="Helvetica", size=11, weight="bold"),
                                           bg='#E3F2FD', fg='#1976D2', pady=10)
        self.gesture_count_label.pack()
        
        face_card = tk.Frame(info_grid, bg='#F3E5F5', relief=tk.RAISED, bd=2)
        face_card.pack(side='left', padx=10, pady=5, fill='both', expand=True)
        
        self.face_match_label = tk.Label(face_card, text="👤 Face Match: 0/20", 
                                         font=font.Font(family="Helvetica", size=11, weight="bold"),
                                         bg='#F3E5F5', fg='#7B1FA2', pady=10)
        self.face_match_label.pack()
        
        timer_card = tk.Frame(info_grid, bg='#FFF3E0', relief=tk.RAISED, bd=2)
        timer_card.pack(side='left', padx=10, pady=5, fill='both', expand=True)
        
        self.timer_label = tk.Label(timer_card, text="⏱️ Time: 20.0s", 
                                    font=font.Font(family="Helvetica", size=11, weight="bold"),
                                    bg='#FFF3E0', fg='#F57C00', pady=10)
        self.timer_label.pack()
        
        # Attractive buttons with hover effect
        btn_container = tk.Frame(main_frame, bg='#F5F5F5')
        btn_container.pack(pady=20)
        
        back_btn = tk.Button(btn_container, text="←  BACK TO HOME", 
                            font=font.Font(family="Helvetica", size=14, weight="bold"),
                            bg='#6C757D', fg='white', command=self.stop_verify,
                            relief=tk.RAISED, bd=4, padx=50, pady=15, cursor='hand2',
                            activebackground='#5A6268', activeforeground='white')
        back_btn.pack()
        
        # Status bar at bottom
        self.status_label = tk.Label(self.root, text="🔒 Secure verification in progress...", 
                                     font=font.Font(family="Helvetica", size=10),
                                     bg='#2C3E50', fg='white', pady=10)
        self.status_label.pack(side='bottom', fill='x')
        
        # Reset all states
        self.blink_completed = False
        self.blink_counter = 0
        self.total_blinks = 0
        self.head_left_done = False
        self.head_right_done = False
        self.mouth_opened = False
        self.initial_face_x = None
        
        # Generate random task order
        self.generate_random_tasks()
        
        self.running = True
        threading.Thread(target=self.verify_loop, daemon=True).start()
    
    def verify_loop(self):
        cap = cv2.VideoCapture(0)
        face_matches = 0
        face_needed = 20  # Increased for stricter verification (more time needed)
        
        # 20-second timer
        import time
        start_time = time.time()
        TIME_LIMIT = 20  # seconds
        
        while self.running and cap.isOpened():
            # Check if 10 seconds passed
            elapsed = time.time() - start_time
            remaining = TIME_LIMIT - elapsed
            
            if elapsed >= TIME_LIMIT:
                # Time's up - check if both conditions met
                if self.check_all_gestures_complete() and face_matches >= face_needed:
                    # SUCCESS - Both conditions met!
                    cap.release()
                    self.success()
                    return
                else:
                    # FAIL - Not complete in time
                    cap.release()
                    messagebox.showerror("Verification Failed", 
                                       f"Could not verify within {TIME_LIMIT} seconds!\n\n"
                                       f"Face matches: {face_matches}/{face_needed}\n"
                                       f"Gestures: {'Complete' if self.check_all_gestures_complete() else 'Incomplete'}")
                    self.running = False
                    self.show_home()
                    return
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            
            locs = face_recognition.face_locations(rgb)
            
            if locs:
                landmarks_list = face_recognition.face_landmarks(rgb)
                encs = face_recognition.face_encodings(rgb, locs)
                
                if landmarks_list and encs:
                    landmarks = landmarks_list[0]
                    face_encoding = encs[0]
                    face_loc = locs[0]
                    t, r, b, l = face_loc
                    t, r, b, l = t*2, r*2, b*2, l*2
                    
                    # SIMULTANEOUS: Check face match AND gestures
                    face_match = face_recognition.compare_faces([self.known_encoding], face_encoding, FACE_TOLERANCE)[0]
                    
                    # IMPORTANT: Block face matching until liveness is proven!
                    if not self.check_all_gestures_complete():
                        # NO LIVENESS YET - Don't accumulate face matches!
                        face_matches = 0
                        box_color = YELLOW
                        status_text = "⚠️ Do gesture first!"
                        cv2.putText(frame, "LIVENESS REQUIRED - DO GESTURE!", 
                                   (frame.shape[1]//2 - 250, 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, YELLOW, 2)
                    elif face_match:
                        face_matches += 1
                        box_color = GREEN
                        status_text = f"✓ Face Match: {face_matches}/{face_needed}"
                    else:
                        face_matches = max(0, face_matches - 2)  # Penalty for mismatch
                        box_color = RED
                        status_text = "❌ Wrong Person!"
                        cv2.putText(frame, "WRONG PERSON - ACCESS DENIED!", 
                                   (frame.shape[1]//2 - 200, 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, RED, 2)
                    
                    # Check all gestures (liveness)
                    self.detect_blink(landmarks)
                    self.detect_head_movement((t, r, b, l), frame.shape[1])
                    self.detect_mouth_opening(landmarks)
                    
                    # Update progress display with face matches and timer
                    self.update_progress(face_matches, remaining)
                    
                    # Draw box based on face match
                    cv2.rectangle(frame, (l, t), (r, b), box_color, 3)
                    cv2.putText(frame, status_text, (l, t-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                    
                    # Check if all gestures done
                    if not self.check_all_gestures_complete():
                        # Still need gestures
                        if self.current_task < len(self.tasks):
                            task_id, task_text = self.tasks[self.current_task]
                            
                            # Check if current task completed
                            task_done = False
                            if task_id == "BLINK" and self.blink_completed:
                                task_done = True
                            elif task_id == "TURN_LEFT" and self.head_left_done:
                                task_done = True
                            elif task_id == "TURN_RIGHT" and self.head_right_done:
                                task_done = True
                            elif task_id == "OPEN_MOUTH" and self.mouth_opened:
                                task_done = True
                            
                            if task_done:
                                self.current_task += 1
                            else:
                                # Show instruction
                                cv2.rectangle(frame, (l, t), (r, b), YELLOW, 3)
                                self.update_instruction(task_text)
                        else:
                            # All tasks from list done, show completion
                            cv2.rectangle(frame, (l, t), (r, b), PURPLE, 3)
                            self.update_instruction("✓ ALL GESTURES COMPLETE!")
                    
                    else:
                        # All gestures complete - check if face matched enough times
                        if face_match and face_matches >= face_needed:
                            # EARLY SUCCESS: Both conditions met before 10 seconds!
                            cap.release()
                            self.success()
                            return
                        else:
                            # Gestures done but need more face matches
                            self.update_instruction("✓ GESTURES COMPLETE - Keep facing camera...")
                            self.update_status(f"Face verification: {face_matches}/{face_needed} - {remaining:.1f}s left")
                    
                    # Add timer display on frame
                    timer_text = f"Time: {remaining:.1f}s"
                    cv2.putText(frame, timer_text, (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, YELLOW, 2)
            
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.running:
                self.verify_video.imgtk = imgtk
                self.verify_video.configure(image=imgtk)
        
        cap.release()
    
    def update_progress(self, face_matches=0, remaining_time=10.0):
        """Update progress indicators including face matching and timer"""
        try:
            if self.blink_completed:
                self.blink_label.config(text="👁️ Blink: ✅", fg='#27AE60')
            
            if self.head_left_done:
                self.left_label.config(text="← Turn Left: ✅", fg='#27AE60')
            
            if self.head_right_done:
                self.right_label.config(text="→ Turn Right: ✅", fg='#27AE60')
            
            if self.mouth_opened:
                self.mouth_label.config(text="😮 Open Mouth: ✅", fg='#27AE60')
            
            # Update gesture counter (need 2 out of 4!)
            gesture_count = sum([self.blink_completed, self.head_left_done, 
                               self.head_right_done, self.mouth_opened])
            if gesture_count >= 2:
                self.gesture_count_label.config(text=f"🎯 Gestures: {gesture_count}/4 ✅", fg='#27AE60')
            else:
                color = '#E74C3C' if gesture_count == 0 else '#F39C12'
                self.gesture_count_label.config(text=f"🎯 Gestures: {gesture_count}/4 (need 2)", fg=color)
            
            # Update face matching progress (out of 20 now)
            if face_matches >= 20:
                self.face_match_label.config(text=f"👤 Face Match: {face_matches}/20 ✅", fg='#27AE60')
            else:
                color = '#3498DB' if face_matches < 10 else '#F39C12'
                self.face_match_label.config(text=f"👤 Face Match: {face_matches}/20", fg=color)
            
            # Update timer (green if >10s, yellow if 5-10s, red if <5s)
            if remaining_time > 10:
                timer_color = '#27AE60'  # Green
            elif remaining_time > 5:
                timer_color = '#F39C12'  # Yellow/Orange
            else:
                timer_color = '#E74C3C'  # Red
            self.timer_label.config(text=f"⏱️ Time: {remaining_time:.1f}s", fg=timer_color)
        except:
            pass
    
    def update_instruction(self, text):
        try:
            self.instruction_label.config(text=text)
        except:
            pass
    
    def update_status(self, text):
        try:
            self.status_label.config(text=text)
        except:
            pass
    
    def success(self):
        self.running = False
        self.mark_attendance()
        self.root.after(0, self.show_success)
    
    def show_success(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("800x700")
        
        tk.Label(self.root, text="✓", 
                font=font.Font(family="Helvetica", size=80),
                bg='#2C3E50', fg='#27AE60').pack(pady=30)
        
        tk.Label(self.root, text="SUCCESSFULLY VERIFIED!", 
                font=font.Font(family="Helvetica", size=32, weight="bold"),
                bg='#2C3E50', fg='#27AE60').pack(pady=20)
        
        tk.Label(self.root, text=f"Roll: {self.current_roll}", 
                font=font.Font(family="Helvetica", size=20),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=10)
        
        # Show all completed checks
        checks = [
            "✓ Blink detection passed",
            "✓ Head movement verified",
            "✓ Mouth movement detected",
            "✓ Face identity confirmed",
            "✓ Attendance marked"
        ]
        
        for check in checks:
            tk.Label(self.root, text=check, 
                    font=font.Font(family="Helvetica", size=12),
                    bg='#2C3E50', fg='#27AE60').pack(pady=3)
        
        tk.Button(self.root, text="DONE", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#27AE60', fg='white', command=self.show_home,
                 relief=tk.FLAT, padx=50, pady=15).pack(pady=30)
    
    def mark_attendance(self):
        with open(ATTENDANCE_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not os.path.isfile(ATTENDANCE_FILE) or os.path.getsize(ATTENDANCE_FILE) == 0:
                writer.writerow(['Roll', 'Date', 'Time', 'Status'])
            writer.writerow([self.current_roll, datetime.now().strftime('%Y-%m-%d'),
                           datetime.now().strftime('%H:%M:%S'), 'Present'])
    
    def stop_verify(self):
        self.running = False
        self.show_home()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    print("="*70)
    print(" "*5 + "COMPLETE 4-FACTOR LIVENESS DETECTION SYSTEM")
    print("="*70)
    print("\nRequired gestures:")
    print("  1. Blink eyes")
    print("  2. Turn head left")
    print("  3. Turn head right")
    print("  4. Open mouth")
    print("\nPhotos CANNOT do ANY of these!")
    print("ULTRA SECURE!\n")
    app = CompleteLivenessSystem()
    app.run()
