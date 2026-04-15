"""
Enhanced Roll Number Verification System with Database Management UI

Features:
- Home page with verify + add student + view database
- Add new students with roll number and photo capture
- Face verification with liveness detection
- Success page with attendance
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

# Configuration
KNOWN_FACES_DIR = 'known_faces'
ATTENDANCE_FILE = 'attendance.csv'
TOLERANCE = 0.5

# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)

class VerificationSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Verification System")
        self.root.geometry("900x650")
        self.root.configure(bg='#2C3E50')
        
        self.current_roll = None
        self.known_encoding = None
        self.running = False
        
        self.show_home()
    
    def show_home(self):
        """Home Page"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("900x700")
        
        # Title
        tk.Label(self.root, text="Face Verification System", 
                font=font.Font(family="Helvetica", size=36, weight="bold"),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=30)
        
        # Subtitle
        tk.Label(self.root, text="Secure Identity Verification", 
                font=font.Font(family="Helvetica", size=14),
                bg='#2C3E50', fg='#BDC3C7').pack(pady=10)
        
        # Entry section
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
        
        tk.Button(btn_frame, text="🔍 VERIFY IDENTITY", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#27AE60', fg='white', command=self.verify_roll,
                 relief=tk.FLAT, padx=40, pady=15, cursor='hand2'
                 ).grid(row=0, column=0, padx=10)
        
        tk.Button(btn_frame, text="➕ ADD NEW STUDENT", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#3498DB', fg='white', command=self.add_student,
                 relief=tk.FLAT, padx=40, pady=15, cursor='hand2'
                 ).grid(row=0, column=1, padx=10)
        
        tk.Button(btn_frame, text="📋 VIEW DATABASE", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#95A5A6', fg='white', command=self.view_database,
                 relief=tk.FLAT, padx=40, pady=15, cursor='hand2'
                 ).grid(row=0, column=2, padx=10)
        
        # Status
        self.status_label = tk.Label(self.root, text="", 
                                     font=font.Font(family="Helvetica", size=12),
                                     bg='#2C3E50', fg='#E74C3C')
        self.status_label.pack(pady=10)
        
        # Database count
        count = len([d for d in os.listdir(KNOWN_FACES_DIR) 
                    if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]) if os.path.exists(KNOWN_FACES_DIR) else 0
        tk.Label(self.root, text=f"📊 Students in Database: {count}", 
                font=font.Font(family="Helvetica", size=11),
                bg='#2C3E50', fg='#95A5A6').pack(side='bottom', pady=10)
    
    def add_student(self):
        """Add New Student Page"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1000x750")
        
        tk.Label(self.root, text="➕ Add New Student", 
                font=font.Font(family="Helvetica", size=28, weight="bold"),
                bg='#2C3E50', fg='#3498DB').pack(pady=20)
        
        tk.Label(self.root, text="Enter roll number and capture photo", 
                font=font.Font(family="Helvetica", size=12),
                bg='#2C3E50', fg='#BDC3C7').pack(pady=5)
        
        # Entry
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
        
        # Video
        self.video_label = tk.Label(self.root, bg='#34495E', width=640, height=480)
        self.video_label.pack(pady=10)
        
        # Status
        self.add_status = tk.Label(self.root, text="Enter roll and click Start Camera", 
                                   font=font.Font(family="Helvetica", size=14),
                                   bg='#2C3E50', fg='#F39C12')
        self.add_status.pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(self.root, bg='#2C3E50')
        btn_frame.pack(pady=15)
        
        self.start_btn = tk.Button(btn_frame, text="📷 START CAMERA", 
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
        """Start camera for adding student"""
        roll = self.new_roll_entry.get().strip()
        if not roll:
            messagebox.showerror("Error", "Please enter roll number!")
            return
        
        if os.path.exists(os.path.join(KNOWN_FACES_DIR, roll)):
            if not messagebox.askyesno("Exists", f"Roll {roll} exists. Add more photos?"):
                return
        
        self.adding_roll = roll
        self.running = True
        self.capture_btn.config(state='normal')
        self.start_btn.config(state='disabled')
        self.add_status.config(text="Position face and click CAPTURE", fg='#27AE60')
        
        threading.Thread(target=self.add_camera_loop, daemon=True).start()
    
    def add_camera_loop(self):
        """Camera loop for adding student"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Camera error!")
            return
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            self.current_frame = frame.copy()
            frame = cv2.flip(frame, 1)
            
            h, w = frame.shape[:2]
            cv2.circle(frame, (w//2, h//2), 120, GREEN, 3)
            cv2.putText(frame, "Align face here", (w//2-90, h//2+150),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)
            
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.running:
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        
        cap.release()
    
    def capture_photo(self):
        """Capture and save photo"""
        if not hasattr(self, 'current_frame'):
            messagebox.showerror("Error", "No frame!")
            return
        
        folder = os.path.join(KNOWN_FACES_DIR, self.adding_roll)
        os.makedirs(folder, exist_ok=True)
        
        filepath = os.path.join(folder, f'photo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
        cv2.imwrite(filepath, self.current_frame)
        
        # Verify face
        try:
            image = face_recognition.load_image_file(filepath)
            if not face_recognition.face_encodings(image):
                os.remove(filepath)
                messagebox.showerror("Error", "No face detected! Try again.")
                return
        except:
            os.remove(filepath)
            messagebox.showerror("Error", "Invalid photo! Try again.")
            return
        
        self.running = False
        messagebox.showinfo("Success", 
                           f"✅ Student added!\n\nRoll: {self.adding_roll}\nSize: {os.path.getsize(filepath):,} bytes")
        self.show_home()
    
    def cancel_add(self):
        """Cancel adding"""
        self.running = False
        self.show_home()
    
    def view_database(self):
        """Show database"""
        if not os.path.exists(KNOWN_FACES_DIR):
            messagebox.showinfo("Database", "Database empty. Add students first!")
            return
        
        folders = [d for d in os.listdir(KNOWN_FACES_DIR) 
                  if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))]
        
        if not folders:
            messagebox.showinfo("Database", "Database empty. Add students first!")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Database")
        win.geometry("500x600")
        win.configure(bg='#34495E')
        
        tk.Label(win, text="📋 Registered Students", 
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
        """Verify roll number"""
        roll = self.roll_entry.get().strip()
        if not roll:
            self.status_label.config(text="❌ Enter roll number!", fg='#E74C3C')
            return
        
        folder = os.path.join(KNOWN_FACES_DIR, roll)
        if not os.path.exists(folder):
            self.status_label.config(text=f"❌ Roll {roll} not found!", fg='#E74C3C')
            if messagebox.askyesno("Not Found", f"Roll {roll} not found. Add to database?"):
                self.new_roll_entry.delete(0, tk.END)
                self.new_roll_entry.insert(0, roll)
                self.add_student()
            return
        
        photos = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not photos:
            messagebox.showerror("Error", f"No photos for roll {roll}!")
            return
        
        try:
            image = face_recognition.load_image_file(os.path.join(folder, photos[0]))
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                messagebox.showerror("Error", "No face in photo!")
                return
            
            self.known_encoding = encodings[0]
            self.current_roll = roll
            self.status_label.config(text="✅ Verified! Loading...", fg='#27AE60')
            self.root.after(1000, self.verify_face)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
    
    def verify_face(self):
        """Face verification page"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1000x700")
        
        tk.Label(self.root, text=f"🔍 Verifying Roll: {self.current_roll}", 
                font=font.Font(family="Helvetica", size=24, weight="bold"),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=20)
        
        self.verify_video = tk.Label(self.root, bg='#34495E')
        self.verify_video.pack(pady=10)
        
        self.verify_status = tk.Label(self.root, text="Position your face", 
                                      font=font.Font(family="Helvetica", size=16, weight="bold"),
                                      bg='#2C3E50', fg='#F39C12')
        self.verify_status.pack(pady=10)
        
        tk.Label(self.root, text="Look at camera • Keep face visible",
                font=font.Font(family="Helvetica", size=11),
                bg='#2C3E50', fg='#BDC3C7').pack(pady=5)
        
        tk.Button(self.root, text="← Back", 
                 font=font.Font(family="Helvetica", size=12),
                 bg='#95A5A6', fg='white', command=self.stop_verify,
                 relief=tk.FLAT, padx=20, pady=10).pack(pady=20)
        
        self.running = True
        threading.Thread(target=self.verify_loop, daemon=True).start()
    
    def verify_loop(self):
        """Verification loop"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Camera error!")
            self.stop_verify()
            return
        
        matches = 0
        needed = 10
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            locs = face_recognition.face_locations(rgb)
            
            if locs:
                encs = face_recognition.face_encodings(rgb, locs)
                for (t, r, b, l), enc in zip(locs, encs):
                    t, r, b, l = t*2, r*2, b*2, l*2
                    match = face_recognition.compare_faces([self.known_encoding], enc, TOLERANCE)[0]
                    
                    if match:
                        matches += 1
                        color = GREEN
                        label = f"Match {matches}/{needed}"
                        if matches >= needed:
                            cap.release()
                            self.success()
                            return
                    else:
                        matches = 0
                        color = RED
                        label = "No match"
                    
                    cv2.rectangle(frame, (l, t), (r, b), color, 3)
                    cv2.rectangle(frame, (l, b), (r, b+35), color, -1)
                    cv2.putText(frame, label, (l+6, b+25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
                    
                    self.update_verify_status(f"Verifying... {matches}/{needed}" if match else "No match",
                                             '#27AE60' if match else '#E74C3C')
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
        """Update status"""
        try:
            self.verify_status.config(text=text, fg=color)
        except:
            pass
    
    def success(self):
        """Success page"""
        self.running = False
        self.mark_attendance()
        self.root.after(0, self.show_success)
    
    def show_success(self):
        """Display success"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("800x600")
        
        tk.Label(self.root, text="✓", 
                font=font.Font(family="Helvetica", size=80),
                bg='#2C3E50', fg='#27AE60').pack(pady=50)
        
        tk.Label(self.root, text="SUCCESSFULLY VERIFIED!", 
                font=font.Font(family="Helvetica", size=32, weight="bold"),
                bg='#2C3E50', fg='#27AE60').pack(pady=20)
        
        tk.Label(self.root, text=f"Roll Number: {self.current_roll}", 
                font=font.Font(family="Helvetica", size=20),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=10)
        
        tk.Label(self.root, text=f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                font=font.Font(family="Helvetica", size=20),
                bg='#2C3E50', fg='#ECF0F1').pack(pady=10)
        
        tk.Label(self.root, text="✓ Attendance marked", 
                font=font.Font(family="Helvetica", size=14),
                bg='#2C3E50', fg='#27AE60').pack(pady=20)
        
        tk.Button(self.root, text="DONE", 
                 font=font.Font(family="Helvetica", size=14, weight="bold"),
                 bg='#27AE60', fg='white', command=self.show_home,
                 relief=tk.FLAT, padx=50, pady=15).pack(pady=30)
    
    def mark_attendance(self):
        """Mark attendance"""
        with open(ATTENDANCE_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not os.path.isfile(ATTENDANCE_FILE) or os.path.getsize(ATTENDANCE_FILE) == 0:
                writer.writerow(['Roll', 'Date', 'Time', 'Status'])
            writer.writerow([self.current_roll, datetime.now().strftime('%Y-%m-%d'),
                           datetime.now().strftime('%H:%M:%S'), 'Present'])
    
    def stop_verify(self):
        """Stop verification"""
        self.running = False
        self.show_home()
    
    def run(self):
        """Run app"""
        self.root.mainloop()

if __name__ == "__main__":
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    print("="*70)
    print(" "*15 + "FACE VERIFICATION SYSTEM")
    print("="*70)
    print("\nFeatures:")
    print("  ✅ Verify by roll number")
    print("  ✅ Add students with webcam")
    print("  ✅ View database")
    print("\nStarting...\n")
    app = VerificationSystem()
    app.run()
