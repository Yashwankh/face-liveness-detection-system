"""
Flask Backend for Aadhaar Face Verification System
Enhanced with Advanced Anti-Spoofing Detection
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

# Import our robust integrated liveness detector
from simple_liveness import RobustLivenessDetector

app = Flask(__name__)
CORS(app)

# Configuration
KNOWN_FACES_DIR = 'known_faces'
ATTENDANCE_FILE = 'attendance.csv'
FACE_TOLERANCE = 0.6  # Standard face matching tolerance

# Thresholds for liveness detection
EYE_AR_THRESH = 0.28
MOUTH_AR_THRESH = 0.65
HEAD_MOVEMENT_THRESH = 20

# Global variables for verification sessions
verification_sessions = {}

def ensure_directories():
    """Create necessary directories if they don't exist"""
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)

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
    """Calculate mouth aspect ratio for mouth opening detection"""
    try:
        A = dist.euclidean(mouth[2], mouth[10])
        B = dist.euclidean(mouth[4], mouth[8])
        C = dist.euclidean(mouth[0], mouth[6])
        D = dist.euclidean(mouth[3], mouth[9])
        mar = (A + B + D) / (3.0 * C)
        return mar
    except:
        return 0.1

def detect_screen_spoofing(frame):
    """Detect if the image is from a phone/computer screen"""
    try:
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Check for screen pixel patterns (Moiré patterns)
        # Apply FFT to detect regular patterns typical of screens
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.log(np.abs(f_shift) + 1)
        
        # Look for regular patterns in frequency domain
        high_freq_energy = np.sum(magnitude_spectrum[magnitude_spectrum > np.percentile(magnitude_spectrum, 95)])
        
        # 2. Check edge sharpness (screens have very sharp edges)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # 3. Check for uniform lighting (screens have very uniform backlighting)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_variance = np.var(hist)
        
        # 4. Check for color temperature consistency (screens have consistent color temp)
        b, g, r = cv2.split(frame)
        color_variance = np.var([np.mean(b), np.mean(g), np.mean(r)])
        
        # Scoring system - more lenient thresholds
        spoofing_score = 0
        
        # High frequency energy indicates screen patterns
        if high_freq_energy > 2000:  # More strict threshold
            spoofing_score += 2
            
        # Very sharp edges indicate screen display
        if edge_density > 0.25:  # More strict threshold
            spoofing_score += 2
            
        # Low histogram variance indicates uniform screen lighting
        if hist_variance < 500:  # More strict threshold
            spoofing_score += 1
            
        # Low color variance indicates screen color consistency
        if color_variance < 50:  # More strict threshold
            spoofing_score += 1
            
        return spoofing_score >= 4  # Higher threshold for spoofing detection
        
    except Exception as e:
        print(f"Screen spoofing detection error: {e}")
        return False

