"""
Secure Verification System with WORKING Liveness Detection
Uses texture analysis and motion detection instead of CNN model
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

# Configuration
KNOWN_FACES_DIR = 'known_faces'
ATTENDANCE_FILE = 'attendance.csv'
FACE_TOLERANCE = 0.5

# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)

class WorkingSecureSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Secure Face Verification - Liveness Detection Active")
        self.root.geometry("900x650")
        self.root.configure(bg='#2C3E50')
        
        self.current_roll = None
        self.known_encoding = None
        self.running = False
        self.prev_frame = None
        
        print("✅ Liveness Detection: ACTIVE (Texture + Motion Analysis)")
        
        self.show_home()
    
    def check_liveness_simple(self, face_frame, frame_full):
        """
        STRONG liveness detection - REJECTS mobile phone photos
        """
        try:
            if face_frame is None or face_frame.size == 0:
                return False, 0.0
            
            gray = cv2.cvtColor(face_frame, cv2.COLOR_BGR2GRAY)
            
            # 1. Screen Glare Detection (NEW!) - Mobile screens have bright spots
            bright_pixels = np.sum(gray > 240)
            total_pixels = gray.size
            glare_ratio = bright_pixels / total_pixels
            if glare_ratio > 0.03:  # > 3% very bright = screen
                return False, 0.1
            
            # 2. Texture Analysis - STRICT threshold
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 80:  # Was 100, now stricter
                return False, 0.2
            texture_score = min(laplacian_var / 200.0, 1.0)
            
            # 3. Edge Sharpness - Photos have sharper edges
            edges = cv2.Canny(gray, 50, 150)
            edge_ratio = np.sum(edges > 0) / edges.size
            if edge_ratio > 0.25:  # Too many sharp edges = photo
                return False, 0.15
            edge_score = 1.0 if 0.05 < edge_ratio < 0.20 else 0.3
            
            # 4. Color Temperature - Screens have different colors
            hsv = cv2.cvtColor(face_frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            s_mean = np.mean(s)
            if s_mean < 30 or s_mean > 200:  # Unnatural saturation
                return False, 0.25
            
            # 5. Motion Detection - STRICTER
            motion_score = 0.3  # Default low
            if self.prev_frame is not None:
                try:
                    prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
                    curr_gray = cv2.cvtColor(frame_full, cv2.COLOR_BGR2GRAY)
                    
                    frame_diff = cv2.absdiff(prev_gray, curr_gray)
                    motion_amount = np.sum(frame_diff) / (frame_diff.size * 255)
                    
                    # Real faces: 0.002 - 0.08
                    if 0.002 < motion_amount < 0.08:
                        motion_score = 1.0
                    elif motion_amount < 0.001:  # Too still = photo
                        return False, 0.1
                    else:
                        motion_score = 0.4
                except:
                    motion_score = 0.3
            
            self.prev_frame = frame_full.copy()
            
            # Combined score - STRICTER weights
            confidence = (texture_score * 0.35 + edge_score * 0.25 + motion_score * 0.40)
            
            # STRICT threshold: > 0.70 (was 0.4)
            is_real = confidence > 0.70
            
            return is_real, confidence
            
        except Exception as e:
            return False, 0.0
    
    def show_home(self):
        """Home Page"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("900x750")
        
        tk.Label(self.root, text="Secure Face Verification", 
                font=font.Font(family="Helvetica", size=36, weight="bold"),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=20)
        
        tk.Label(self.root, text="🛡️ Liveness Detection: ACTIVE", 
                font=font.Font(family="Helvetica", size=12, weight="bold"),
                bg='#2C3E50', fg='#27AE60').pack(pady=5)
        
        tk.Label(self.root, text="Texture + Motion Analysis Active", 
                font=font.Font(family="Helvetica", size=10),
                bg='#2C3E50', fg='#BDC3C7').pack(pady=5)
        
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
        
        tk.Button(btn_frame, text="📋 DATABASE", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#95A5A6', fg='white', command=self.view_database,
                 relief=tk.FLAT, padx=40, pady=15, cursor='hand2'
                 ).grid(row=0, column=2, padx=10)
        
        self.status_label = tk.Label(self.root, text="", 
                                     font=font.Font(family="Helvetica", size=12),
                                     bg='#2C3E50', fg='#E74C3C')
        self.status_label.pack(pady=10)
        
        # Security info
        info_frame = tk.Frame(self.root, bg='#34495E', relief=tk.RAISED, bd=2)
        info_frame.pack(pady=20, padx=50, fill='x')
        
        tk.Label(info_frame, text="🛡️ Security Features:", 
                font=font.Font(family="Helvetica", size=12, weight="bold"),
                bg='#34495E', fg='#ECF0F1').pack(pady=10)
        
        features = [
            "✓ Face Recognition (128-D encoding)",
            "✓ Liveness Detection (Texture + Motion)",
            "✓ Multi-frame verification (10 matches)",
            "✓ Photo/Video spoofing prevention"
        ]
        
        for feature in features:
            tk.Label(info_frame, text=feature, 
                    font=font.Font(family="Helvetica", size=10),
                    bg='#34495E', fg='#27AE60', anchor='w').pack(padx=20, pady=2)
        
        info_frame.pack(pady=10)
        
        # Database count
        count = len([d for d in os.listdir(KNOWN_FACES_DIR) 
                    if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]) if os.path.exists(KNOWN_FACES_DIR) else 0
        tk.Label(self.root, text=f"📊 Students: {count}", 
                font=font.Font(family="Helvetica", size=11),
                bg='#2C3E50', fg='#95A5A6').pack(side='bottom', pady=10)
    
    def add_student(self):
        """Add student - same as before"""
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
        self.add_status.config(text="Position face", fg='#27AE60')
        
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
        messagebox.showinfo("Success", f"✅ Added Roll: {self.adding_roll}")
        self.show_home()
    
    def cancel_add(self):
        self.running = False
        self.show_home()
    
    def view_database(self):
        if not os.path.exists(KNOWN_FACES_DIR):
            messagebox.showinfo("Database", "Empty!")
            return
        
        folders = [d for d in os.listdir(KNOWN_FACES_DIR) 
                  if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]
        
        if not folders:
            messagebox.showinfo("Database", "Empty!")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Database")
        win.geometry("500x600")
        win.configure(bg='#34495E')
        
        tk.Label(win, text="📋 Students", 
                font=font.Font(family="Helvetica", size=20, weight="bold"),
                bg='#34495E', fg='#ECF0F1').pack(pady=20)
        
        frame = tk.Frame(win, bg='#34495E')
        frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        for i, roll in enumerate(sorted(folders), 1):
            photos = len([f for f in os.listdir(os.path.join(KNOWN_FACES_DIR, roll))
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            
            box = tk.Frame(frame, bg='#2C3E50', relief=tk.RAISED, bd=2)
            box.pack(fill='x', pady=5)
            
            tk.Label(box, text=f"{i}. Roll: {roll} | Photos: {photos}", 
                    font=font.Font(family="Helvetica", size=12),
                    bg='#2C3E50', fg='#ECF0F1', anchor='w'
                    ).pack(fill='x', padx=10, pady=10)
        
        tk.Button(win, text="Close", command=win.destroy,
                 bg='#E74C3C', fg='white', padx=20, pady=10).pack(pady=10)
    
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
            messagebox.showerror("Error", f"No photos for {roll}!")
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
        
        self.root.geometry("1000x750")
        
        tk.Label(self.root, text=f"🔍 Verifying Roll: {self.current_roll}", 
                font=font.Font(family="Helvetica", size=24, weight="bold"),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=10)
        
        tk.Label(self.root, text="🛡️ Liveness Detection Active", 
                font=font.Font(family="Helvetica", size=11),
                bg='#2C3E50', fg='#27AE60').pack(pady=5)
        
        self.verify_video = tk.Label(self.root, bg='#34495E')
        self.verify_video.pack(pady=10)
        
        self.verify_status = tk.Label(self.root, text="Position face", 
                                      font=font.Font(family="Helvetica", size=16, weight="bold"),
                                      bg='#2C3E50', fg='#F39C12')
        self.verify_status.pack(pady=10)
        
        self.liveness_status = tk.Label(self.root, text="", 
                                        font=font.Font(family="Helvetica", size=12),
                                        bg='#2C3E50', fg='#3498DB')
        self.liveness_status.pack(pady=5)
        
        tk.Button(self.root, text="← Back", 
                 font=font.Font(family="Helvetica", size=12),
                 bg='#95A5A6', fg='white', command=self.stop_verify,
                 relief=tk.FLAT, padx=20, pady=10).pack(pady=10)
        
        self.running = True
        self.prev_frame = None
        threading.Thread(target=self.verify_loop, daemon=True).start()
    
    def verify_loop(self):
        cap = cv2.VideoCapture(0)
        matches = 0
        needed = 10
        frame_count = 0
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            frame = cv2.flip(frame, 1)
            
            if frame_count % 2 == 0:
                small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                locs = face_recognition.face_locations(rgb)
                
                if locs:
                    encs = face_recognition.face_encodings(rgb, locs)
                    
                    for (t, r, b, l), enc in zip(locs, encs):
                        t, r, b, l = t*2, r*2, b*2, l*2
                        face_frame = frame[t:b, l:r]
                        
                        # Check liveness
                        is_real, confidence = self.check_liveness_simple(face_frame, frame)
                        
                        if not is_real:
                            matches = 0
                            color = RED
                            label = "FAKE FACE!"
                            
                            cv2.rectangle(frame, (l, t), (r, b), color, 3)
                            cv2.rectangle(frame, (l, b), (r, b+35), color, -1)
                            cv2.putText(frame, label, (l+6, b+25), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
                            
                            cv2.putText(frame, "SPOOFING DETECTED!", 
                                       (frame.shape[1]//2 - 150, 50),
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 3)
                            
                            self.update_verify_status("❌ FAKE - Photo/Video!", '#E74C3C')
                            self.update_liveness_status(f"Fake (conf: {confidence:.2f})", '#E74C3C')
                            continue
                        
                        # Real face - check match
                        match = face_recognition.compare_faces([self.known_encoding], enc, FACE_TOLERANCE)[0]
                        
                        if match:
                            matches += 1
                            color = GREEN
                            label = f"Real {matches}/{needed}"
                            
                            if matches >= needed:
                                cap.release()
                                self.success()
                                return
                        else:
                            matches = 0
                            color = YELLOW
                            label = "Real but wrong"
                        
                        cv2.rectangle(frame, (l, t), (r, b), color, 3)
                        cv2.rectangle(frame, (l, b), (r, b+35), color, -1)
                        cv2.putText(frame, label, (l+6, b+25), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
                        
                        if match:
                            self.update_verify_status(f"✅ Verifying {matches}/{needed}", '#27AE60')
                            self.update_liveness_status(f"✓ Real (conf: {confidence:.2f})", '#27AE60')
                        else:
                            self.update_verify_status("Wrong person!", '#F39C12')
                            self.update_liveness_status(f"✓ Real wrong person", '#F39C12')
                else:
                    matches = 0
                    self.update_verify_status("No face", '#F39C12')
            
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
    
    def update_liveness_status(self, text, color):
        try:
            self.liveness_status.config(text=text, fg=color)
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
        
        tk.Label(self.root, text=f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                font=font.Font(family="Helvetica", size=20),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=10)
        
        tk.Label(self.root, text="✓ Real person verified", 
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
    print(" "*10 + "SECURE VERIFICATION WITH LIVENESS DETECTION")
    print("="*70)
    print("\nFeatures:")
    print("  ✅ Face Recognition")
    print("  ✅ Liveness Detection (Texture + Motion)")
    print("  ✅ Anti-Spoofing Protection")
    print("\nStarting...\n")
    app = WorkingSecureSystem()
    app.run()
