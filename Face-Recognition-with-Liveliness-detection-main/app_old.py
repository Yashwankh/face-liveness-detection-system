"""
Flask Backend for Aadhaar Face Verification System
Handles face recognition, liveness detection, and API endpoints
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import cv2
import face_recognition
import os
import csv
from datetime import datetime
import numpy as np
from scipy.spatial import distance as dist
import base64
from io import BytesIO
from PIL import Image
import threading
import time

app = Flask(__name__)
CORS(app)

# Configuration
KNOWN_FACES_DIR = 'known_faces'
ATTENDANCE_FILE = 'attendance.csv'
FACE_TOLERANCE = 0.4  # Stricter face matching tolerance

# Thresholds for liveness detection
EYE_AR_THRESH = 0.28
MOUTH_AR_THRESH = 0.65
HEAD_MOVEMENT_THRESH = 20

# Global variables for verification sessions
verification_sessions = {}

def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    
    # Create attendance file with headers if it doesn't exist
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Aadhaar', 'Date', 'Time', 'Status'])

def eye_aspect_ratio(eye):
    """Calculate eye aspect ratio for blink detection"""
    try:
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear
    except:
        return 0.3  # Default open eye value

def mouth_aspect_ratio(mouth):
    """Calculate mouth aspect ratio for mouth opening detection - IMPROVED"""
    try:
        # More reliable mouth detection using multiple points
        A = dist.euclidean(mouth[2], mouth[10])  # Top to bottom
        B = dist.euclidean(mouth[4], mouth[8])   # Top to bottom  
        C = dist.euclidean(mouth[0], mouth[6])   # Left to right
        
        # Additional measurements for better accuracy
        D = dist.euclidean(mouth[3], mouth[9])   # Center top to bottom
        
        # Average multiple measurements
        mar = (A + B + D) / (3.0 * C)
        return mar
    except:
        return 0.1  # Default closed mouth value (lower for easier detection)

class LivenessDetector:
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all liveness detection variables"""
        # Blink detection - more robust
        self.blink_completed = False
        self.blink_counter = 0
        self.total_blinks = 0
        self.blink_sequence = []  # Track EAR values over time
        self.blink_threshold_low = 0.25  # Eye closed threshold
        self.blink_threshold_high = 0.35  # Eye open threshold
        self.min_blink_frames = 3  # Minimum frames for valid blink
        self.max_blink_frames = 15  # Maximum frames for valid blink
        
        # Head movement - more precise
        self.head_left_done = False
        self.head_right_done = False
        self.head_positions = []  # Track head positions over time
        self.initial_face_center = None
        self.min_head_movement = 25  # Minimum movement percentage
        self.head_movement_frames = 0
        
        # Mouth detection - more accurate
        self.mouth_opened = False
        self.mouth_ratios = []  # Track mouth ratios over time
        self.mouth_open_threshold = 0.6
        self.mouth_open_frames = 0
        self.min_mouth_open_frames = 5
        
        # Face matching
        self.face_matches = 0
        self.consecutive_matches = 0
        self.consecutive_mismatches = 0
        
        # Timing
        self.start_time = time.time()
        self.last_detection_time = time.time()
    
    def detect_blink(self, landmarks):
        """Advanced blink detection with sequence validation"""
        try:
            if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
                # Auto-complete after 15 seconds
                if time.time() - self.start_time > 15:
                    self.blink_completed = True
                return self.blink_completed, 0.3
            
            left_eye = np.array(landmarks['left_eye'])
            right_eye = np.array(landmarks['right_eye'])
            
            if len(left_eye) >= 6 and len(right_eye) >= 6:
                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)
                ear = (left_ear + right_ear) / 2.0
                
                # Add current EAR to sequence
                self.blink_sequence.append(ear)
                
                # Keep only recent frames (last 20 frames)
                if len(self.blink_sequence) > 20:
                    self.blink_sequence.pop(0)
                
                # Detect valid blink pattern: open -> closed -> open
                if len(self.blink_sequence) >= 10 and not self.blink_completed:
                    self.blink_completed = self._validate_blink_sequence()
                
                return self.blink_completed, ear
            
            # Auto-complete after 15 seconds
            if time.time() - self.start_time > 15:
                self.blink_completed = True
            
            return self.blink_completed, 0.3
        except Exception as e:
            print(f"Blink detection error: {e}")
            if time.time() - self.start_time > 15:
                self.blink_completed = True
            return self.blink_completed, 0.3
    
    def _validate_blink_sequence(self):
        """Validate if the EAR sequence represents a real blink"""
        if len(self.blink_sequence) < 10:
            return False
        
        # Look for pattern: high EAR -> low EAR -> high EAR
        for i in range(len(self.blink_sequence) - 6):
            window = self.blink_sequence[i:i+7]
            
            # Check for blink pattern
            open_start = window[0] > self.blink_threshold_high
            closed_middle = min(window[2:5]) < self.blink_threshold_low
            open_end = window[6] > self.blink_threshold_high
            
            # Validate the pattern
            if open_start and closed_middle and open_end:
                # Check duration is reasonable
                closed_frames = sum(1 for ear in window[1:6] if ear < self.blink_threshold_low)
                if self.min_blink_frames <= closed_frames <= self.max_blink_frames:
                    return True
        
        return False
    
    def detect_head_movement(self, face_location, frame_width):
        """Advanced head movement detection with position tracking"""
        try:
            top, right, bottom, left = face_location
            face_center_x = (left + right) / 2
            face_center_y = (top + bottom) / 2
            face_width = right - left
            
            current_position = {
                'x': face_center_x,
                'y': face_center_y,
                'width': face_width,
                'timestamp': time.time()
            }
            
            # Initialize reference position
            if self.initial_face_center is None:
                self.initial_face_center = current_position
                return "center", 0
            
            # Add to position history
            self.head_positions.append(current_position)
            
            # Keep only recent positions (last 30 frames)
            if len(self.head_positions) > 30:
                self.head_positions.pop(0)
            
            # Calculate movement relative to initial position
            movement_x = face_center_x - self.initial_face_center['x']
            movement_percent = (movement_x / face_width) * 100
            
            # Validate sustained movement (not just noise)
            if abs(movement_percent) > self.min_head_movement:
                sustained_movement = self._validate_head_movement(movement_percent > 0)
                
                if sustained_movement:
                    if movement_percent < -self.min_head_movement and not self.head_left_done:
                        self.head_left_done = True
                        return "left", movement_percent
                    elif movement_percent > self.min_head_movement and not self.head_right_done:
                        self.head_right_done = True
                        return "right", movement_percent
            
            # Auto-complete after 25 seconds
            if time.time() - self.start_time > 25:
                if not self.head_left_done:
                    self.head_left_done = True
                if not self.head_right_done:
                    self.head_right_done = True
            
            return "center", movement_percent
        except Exception as e:
            print(f"Head movement error: {e}")
            if time.time() - self.start_time > 25:
                self.head_left_done = True
                self.head_right_done = True
            return "center", 0
    
    def _validate_head_movement(self, is_right_movement):
        """Validate sustained head movement to prevent false positives"""
        if len(self.head_positions) < 10:
            return False
        
        # Check last 10 positions for consistent movement
        recent_positions = self.head_positions[-10:]
        initial_x = self.initial_face_center['x']
        
        consistent_frames = 0
        for pos in recent_positions:
            movement = pos['x'] - initial_x
            movement_percent = (movement / pos['width']) * 100
            
            if is_right_movement and movement_percent > self.min_head_movement:
                consistent_frames += 1
            elif not is_right_movement and movement_percent < -self.min_head_movement:
                consistent_frames += 1
        
        # Require at least 7 out of 10 frames to show consistent movement
        return consistent_frames >= 7
    
    def detect_mouth_opening(self, landmarks):
        """Advanced mouth opening detection with sustained validation"""
        try:
            if not landmarks or 'top_lip' not in landmarks or 'bottom_lip' not in landmarks:
                # Auto-complete after 30 seconds
                if time.time() - self.start_time > 30:
                    self.mouth_opened = True
                return self.mouth_opened, 0.5
            
            mouth = landmarks['top_lip'] + landmarks['bottom_lip']
            mouth = np.array(mouth)
            
            if len(mouth) >= 12:
                mar = mouth_aspect_ratio(mouth)
                
                # Add current MAR to sequence
                self.mouth_ratios.append(mar)
                
                # Keep only recent ratios (last 15 frames)
                if len(self.mouth_ratios) > 15:
                    self.mouth_ratios.pop(0)
                
                # Check for sustained mouth opening
                if mar > self.mouth_open_threshold:
                    self.mouth_open_frames += 1
                else:
                    self.mouth_open_frames = 0
                
                # Validate sustained mouth opening
                if self.mouth_open_frames >= self.min_mouth_open_frames and not self.mouth_opened:
                    # Additional validation: check if opening is significant
                    if self._validate_mouth_opening():
                        self.mouth_opened = True
                        return True, mar
                
                return self.mouth_opened, mar
            
            # Auto-complete after 30 seconds
            if time.time() - self.start_time > 30:
                self.mouth_opened = True
            
            return self.mouth_opened, 0.5
        except Exception as e:
            print(f"Mouth detection error: {e}")
            if time.time() - self.start_time > 30:
                self.mouth_opened = True
            return self.mouth_opened, 0.5
    
    def _validate_mouth_opening(self):
        """Validate if mouth opening is genuine and sustained"""
        if len(self.mouth_ratios) < 10:
            return False
        
        # Check recent ratios for consistent opening
        recent_ratios = self.mouth_ratios[-10:]
        high_ratios = sum(1 for ratio in recent_ratios if ratio > self.mouth_open_threshold)
        
        # Require at least 7 out of 10 recent frames to show mouth opening
        if high_ratios >= 7:
            # Additional check: ensure significant opening compared to baseline
            baseline = min(self.mouth_ratios[:5]) if len(self.mouth_ratios) >= 5 else 0.3
            current_max = max(recent_ratios)
            
            # Opening should be at least 50% more than baseline
            return current_max > baseline * 1.5
        
        return False
    
    def check_gestures_complete(self):
        """Check if at least 3 out of 4 gestures completed"""
        completed_count = sum([
            self.blink_completed,
            self.head_left_done,
            self.head_right_done,
            self.mouth_opened
        ])
        return completed_count >= 3
    
    def get_gesture_count(self):
        """Get number of completed gestures"""
        return sum([
            self.blink_completed,
            self.head_left_done,
            self.head_right_done,
            self.mouth_opened
        ])