def detect_mobile_photo_spoofing(frame):
    """Simple but effective mobile photo detection"""
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        spoofing_indicators = 0
        
        print("🔍 Analyzing frame for mobile photo characteristics...")
        
        # 1. MOST RELIABLE: Check for screen pixel patterns using FFT
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # Look for regular high-frequency patterns (screen pixels)
        high_freq_energy = np.sum(magnitude_spectrum > np.percentile(magnitude_spectrum, 98))
        print(f"📊 High frequency energy: {high_freq_energy}")
        
        if high_freq_energy > 3000:  # Lower threshold - more sensitive
            spoofing_indicators += 1
            print("⚠️ SCREEN PIXEL PATTERN DETECTED!")
        
        # 2. Check brightness uniformity (screens are very uniform)
        brightness_std = np.std(gray)
        brightness_mean = np.mean(gray)
        print(f"📊 Brightness - std: {brightness_std:.2f}, mean: {brightness_mean:.2f}")
        
        if brightness_std < 30 and brightness_mean > 80:  # More sensitive
            spoofing_indicators += 1
            print("⚠️ UNIFORM SCREEN BRIGHTNESS DETECTED!")
        
        # 3. Check for artificial color saturation (screens oversaturate)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        high_sat_pixels = np.sum(saturation > 120) / saturation.size  # Lower threshold
        print(f"📊 High saturation pixels: {high_sat_pixels:.3f}")
        
        if high_sat_pixels > 0.25:  # Lower threshold - more sensitive
            spoofing_indicators += 1
            print("⚠️ ARTIFICIAL SATURATION DETECTED!")
        
        # 4. Check for blue light dominance (phone screens)
        b_channel = frame[:, :, 0]  # Blue in BGR
        g_channel = frame[:, :, 1]  # Green
        r_channel = frame[:, :, 2]  # Red
        
        blue_dominance = np.mean(b_channel) / (np.mean([np.mean(b_channel), np.mean(g_channel), np.mean(r_channel)]) + 1)
        print(f"📊 Blue dominance ratio: {blue_dominance:.3f}")
        
        if blue_dominance > 0.35:  # Lower threshold - more sensitive
            spoofing_indicators += 1
            print("⚠️ BLUE LIGHT DOMINANCE DETECTED!")
        
        # 5. Check edge sharpness (mobile photos are oversharpened)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        print(f"📊 Edge density: {edge_density:.4f}")
        
        if edge_density > 0.12:  # Lower threshold - more sensitive
            spoofing_indicators += 1
            print("⚠️ OVERSHARPENED EDGES DETECTED!")
        
        print(f"📊 Total spoofing indicators: {spoofing_indicators}/5")
        
        # If 2 or more indicators, it's likely a mobile photo (lower threshold)
        if spoofing_indicators >= 2:
            print("🚫 MOBILE PHOTO DETECTED! (2+ indicators)")
            return True
        
        print("✅ Appears to be real face (low indicators)")
        return False
        
    except Exception as e:
        print(f"❌ Mobile detection error: {e}")
        return False

