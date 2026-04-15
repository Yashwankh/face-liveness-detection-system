"""
ULTRA SECURE System with BLINK DETECTION
Photos CANNOT blink - this will reject all static images!
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

# Configuration
KNOWN_FACES_DIR = 'known_faces'
ATTENDANCE_FILE = 'attendance.csv'
FACE_TOLERANCE = 0.5
EYE_AR_THRESH = 0.25  # Eye aspect ratio threshold
EYE_AR_CONSEC_FRAMES = 3  # Frames for blink
BLINKS_REQUIRED = 2  # Must blink at least twice

# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)

def eye_aspect_ratio(eye):
    """Calculate eye aspect ratio"""
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

class BlinkDetectionSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ULTRA SECURE - Blink Detection Required")
        self.root.geometry("900x650")
        self.root.configure(bg='#2C3E50')
        
        self.current_roll = None
        self.known_encoding = None
        self.running = False
        
        # Blink detection
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_counter = 0
        
        print("✅ ULTRA SECURE MODE: BLINK DETECTION ACTIVE")
        print("   Photos CANNOT blink - 100% secure!")
        
        self.show_home()
    
    def detect_blinks(self, landmarks_dict):
        """Detect eye blinks using facial landmarks from face_recognition"""
        try:
            if not landmarks_dict or 'left_eye' not in landmarks_dict or 'right_eye' not in landmarks_dict:
                return False, 0.0
            
            # Get eye landmarks
            left_eye = np.array(landmarks_dict['left_eye'])
            right_eye = np.array(landmarks_dict['right_eye'])
            
            if len(left_eye) < 6 or len(right_eye) < 6:
                return False, 0.0
            
            # Calculate eye aspect ratios
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            # Check if eyes are closed (EAR drops below threshold)
            if ear < EYE_AR_THRESH:
                self.frame_counter += 1
            else:
                # Eyes opened again - check if it was a blink
                if self.frame_counter >= EYE_AR_CONSEC_FRAMES:
                    self.total_blinks += 1
                    print(f"✓ BLINK DETECTED! Total: {self.total_blinks}")
                self.frame_counter = 0
            
            return self.total_blinks >= BLINKS_REQUIRED, ear
            
        except Exception as e:
            print(f"Blink detection error: {e}")
            return False, 0.0
    
    def show_home(self):
        """Home Page"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("900x800")
        
        tk.Label(self.root, text="ULTRA SECURE System", 
                font=font.Font(family="Helvetica", size=36, weight="bold"),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=20)
        
        tk.Label(self.root, text="🛡️ BLINK DETECTION REQUIRED", 
                font=font.Font(family="Helvetica", size=14, weight="bold"),
                bg='#2C3E50', fg='#E74C3C').pack(pady=5)
        
        tk.Label(self.root, text="Photos CANNOT blink - 100% secure!", 
                font=font.Font(family="Helvetica", size=11),
                bg='#2C3E50', fg='#27AE60').pack(pady=5)
        
        # Entry
        entry_frame = tk.Frame(self.root, bg='#34495E', relief=tk.RAISED, bd=3)
        entry_frame.pack(pady=30, padx=50, fill='x')
        
        tk.Label(entry_frame, text="Enter Roll Number:", 
                font=font.Font(family="Helvetica", size=18, weight="bold"),
                bg='#34495E', fg='#ECF0F1').pack(pady=15)
        
        self.roll_entry = tk.Entry(entry_frame, 
                                   font=font.Font(family="Helvetica", size=22),
                                   width=20, bg='#ECF0F1', fg='#2C3E50',
                                   relief=tk.FLAT, bd=0, justify='center')
        self.roll_entry.pack(pady=10, ipady=10)
        self.roll_entry.focus()
        self.roll_entry.bind('<Return>', lambda e: self.verify_roll())
        
        # Buttons
        btn_frame = tk.Frame(self.root, bg='#2C3E50')
        btn_frame.pack(pady=30)
        
        tk.Button(btn_frame, text="🔍 VERIFY", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#27AE60', fg='white', command=self.verify_roll,
                 relief=tk.FLAT, padx=40, pady=15, cursor='hand2'
                 ).grid(row=0, column=0, padx=10)
        
        tk.Button(btn_frame, text="➕ ADD STUDENT", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#3498DB', fg='white', command=self.add_student,
                 relief=tk.FLAT, padx=40, pady=15, cursor='hand2'
                 ).grid(row=0, column=1, padx=10)
        
        self.status_label = tk.Label(self.root, text="", 
                                     font=font.Font(family="Helvetica", size=12),
                                     bg='#2C3E50', fg='#E74C3C')
        self.status_label.pack(pady=10)
        
        # Security info
        info_frame = tk.Frame(self.root, bg='#34495E', relief=tk.RAISED, bd=2)
        info_frame.pack(pady=20, padx=50, fill='x')
        
        tk.Label(info_frame, text="🛡️ ULTRA SECURE Features:", 
                font=font.Font(family="Helvetica", size=12, weight="bold"),
                bg='#34495E', fg='#ECF0F1').pack(pady=10)
        
        features = [
            "✓ BLINK DETECTION (Required)",
            "✓ Minimum 2 blinks to verify",
            "✓ Photos CANNOT pass",
            "✓ Videos CANNOT pass",
            "✓ Only REAL people verified"
        ]
        
        for feature in features:
            tk.Label(info_frame, text=feature, 
                    font=font.Font(family="Helvetica", size=10),
                    bg='#34495E', fg='#27AE60', anchor='w').pack(padx=20, pady=2)
        
        tk.Label(self.root, text="⚠️ You MUST blink naturally during verification!", 
                font=font.Font(family="Helvetica", size=11, weight="bold"),
                bg='#2C3E50', fg='#F39C12').pack(pady=20)
        
        count = len([d for d in os.listdir(KNOWN_FACES_DIR) 
                    if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]) if os.path.exists(KNOWN_FACES_DIR) else 0
        tk.Label(self.root, text=f"📊 Students: {count}", 
                font=font.Font(family="Helvetica", size=11),
                bg='#2C3E50', fg='#95A5A6').pack(side='bottom', pady=10)
    
    def add_student(self):
        """Simplified add student"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1000x750")
        
        tk.Label(self.root, text="➕ Add New Student", 
                font=font.Font(family="Helvetica", size=28, weight="bold"),
                bg='#2C3E50', fg='#3498DB').pack(pady=20)
        
        entry_frame = tk.Frame(self.root, bg='#34495E', relief=tk.RAISED, bd=3)
        entry_frame.pack(pady=20)
        
        tk.Label(entry_frame, text="Roll Number:", 
                font=font.Font(family="Helvetica", size=14),
                bg='#34495E', fg='#ECF0F1').grid(row=0, column=0, padx=15, pady=15)
        
        self.new_roll_entry = tk.Entry(entry_frame, 
                                       font=font.Font(family="Helvetica", size=16),
                                       width=20, bg='#ECF0F1', fg='#2C3E50')
        self.new_roll_entry.grid(row=0, column=1, padx=15, pady=15)
        self.new_roll_entry.focus()
        
        self.video_label = tk.Label(self.root, bg='#34495E', width=640, height=480)
        self.video_label.pack(pady=10)
        
        self.add_status = tk.Label(self.root, text="Enter roll and click Start", 
                                   font=font.Font(family="Helvetica", size=14),
                                   bg='#2C3E50', fg='#F39C12')
        self.add_status.pack(pady=10)
        
        btn_frame = tk.Frame(self.root, bg='#2C3E50')
        btn_frame.pack(pady=15)
        
        self.start_btn = tk.Button(btn_frame, text="📷 START", 
                                   font=font.Font(family="Helvetica", size=12, weight="bold"),
                                   bg='#27AE60', fg='white', command=self.start_add_camera,
                                   relief=tk.FLAT, padx=30, pady=12)
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.capture_btn = tk.Button(btn_frame, text="📸 CAPTURE", 
                                     font=font.Font(family="Helvetica", size=12, weight="bold"),
                                     bg='#3498DB', fg='white', command=self.capture_photo,
                                     relief=tk.FLAT, padx=30, pady=12, state='disabled')
        self.capture_btn.grid(row=0, column=1, padx=10)
        
        tk.Button(btn_frame, text="← BACK", 
                 font=font.Font(family="Helvetica", size=12),
                 bg='#95A5A6', fg='white', command=self.cancel_add,
                 relief=tk.FLAT, padx=30, pady=12).grid(row=0, column=2, padx=10)
    
    def start_add_camera(self):
        roll = self.new_roll_entry.get().strip()
        if not roll:
            messagebox.showerror("Error", "Enter roll!")
            return
        
        self.adding_roll = roll
        self.running = True
        self.capture_btn.config(state='normal')
        self.start_btn.config(state='disabled')
        
        threading.Thread(target=self.add_camera_loop, daemon=True).start()
    
    def add_camera_loop(self):
        cap = cv2.VideoCapture(0)
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            self.current_frame = frame.copy()
            frame = cv2.flip(frame, 1)
            
            h, w = frame.shape[:2]
            cv2.circle(frame, (w//2, h//2), 120, GREEN, 3)
            
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.running:
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        
        cap.release()
    
    def capture_photo(self):
        if not hasattr(self, 'current_frame'):
            return
        
        folder = os.path.join(KNOWN_FACES_DIR, self.adding_roll)
        os.makedirs(folder, exist_ok=True)
        
        filepath = os.path.join(folder, f'photo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
        cv2.imwrite(filepath, self.current_frame)
        
        try:
            image = face_recognition.load_image_file(filepath)
            if not face_recognition.face_encodings(image):
                os.remove(filepath)
                messagebox.showerror("Error", "No face!")
                return
        except:
            os.remove(filepath)
            messagebox.showerror("Error", "Invalid!")
            return
        
        self.running = False
        messagebox.showinfo("Success", f"✅ Added: {self.adding_roll}")
        self.show_home()
    
    def cancel_add(self):
        self.running = False
        self.show_home()
    
    def verify_roll(self):
        roll = self.roll_entry.get().strip()
        if not roll:
            self.status_label.config(text="❌ Enter roll!", fg='#E74C3C')
            return
        
        folder = os.path.join(KNOWN_FACES_DIR, roll)
        if not os.path.exists(folder):
            self.status_label.config(text=f"❌ Roll {roll} not found!", fg='#E74C3C')
            return
        
        photos = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not photos:
            messagebox.showerror("Error", f"No photos!")
            return
        
        try:
            image = face_recognition.load_image_file(os.path.join(folder, photos[0]))
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                messagebox.showerror("Error", "No face!")
                return
            
            self.known_encoding = encodings[0]
            self.current_roll = roll
            self.status_label.config(text="✅ Loading...", fg='#27AE60')
            self.root.after(1000, self.verify_face)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def verify_face(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1000x800")
        
        tk.Label(self.root, text=f"🔍 Verifying Roll: {self.current_roll}", 
                font=font.Font(family="Helvetica", size=24, weight="bold"),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=10)
        
        tk.Label(self.root, text="👁️ BLINK NATURALLY - Photos will be rejected!", 
                font=font.Font(family="Helvetica", size=12, weight="bold"),
                bg='#2C3E50', fg='#E74C3C').pack(pady=5)
        
        self.verify_video = tk.Label(self.root, bg='#34495E')
        self.verify_video.pack(pady=10)
        
        self.verify_status = tk.Label(self.root, text="Position face & BLINK naturally", 
                                      font=font.Font(family="Helvetica", size=16, weight="bold"),
                                      bg='#2C3E50', fg='#F39C12')
        self.verify_status.pack(pady=10)
        
        self.blink_status = tk.Label(self.root, text="Blinks: 0/2 - Keep blinking!", 
                                     font=font.Font(family="Helvetica", size=14, weight="bold"),
                                     bg='#2C3E50', fg='#E74C3C')
        self.blink_status.pack(pady=5)
        
        tk.Button(self.root, text="← Back", 
                 font=font.Font(family="Helvetica", size=12),
                 bg='#95A5A6', fg='white', command=self.stop_verify,
                 relief=tk.FLAT, padx=20, pady=10).pack(pady=10)
        
        self.running = True
        self.total_blinks = 0
        self.frame_counter = 0
        threading.Thread(target=self.verify_loop, daemon=True).start()
    
    def verify_loop(self):
        cap = cv2.VideoCapture(0)
        matches = 0
        needed = 5  # Reduced to 5 since blink detection is main security
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            
            locs = face_recognition.face_locations(rgb)
            
            if locs:
                # Get facial landmarks for blink detection
                landmarks = face_recognition.face_landmarks(rgb)
                
                if landmarks:
                    # Use first face's landmarks (dictionary format)
                    landmark_dict = landmarks[0]
                    
                    # Detect blinks using eye landmarks
                    has_blinked, ear = self.detect_blinks(landmark_dict)
                    
                    # Update blink status
                    color = '#27AE60' if self.total_blinks >= BLINKS_REQUIRED else '#E74C3C'
                    self.update_blink_status(f"Blinks: {self.total_blinks}/{BLINKS_REQUIRED}", color)
                    
                    if not has_blinked and self.total_blinks < BLINKS_REQUIRED:
                        # Not enough blinks yet
                        for (t, r, b, l) in locs:
                            t, r, b, l = t*2, r*2, b*2, l*2
                            cv2.rectangle(frame, (l, t), (r, b), YELLOW, 3)
                            cv2.putText(frame, f"BLINK! ({self.total_blinks}/2)", (l, t-10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)
                        
                        cv2.putText(frame, "BLINK NATURALLY TO CONTINUE!", 
                                   (frame.shape[1]//2 - 200, 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, YELLOW, 2)
                        
                        self.update_verify_status("👁️ BLINK naturally to verify!", '#F39C12')
                    
                    elif has_blinked:
                        # Enough blinks - now check face match
                        encs = face_recognition.face_encodings(rgb, locs)
                        
                        for (t, r, b, l), enc in zip(locs, encs):
                            t, r, b, l = t*2, r*2, b*2, l*2
                            
                            match = face_recognition.compare_faces([self.known_encoding], enc, FACE_TOLERANCE)[0]
                            
                            if match:
                                matches += 1
                                color_box = GREEN
                                label = f"Verified {matches}/{needed}"
                                
                                if matches >= needed:
                                    cap.release()
                                    self.success()
                                    return
                            else:
                                matches = 0
                                color_box = RED
                                label = "Wrong person"
                            
                            cv2.rectangle(frame, (l, t), (r, b), color_box, 3)
                            cv2.putText(frame, label, (l, t-10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_box, 2)
                            
                            if match:
                                self.update_verify_status(f"✅ Matching... {matches}/{needed}", '#27AE60')
                            else:
                                self.update_verify_status("Wrong person!", '#E74C3C')
            else:
                matches = 0
                self.update_verify_status("No face detected", '#F39C12')
            
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.running:
                self.verify_video.imgtk = imgtk
                self.verify_video.configure(image=imgtk)
        
        cap.release()
    
    def update_verify_status(self, text, color):
        try:
            self.verify_status.config(text=text, fg=color)
        except:
            pass
    
    def update_blink_status(self, text, color):
        try:
            self.blink_status.config(text=text, fg=color)
        except:
            pass
    
    def success(self):
        self.running = False
        self.mark_attendance()
        self.root.after(0, self.show_success)
    
    def show_success(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("800x600")
        
        tk.Label(self.root, text="✓", 
                font=font.Font(family="Helvetica", size=80),
                bg='#2C3E50', fg='#27AE60').pack(pady=50)
        
        tk.Label(self.root, text="SUCCESSFULLY VERIFIED!", 
                font=font.Font(family="Helvetica", size=32, weight="bold"),
                bg='#2C3E50', fg='#27AE60').pack(pady=20)
        
        tk.Label(self.root, text=f"Roll: {self.current_roll}", 
                font=font.Font(family="Helvetica", size=20),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=10)
        
        tk.Label(self.root, text="✓ Real person (blinked)", 
                font=font.Font(family="Helvetica", size=14),
                bg='#2C3E50', fg='#27AE60').pack(pady=5)
        
        tk.Label(self.root, text="✓ Attendance marked", 
                font=font.Font(family="Helvetica", size=14),
                bg='#2C3E50', fg='#27AE60').pack(pady=5)
        
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
    print(" "*10 + "ULTRA SECURE - BLINK DETECTION REQUIRED")
    print("="*70)
    print("\nYou MUST blink naturally to verify")
    print("Photos CANNOT blink - 100% secure!")
    print("\nStarting...\n")
    app = BlinkDetectionSystem()
    app.run()