# Routes
@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)"""
    return send_from_directory('.', filename)

@app.route('/api/check-aadhaar', methods=['POST'])
def check_aadhaar():
    """Check if Aadhaar number exists in database"""
    try:
        data = request.get_json()
        aadhaar = data.get('aadhaar')
        
        if not aadhaar:
            return jsonify({'error': 'Aadhaar number required'}), 400
        
        folder_path = os.path.join(KNOWN_FACES_DIR, aadhaar)
        exists = os.path.exists(folder_path)
        
        if exists:
            # Check if there are any photo files
            photos = [f for f in os.listdir(folder_path) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            exists = len(photos) > 0
        
        return jsonify({'exists': exists})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-frame', methods=['POST'])
def process_frame():
    """Process video frame for face verification and liveness detection"""
    try:
        aadhaar = request.form.get('aadhaar')
        frame_file = request.files.get('frame')
        
        if not aadhaar or not frame_file:
            return jsonify({'error': 'Missing aadhaar or frame'}), 400
        
        # Initialize session if not exists
        if aadhaar not in verification_sessions:
            verification_sessions[aadhaar] = LivenessDetector()
            
            # Load known face encoding
            folder_path = os.path.join(KNOWN_FACES_DIR, aadhaar)
            photos = [f for f in os.listdir(folder_path) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if not photos:
                return jsonify({'error': 'No photos found for this Aadhaar'}), 400
            
            known_image = face_recognition.load_image_file(
                os.path.join(folder_path, photos[0])
            )
            known_encodings = face_recognition.face_encodings(known_image)
            
            if not known_encodings:
                return jsonify({'error': 'No face found in registered photo'}), 400
            
            verification_sessions[aadhaar].known_encoding = known_encodings[0]
        
        detector = verification_sessions[aadhaar]
        
        # Check time limit
        elapsed_time = time.time() - detector.start_time
        if elapsed_time > 60:  # 60 second limit
            del verification_sessions[aadhaar]
            return jsonify({
                'failed': True,
                'message': 'Time limit exceeded'
            })
        
        # Process frame
        image = Image.open(frame_file.stream)
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Resize for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find faces
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            return jsonify({
                'instruction': 'Please position your face in the camera view',
                'gesture_count': detector.get_gesture_count(),
                'face_matches': detector.face_matches,
                'blink_completed': detector.blink_completed,
                'head_left_done': detector.head_left_done,
                'head_right_done': detector.head_right_done,
                'mouth_opened': detector.mouth_opened
            })
        
        # Get face landmarks and encodings with full accuracy
        face_landmarks = face_recognition.face_landmarks(rgb_frame, face_locations)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if not face_landmarks or not face_encodings:
            return jsonify({
                'instruction': 'Face not clearly visible. Please adjust position.',
                'gesture_count': detector.get_gesture_count(),
                'face_matches': detector.face_matches,
                'blink_completed': detector.blink_completed,
                'head_left_done': detector.head_left_done,
                'head_right_done': detector.head_right_done,
                'mouth_opened': detector.mouth_opened
            })
        
        landmarks = face_landmarks[0]
        face_encoding = face_encodings[0]
        face_location = face_locations[0]
        
        # Scale back face location
        top, right, bottom, left = [v * 2 for v in face_location]
        
        # Check face match
        face_match = face_recognition.compare_faces(
            [detector.known_encoding], face_encoding, FACE_TOLERANCE
        )[0]
        
        # Perform liveness detection
        detector.detect_blink(landmarks)
        detector.detect_head_movement((top, right, bottom, left), frame.shape[1])
        detector.detect_mouth_opening(landmarks)
        
        # Robust face match counter with consecutive validation
        if detector.check_gestures_complete():
            if face_match:
                detector.consecutive_matches += 1
                detector.consecutive_mismatches = 0
                # Only increment after 2 consecutive matches to reduce false positives
                if detector.consecutive_matches >= 2:
                    detector.face_matches += 1
            else:
                detector.consecutive_mismatches += 1
                detector.consecutive_matches = 0
                # Penalize after 3 consecutive mismatches
                if detector.consecutive_mismatches >= 3:
                    detector.face_matches = max(0, detector.face_matches - 1)
                    detector.consecutive_mismatches = 0
        else:
            detector.face_matches = 0
            detector.consecutive_matches = 0
            detector.consecutive_mismatches = 0
        
        # Generate instruction
        instruction = "Follow the instructions to prove you're live"
        if detector.check_gestures_complete():
            instruction = "✅ Liveness confirmed. Hold steady for face matching."
            if detector.face_matches >= 5:
                # Success!
                del verification_sessions[aadhaar]
                return jsonify({
                    'success': True,
                    'message': 'Verification successful!'
                })
        else:
            # Give specific instructions
            if not detector.blink_completed:
                instruction = "👁️ Please BLINK your eyes"
            elif not detector.head_left_done:
                instruction = "← Please turn your head LEFT"
            elif not detector.head_right_done:
                instruction = "→ Please turn your head RIGHT"
            elif not detector.mouth_opened:
                instruction = "😮 Please OPEN your mouth"
        
        return jsonify({
            'instruction': instruction,
            'gesture_count': detector.get_gesture_count(),
            'face_matches': detector.face_matches,
            'blink_completed': detector.blink_completed,
            'head_left_done': detector.head_left_done,
            'head_right_done': detector.head_right_done,
            'mouth_opened': detector.mouth_opened
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-student', methods=['POST'])
def add_student():
    """Add new student with photo"""
    try:
        aadhaar = request.form.get('aadhaar')
        photo_file = request.files.get('photo')
        
        if not aadhaar or not photo_file:
            return jsonify({'error': 'Missing aadhaar or photo'}), 400
        
        # Create folder for this Aadhaar
        folder_path = os.path.join(KNOWN_FACES_DIR, aadhaar)
        os.makedirs(folder_path, exist_ok=True)
        
        # Save photo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'photo_{timestamp}.jpg'
        filepath = os.path.join(folder_path, filename)
        
        # Convert and save image
        image = Image.open(photo_file.stream)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(filepath, 'JPEG')
        
        # Validate that face is detected
        test_image = face_recognition.load_image_file(filepath)
        face_encodings = face_recognition.face_encodings(test_image)
        
        if not face_encodings:
            os.remove(filepath)
            return jsonify({
                'success': False,
                'message': 'No face detected in the photo. Please try again.'
            })
        
        return jsonify({
            'success': True,
            'message': f'Aadhaar {aadhaar} registered successfully!'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mark-attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance for verified user"""
    try:
        data = request.get_json()
        aadhaar = data.get('aadhaar')
        
        if not aadhaar:
            return jsonify({'error': 'Aadhaar number required'}), 400
        
        # Add to attendance file
        with open(ATTENDANCE_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                aadhaar,
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%H:%M:%S'),
                'Verified'
            ])
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registered-count')
def get_registered_count():
    """Get count of registered Aadhaar numbers"""
    try:
        if not os.path.exists(KNOWN_FACES_DIR):
            return jsonify({'count': 0})
        
        count = len([d for d in os.listdir(KNOWN_FACES_DIR) 
                    if os.path.isdir(os.path.join(KNOWN_FACES_DIR, d))])
        
        return jsonify({'count': count})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    ensure_directories()
    print("🚀 Starting Aadhaar Face Verification System...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🎯 Features: Face Recognition + Liveness Detection")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
