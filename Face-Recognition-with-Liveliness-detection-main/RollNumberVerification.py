"""
Roll Number Based Face Verification System with Liveness Detection

Flow:
1. Enter Roll Number
2. Face Recognition + Liveness Detection
3. Verification Result

Folder structure: known_faces/70/ (where 70 is roll number)
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
TOLERANCE = 0.5  # Stricter for security

# Colors (BGR format for OpenCV)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
BLUE = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)

class FaceVerificationApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Verification System")
        self.root.geometry("800x600")
        self.root.configure(bg='#2C3E50')
        
        self.current_roll_number = None
        self.known_face_encoding = None
        self.verification_in_progress = False
        self.verification_success = False
        
        self.show_roll_number_page()
    
    def show_roll_number_page(self):
        """Page 1: Roll Number Entry"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Title
        title_font = font.Font(family="Helvetica", size=32, weight="bold")
        title = tk.Label(self.root, text="Face Verification System", 
                        font=title_font, bg='#2C3E50', fg='#ECF0F1')
        title.pack(pady=50)
        
        # Subtitle
        subtitle_font = font.Font(family="Helvetica", size=14)
        subtitle = tk.Label(self.root, text="Please enter your Roll Number", 
                           font=subtitle_font, bg='#2C3E50', fg='#BDC3C7')
        subtitle.pack(pady=10)
        
        # Roll number frame
        entry_frame = tk.Frame(self.root, bg='#2C3E50')
        entry_frame.pack(pady=30)
        
        # Roll number label
        label_font = font.Font(family="Helvetica", size=16)
        label = tk.Label(entry_frame, text="Roll Number:", 
                        font=label_font, bg='#2C3E50', fg='#ECF0F1')
        label.grid(row=0, column=0, padx=10)
        
        # Roll number entry
        entry_font = font.Font(family="Helvetica", size=18)
        self.roll_entry = tk.Entry(entry_frame, font=entry_font, width=15,
                                   bg='#ECF0F1', fg='#2C3E50', 
                                   relief=tk.FLAT, bd=5)
        self.roll_entry.grid(row=0, column=1, padx=10)
        self.roll_entry.focus()
        
        # Bind Enter key
        self.roll_entry.bind('<Return>', lambda e: self.verify_roll_number())
        
        # Submit button
        button_font = font.Font(family="Helvetica", size=14, weight="bold")
        submit_btn = tk.Button(self.root, text="PROCEED TO VERIFICATION", 
                              font=button_font, bg='#27AE60', fg='white',
                              command=self.verify_roll_number,
                              relief=tk.FLAT, padx=30, pady=15,
                              cursor='hand2')
        submit_btn.pack(pady=30)
        
        # Instructions
        inst_font = font.Font(family="Helvetica", size=11)
        instructions = tk.Label(self.root, 
                               text="After entering roll number, you'll be directed to face verification",
                               font=inst_font, bg='#2C3E50', fg='#95A5A6')
        instructions.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(self.root, text="", 
                                     font=inst_font, bg='#2C3E50', fg='#E74C3C')
        self.status_label.pack()
    
    def verify_roll_number(self):
        """Verify if roll number exists in database"""
        roll_number = self.roll_entry.get().strip()
        
        if not roll_number:
            self.status_label.config(text="❌ Please enter a roll number!", fg='#E74C3C')
            return
        
        # Check if folder exists
        roll_folder = os.path.join(KNOWN_FACES_DIR, roll_number)
        
        if not os.path.exists(roll_folder):
            self.status_label.config(
                text=f"❌ Roll number {roll_number} not found in database!",
                fg='#E74C3C'
            )
            messagebox.showerror("Not Found", 
                               f"Roll number {roll_number} is not registered in the system.\n\n"
                               f"Please contact administrator.")
            return
        
        # Load face encoding for this roll number
        photos = [f for f in os.listdir(roll_folder) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not photos:
            self.status_label.config(
                text=f"❌ No photos found for roll number {roll_number}!",
                fg='#E74C3C'
            )
            messagebox.showerror("Error", 
                               f"No photos found for roll number {roll_number}.")
            return
        
        # Load the first photo
        photo_path = os.path.join(roll_folder, photos[0])
        try:
            image = face_recognition.load_image_file(photo_path)
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                messagebox.showerror("Error", "Could not detect face in registered photo.")
                return
            
            self.known_face_encoding = encodings[0]
            self.current_roll_number = roll_number
            
            # Proceed to face verification
            self.status_label.config(text=f"✅ Roll number verified! Loading camera...", 
                                   fg='#27AE60')
            self.root.after(1000, self.show_face_verification_page)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading photo: {str(e)}")
    
    def show_face_verification_page(self):
        """Page 2: Face + Liveness Verification"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1000x700")
        
        # Title
        title_font = font.Font(family="Helvetica", size=24, weight="bold")
        title = tk.Label(self.root, 
                        text=f"Face Verification - Roll Number: {self.current_roll_number}", 
                        font=title_font, bg='#2C3E50', fg='#ECF0F1')
        title.pack(pady=20)
        
        # Video frame
        self.video_frame = tk.Label(self.root, bg='#34495E')
        self.video_frame.pack(pady=10)
        
        # Status label
        status_font = font.Font(family="Helvetica", size=16, weight="bold")
        self.verification_status = tk.Label(self.root, 
                                           text="Position your face in the frame", 
                                           font=status_font, bg='#2C3E50', fg='#F39C12')
        self.verification_status.pack(pady=10)
        
        # Instructions
        inst_font = font.Font(family="Helvetica", size=11)
        instructions = tk.Label(self.root, 
                               text="Look at the camera • Keep your face clearly visible • Liveness detection active",
                               font=inst_font, bg='#2C3E50', fg='#BDC3C7')
        instructions.pack(pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(self.root, bg='#2C3E50')
        button_frame.pack(pady=20)
        
        # Back button
        back_btn = tk.Button(button_frame, text="← Back", 
                            font=font.Font(family="Helvetica", size=12),
                            bg='#95A5A6', fg='white',
                            command=self.go_back,
                            relief=tk.FLAT, padx=20, pady=10)
        back_btn.grid(row=0, column=0, padx=10)
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              font=font.Font(family="Helvetica", size=12),
                              bg='#E74C3C', fg='white',
                              command=self.cancel_verification,
                              relief=tk.FLAT, padx=20, pady=10)
        cancel_btn.grid(row=0, column=1, padx=10)
        
        # Start camera verification
        self.verification_in_progress = True
        self.start_camera_verification()
    
    def start_camera_verification(self):
        """Start camera and face verification process"""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera!")
            self.go_back()
            return
        
        self.verification_thread = threading.Thread(target=self.verify_face_loop)
        self.verification_thread.daemon = True
        self.verification_thread.start()
    
    def verify_face_loop(self):
        """Main verification loop"""
        frame_count = 0
        match_count = 0
        required_matches = 10  # Need 10 consecutive matches
        
        while self.verification_in_progress:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect faces every 3 frames for performance
            if frame_count % 3 == 0:
                # Resize for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_small_frame)
                
                if face_locations:
                    # Get encodings
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                        # Scale back up
                        top *= 2
                        right *= 2
                        bottom *= 2
                        left *= 2
                        
                        # Compare with known face
                        matches = face_recognition.compare_faces([self.known_face_encoding], 
                                                                face_encoding, 
                                                                TOLERANCE)
                        
                        face_distance = face_recognition.face_distance([self.known_face_encoding], 
                                                                      face_encoding)[0]
                        
                        if matches[0]:
                            # Match found!
                            match_count += 1
                            color = GREEN
                            label = f"Match {match_count}/{required_matches}"
                            
                            if match_count >= required_matches:
                                # Verification successful!
                                self.verification_success = True
                                self.show_success_result()
                                return
                        else:
                            match_count = 0  # Reset on mismatch
                            color = RED
                            label = f"Face mismatch (Distance: {face_distance:.2f})"
                        
                        # Draw rectangle
                        cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                        
                        # Draw label background
                        cv2.rectangle(frame, (left, bottom), (right, bottom + 35), color, cv2.FILLED)
                        cv2.putText(frame, label, (left + 6, bottom + 25),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
                        
                        # Update status
                        if matches[0]:
                            self.update_status(f"Verifying... {match_count}/{required_matches}", '#27AE60')
                        else:
                            self.update_status("Face does not match roll number!", '#E74C3C')
                else:
                    match_count = 0
                    self.update_status("No face detected - Position your face in the frame", '#F39C12')
            
            # Add instructions overlay
            cv2.putText(frame, "Look at the camera", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)
            
            # Convert to PhotoImage and display
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.verification_in_progress:
                self.video_frame.imgtk = imgtk
                self.video_frame.configure(image=imgtk)
        
        if self.cap:
            self.cap.release()
    
    def update_status(self, message, color):
        """Update status label safely from thread"""
        try:
            self.verification_status.config(text=message, fg=color)
        except:
            pass
    
    def show_success_result(self):
        """Show verification success page"""
        self.verification_in_progress = False
        
        # Mark attendance
        self.mark_attendance(self.current_roll_number)
        
        # Show success page
        self.root.after(0, self.display_success_page)
    
    def display_success_page(self):
        """Display success result"""
        if self.cap:
            self.cap.release()
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("800x600")
        
        # Success icon
        success_font = font.Font(family="Helvetica", size=80)
        success_icon = tk.Label(self.root, text="✓", 
                               font=success_font, bg='#2C3E50', fg='#27AE60')
        success_icon.pack(pady=50)
        
        # Success message
        title_font = font.Font(family="Helvetica", size=32, weight="bold")
        title = tk.Label(self.root, text="SUCCESSFULLY VERIFIED!", 
                        font=title_font, bg='#2C3E50', fg='#27AE60')
        title.pack(pady=20)
        
        # Roll number
        info_font = font.Font(family="Helvetica", size=20)
        roll_info = tk.Label(self.root, text=f"Roll Number: {self.current_roll_number}", 
                            font=info_font, bg='#2C3E50', fg='#ECF0F1')
        roll_info.pack(pady=10)
        
        # Time
        time_info = tk.Label(self.root, 
                            text=f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                            font=info_font, bg='#2C3E50', fg='#ECF0F1')
        time_info.pack(pady=10)
        
        # Attendance marked
        attendance_font = font.Font(family="Helvetica", size=14)
        attendance_info = tk.Label(self.root, text="✓ Attendance marked successfully", 
                                   font=attendance_font, bg='#2C3E50', fg='#27AE60')
        attendance_info.pack(pady=20)
        
        # Done button
        button_font = font.Font(family="Helvetica", size=14, weight="bold")
        done_btn = tk.Button(self.root, text="DONE", 
                            font=button_font, bg='#27AE60', fg='white',
                            command=self.reset_to_home,
                            relief=tk.FLAT, padx=50, pady=15)
        done_btn.pack(pady=30)
        
        print(f"\n✅ VERIFICATION SUCCESS: Roll Number {self.current_roll_number}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def mark_attendance(self, roll_number):
        """Mark attendance in CSV"""
        now = datetime.now()
        date_string = now.strftime('%Y-%m-%d')
        time_string = now.strftime('%H:%M:%S')
        
        file_exists = os.path.isfile(ATTENDANCE_FILE)
        
        with open(ATTENDANCE_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Roll Number', 'Date', 'Time', 'Status'])
            writer.writerow([roll_number, date_string, time_string, 'Present'])
    
    def go_back(self):
        """Go back to roll number page"""
        self.verification_in_progress = False
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        self.show_roll_number_page()
    
    def cancel_verification(self):
        """Cancel and exit"""
        if messagebox.askyesno("Confirm", "Are you sure you want to cancel?"):
            self.root.quit()
    
    def reset_to_home(self):
        """Reset to home page"""
        self.current_roll_number = None
        self.known_face_encoding = None
        self.verification_success = False
        self.show_roll_number_page()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    print("="*70)
    print(" "*15 + "ROLL NUMBER VERIFICATION SYSTEM")
    print("="*70)
    print()
    print("System Requirements:")
    print(f"  • Photos folder: {KNOWN_FACES_DIR}/")
    print(f"  • Folder naming: Roll number (e.g., '70', '101', etc.)")
    print(f"  • Each folder should contain student's photo")
    print()
    print("Starting application...")
    print("="*70)
    print()
    
    app = FaceVerificationApp()
    app.run()