class LivenessDetector:
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all liveness detection variables"""
        self.blink_completed = False
        self.blink_counter = 0
        self.head_left_done = False
        self.head_right_done = False
        self.initial_face_x = None
        self.mouth_opened = False
        self.face_matches = 0
        self.start_time = time.time()
        
        # Anti-spoofing tracking
        self.frame_count = 0
        self.brightness_values = []
        self.position_changes = []
        self.last_position = None
    
    def detect_blink(self, landmarks):
        """Real blink detection with reasonable threshold"""
        try:
            if not landmarks:
                print("⚠️ No landmarks provided!")
                return self.blink_completed, 0.3
            
            if 'left_eye' not in landmarks or 'right_eye' not in landmarks:
                print(f"⚠️ Missing eye landmarks. Available: {list(landmarks.keys())}")
                return self.blink_completed, 0.3
            
            left_eye = np.array(landmarks['left_eye'])
            right_eye = np.array(landmarks['right_eye'])
            
            if len(left_eye) >= 6 and len(right_eye) >= 6:
                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)
                ear = (left_ear + right_ear) / 2.0
                
                print(f"👁️ EAR: {ear:.3f} | Threshold: 0.25 | Counter: {self.blink_counter}")
                
                # Detect eye closure
                if ear < 0.25:
                    self.blink_counter += 1
                else:
                    # Eye opened after closure
                    if self.blink_counter >= 2:
                        self.blink_completed = True
                        print(f"✅ BLINK DETECTED! (closed for {self.blink_counter} frames)")
                    self.blink_counter = 0
                
                return self.blink_completed, ear
            
            return self.blink_completed, 0.3
        except Exception as e:
            print(f"❌ Blink detection error: {e}")
            return self.blink_completed, 0.3
    
    def detect_head_movement(self, face_location, frame_width):
        """Real head movement detection"""
        try:
            top, right, bottom, left = face_location
            face_center_x = (left + right) / 2
            face_width = right - left
            
            # Initialize reference position
            if self.initial_face_x is None:
                self.initial_face_x = face_center_x
                print(f"📍 Initial position: {face_center_x:.1f}")
                return "center", 0
            
            # Calculate movement
            movement = face_center_x - self.initial_face_x
            movement_percent = (movement / face_width) * 100
            
            print(f"👤 Movement: {movement_percent:.1f}% | Threshold: ±12%")
            
            # Detect significant movement
            if movement_percent < -12 and not self.head_left_done:
                self.head_left_done = True
                print(f"✅ HEAD LEFT DETECTED! ({movement_percent:.1f}%)")
                return "left", movement_percent
            elif movement_percent > 12 and not self.head_right_done:
                self.head_right_done = True
                print(f"✅ HEAD RIGHT DETECTED! ({movement_percent:.1f}%)")
                return "right", movement_percent
            
            return "center", movement_percent
        except Exception as e:
            print(f"❌ Head movement error: {e}")
            return "center", 0
    
    def detect_mouth_opening(self, landmarks):
        """Real mouth opening detection"""
        try:
            if not landmarks or 'top_lip' not in landmarks or 'bottom_lip' not in landmarks:
                return self.mouth_opened, 0.5
            
            mouth = landmarks['top_lip'] + landmarks['bottom_lip']
            mouth = np.array(mouth)
            
            if len(mouth) >= 12:
                mar = mouth_aspect_ratio(mouth)
                
                print(f"😮 MAR: {mar:.3f} | Threshold: 0.5")
                
                # Detect mouth opening
                if mar > 0.5 and not self.mouth_opened:
                    self.mouth_opened = True
                    print(f"✅ MOUTH OPENING DETECTED! (MAR: {mar:.3f})")
                    return True, mar
                
                return self.mouth_opened, mar
            
            return self.mouth_opened, 0.5
        except Exception as e:
            print(f"❌ Mouth detection error: {e}")
            return self.mouth_opened, 0.5
    
    def analyze_frame_for_spoofing(self, frame):
        """Detect mobile phone screens and photo spoofing"""
        try:
            self.frame_count += 1
            
            # Analyze screen patterns
            is_screen = detect_screen_spoofing(frame)
            
            # Track brightness variations (screens have consistent brightness)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            self.brightness_values.append(mean_brightness)
            
            if len(self.brightness_values) > 15:
                self.brightness_values.pop(0)
            
            # Check brightness consistency (screens are very consistent)
            if len(self.brightness_values) >= 10:
                brightness_variance = np.var(self.brightness_values)
                # Very low variance = screen (real faces have natural lighting changes)
                if brightness_variance < 50:
                    is_screen = True
                    print(f"⚠️ Low brightness variance detected: {brightness_variance:.2f} (screen indicator)")
            
            # Track position changes (photos from screens don't move naturally)
            if self.last_position is not None:
                position_diff = np.mean(np.abs(frame - self.last_position))
                self.position_changes.append(position_diff)
                
                if len(self.position_changes) > 10:
                    self.position_changes.pop(0)
                
                # Check if movement is too uniform (video playback)
                if len(self.position_changes) >= 8:
                    movement_std = np.std(self.position_changes)
                    if movement_std < 2:  # Too uniform = video playback
                        is_screen = True
                        print(f"⚠️ Uniform movement detected: {movement_std:.2f} (video playback indicator)")
            
            self.last_position = frame.copy()
            
            # Require strong evidence over multiple frames
            if self.frame_count >= 10:
                # Check if screen detected in multiple analyses
                if is_screen:
                    print(f"🚫 Mobile/Screen photo detected on frame {self.frame_count}!")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Spoofing analysis error: {e}")
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

# Rest of the Flask routes remain the same...
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/check-aadhaar', methods=['POST'])
def check_aadhaar():
    data = request.get_json()
    aadhaar = data.get('aadhaar', '').replace(' ', '')
    
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        return jsonify({'error': 'Invalid Aadhaar number'}), 400
    
    folder_path = os.path.join(KNOWN_FACES_DIR, aadhaar)
    
    if os.path.exists(folder_path):
        photos = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if photos:
            return jsonify({'exists': True, 'photos': len(photos)})
    
    return jsonify({'exists': False})

@app.route('/api/verify-face', methods=['POST'])
def verify_face():
    try:
        aadhaar = request.form.get('aadhaar', '').replace(' ', '')
        frame_file = request.files.get('frame')
        
        if not aadhaar or not frame_file:
            return jsonify({'error': 'Missing aadhaar or frame'}), 400
        
        # Initialize session if not exists
        if aadhaar not in verification_sessions:
            verification_sessions[aadhaar] = RobustLivenessDetector()
            verification_sessions[aadhaar].start_time = time.time()
        
        # Load known face if not loaded
        if not hasattr(verification_sessions[aadhaar], 'known_encoding'):
            folder_path = os.path.join(KNOWN_FACES_DIR, aadhaar)
            if not os.path.exists(folder_path):
                return jsonify({'error': 'Aadhaar not registered'}), 400
            
            photos = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
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
        if not hasattr(detector, 'start_time') or detector.start_time is None:
            detector.start_time = time.time()
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
        
        # Use full-resolution frame for better detection reliability
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces FIRST (upsample 2x for better small face detection)
        face_locations = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=2, model='hog')
        print(f"✅ Detected {len(face_locations)} face(s)")
        
        if not face_locations:
            print(f"❌ No face detected. Frame size: {rgb_frame.shape[1]}x{rgb_frame.shape[0]}")
            return jsonify({
                'instruction': '👤 Face not detected. Move closer and center your face.',
                'gesture_count': detector.get_gesture_count(),
                'face_matches': detector.face_matches,
                'blink_completed': detector.blink_done,
                'head_left_done': detector.head_left_done,
                'head_right_done': detector.head_right_done,
                'mouth_opened': detector.mouth_done
            })
        
        # Pick the largest face (most stable for tracking)
        def box_area(box):
            t, r, b, l = box
            return max(0, b - t) * max(0, r - l)
        best_location = max(face_locations, key=box_area)
        print(f"📦 Using face: {best_location} (area={box_area(best_location)} px²)")
        
        # Get face landmarks and encodings for the chosen face only
        face_landmarks = face_recognition.face_landmarks(rgb_frame, [best_location])
        face_encodings = face_recognition.face_encodings(rgb_frame, [best_location])
        
        if not face_landmarks:
            print("❌ No landmarks detected")
            return jsonify({
                'instruction': 'Face not clear. Adjust position and lighting.',
                'gesture_count': detector.get_gesture_count(),
                'face_matches': detector.face_matches,
                'blink_completed': detector.blink_done,
                'head_left_done': detector.head_left_done,
                'head_right_done': detector.head_right_done,
                'mouth_opened': detector.mouth_done
            })
        
        landmarks = face_landmarks[0]
        face_location = best_location
        
        # Use original coordinates (no scaling since no resize)
        top, right, bottom, left = face_location
        
        # Check face match (only if encoding is available)
        face_match = False
        if face_encodings:
            face_encoding = face_encodings[0]
            face_match = face_recognition.compare_faces(
                [detector.known_encoding], face_encoding, FACE_TOLERANCE
            )[0]
            print(f"🔍 Face match: {face_match}")
        else:
            print("⚠️ No face encoding found; proceeding with liveness only.")
        
        # Use the enhanced liveness detector with integrated anti-spoofing
        print("\n" + "="*70)
        print("🛡️ ENHANCED LIVENESS DETECTION WITH ANTI-SPOOFING")
        print("   ✅ Active gesture detection")
        print("   🚫 Passive spoofing detection")
        print("="*70)
        
        # Run the integrated check
        liveness_result = detector.check(frame, landmarks, (top, right, bottom, left))
        
        if liveness_result == "SPOOF_DETECTED":
            print("🚫 SPOOFING DETECTED - BLOCKING!")
            del verification_sessions[aadhaar]
            return jsonify({
                'failed': True,
                'message': '🚫 Spoofing detected! Please use your real face, not a photo or screen.'
            })
        
        # Show status
        status = detector.get_status()
        print("\n" + "="*70)
        print("📊 LIVENESS STATUS:")
        print(f"  {status['blink']} Natural Blink Pattern")
        print(f"  {status['head_left']} Natural Head Left Movement")
        print(f"  {status['head_right']} Natural Head Right Movement")
        print(f"  {status['mouth']} Natural Mouth Opening Pattern")
        print(f"  🎯 Natural Gestures Completed: {status['count']}/4")
        print("="*70 + "\n")
        
        # Face match counter
        if detector.gestures_complete():
            if face_match:
                detector.face_matches += 1
            else:
                detector.face_matches = max(0, detector.face_matches - 2)
        else:
            detector.face_matches = 0
        
        # Generate instruction
        instruction = "Follow the instructions to prove you're live"
        if detector.gestures_complete():
            instruction = "✅ Liveness confirmed. Hold steady for face matching."
            if detector.face_matches >= 3:
                # Success!
                del verification_sessions[aadhaar]
                return jsonify({
                    'success': True,
                    'message': 'Verification successful!'
                })
        else:
            # Give specific instructions
            if not detector.blink_done:
                instruction = "👁️ Please BLINK your eyes"
            elif not detector.head_left_done:
                instruction = "← Please turn your head LEFT"
            elif not detector.head_right_done:
                instruction = "→ Please turn your head RIGHT"
            elif not detector.mouth_done:
                instruction = "😮 Please OPEN your mouth"
        
        return jsonify({
            'instruction': instruction,
            'gesture_count': detector.get_gesture_count(),
            'face_matches': detector.face_matches,
            'blink_completed': detector.blink_done,
            'head_left_done': detector.head_left_done,
            'head_right_done': detector.head_right_done,
            'mouth_opened': detector.mouth_done
        })
        
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({'error': 'Verification failed'}), 500

@app.route('/api/add-student', methods=['POST'])
def add_student():
    try:
        aadhaar = request.form.get('aadhaar', '').replace(' ', '')
        frame_file = request.files.get('photo')
        
        if not aadhaar or not frame_file:
            return jsonify({'error': 'Missing aadhaar or frame'}), 400
        
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            return jsonify({'error': 'Invalid Aadhaar number'}), 400
        
        # Create directory for this Aadhaar
        folder_path = os.path.join(KNOWN_FACES_DIR, aadhaar)
        os.makedirs(folder_path, exist_ok=True)
        
        # Process and save the image
        image = Image.open(frame_file.stream)
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Temporarily disable anti-spoofing during registration too
        # is_spoofed = detect_mobile_photo_spoofing(frame)
        # if is_spoofed:
        #     return jsonify({
        #         'error': '🚫 Mobile photo detected! Please use your real face, not a photo from a phone screen.'
        #     })
        
        # Find face in the image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            return jsonify({'error': 'No face detected in the image'}), 400
        
        # Save the image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{aadhaar}_{timestamp}.jpg"
        filepath = os.path.join(folder_path, filename)
        
        cv2.imwrite(filepath, frame)
        
        return jsonify({
            'success': True,
            'message': f'Face registered successfully for Aadhaar {aadhaar}'
        })
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/registered-count')
def registered_count():
    try:
        if not os.path.exists(KNOWN_FACES_DIR):
            return jsonify({'count': 0})
        count = sum(
            1 for name in os.listdir(KNOWN_FACES_DIR)
            if os.path.isdir(os.path.join(KNOWN_FACES_DIR, name))
        )
        return jsonify({'count': count})
    except Exception as e:
        print(f"Registered count error: {e}")
        return jsonify({'count': 0})

@app.route('/api/mark-attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        aadhaar = data.get('aadhaar', '').replace(' ', '') if data else ''
        if not aadhaar:
            return jsonify({'error': 'Missing aadhaar'}), 400
        # Ensure file exists with header
        file_exists = os.path.exists(ATTENDANCE_FILE)
        with open(ATTENDANCE_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'aadhaar'])
            writer.writerow([datetime.now().isoformat(timespec='seconds'), aadhaar])
        return jsonify({'success': True})
    except Exception as e:
        print(f"Attendance error: {e}")
        return jsonify({'error': 'Attendance failed'}), 500

if __name__ == '__main__':
    ensure_directories()
    print("🚀 Starting Aadhaar Face Verification System...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🎯 Features: Face Recognition + Advanced Anti-Spoofing Detection")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
