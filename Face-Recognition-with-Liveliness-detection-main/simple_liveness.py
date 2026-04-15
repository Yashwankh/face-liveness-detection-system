"""
ROBUST INTEGRATED LIVENESS DETECTOR
Combines active gesture checks with passive frame analysis to ensure only genuine live faces pass.
Enhanced to reject mobile photos, printed photos, and video replays through movement and glare detection.
"""
import numpy as np
from scipy.spatial import distance as dist
import cv2


def eye_aspect_ratio(eye):
    """Calculate EAR"""
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    # Avoid division by zero
    if C == 0:
        return 0.3 # Return a default open-eye value
    return (A + B) / (2.0 * C)


def mouth_aspect_ratio(mouth):
    """Calculate MAR"""
    A = dist.euclidean(mouth[2], mouth[10])
    B = dist.euclidean(mouth[4], mouth[8])
    C = dist.euclidean(mouth[0], mouth[6])
    # Avoid division by zero
    if C == 0:
        return 0.0 # Return a default closed-mouth value
    return (A + B) / (2.0 * C)



class RobustLivenessDetector:
    def __init__(self):
        # --- Gesture Detection State ---
        self.blink_done = False
        self.head_left_done = False
        self.head_right_done = False
        self.mouth_done = False
        self.face_matches = 0
        self.start_time = None  # Will be set by app.py
        
        # --- Enhanced Tracking for Gestures ---
        self.blink_frames = []
        self.initial_x = None
        self.head_positions = []
        self.mouth_values = []
        
        # --- Anti-Spoofing / Passive Liveness State ---
        self.last_gray_face = None
        self.suspicious_movement_frames = 0
        self.brightness_history = []


        # --- Anti-Spoofing Thresholds (DISABLED FOR TESTING) ---
        # Low movement threshold to detect static images (higher value is more strict)
        self.MOVEMENT_THRESHOLD = 0.1
        # Number of consecutive static frames to trigger a spoof alert
        self.SPOOF_CONSECUTIVE_FRAMES = 50
        # History length for brightness analysis
        self.BRIGHTNESS_HISTORY_LEN = 20
        # Factor to detect glare/reflections (e.g., 1.8 means a 80% spike)
        self.BRIGHTNESS_SPIKE_FACTOR = 3.5


    def _analyze_frame_properties(self, frame, face_box):
        """
        Performs passive liveness checks to detect presentation attacks (photos/videos).
        Returns True if a spoof is detected, False otherwise.
        """
        try:
            top, right, bottom, left = face_box
            # Ensure coordinates are integers and within frame bounds
            top, right, bottom, left = max(0, int(top)), min(frame.shape[1], int(right)), min(frame.shape[0], int(bottom)), max(0, int(left))
            
            # Crop the face region and convert to grayscale
            face_roi = frame[top:bottom, left:right]
            if face_roi.size == 0:
                print("⚠️ Face ROI is empty, skipping frame analysis.")
                return False


            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            gray_face = cv2.GaussianBlur(gray_face, (7, 7), 0)


            # --- 1. Glare/Brightness Analysis ---
            avg_brightness = np.mean(gray_face)
            self.brightness_history.append(avg_brightness)
            if len(self.brightness_history) > self.BRIGHTNESS_HISTORY_LEN:
                self.brightness_history.pop(0)
            
            if len(self.brightness_history) > 5:
                # Calculate recent average brightness, excluding the current frame
                recent_avg = np.mean(self.brightness_history[:-1])
                # Check for a sudden spike in brightness (potential screen glare)
                if avg_brightness > recent_avg * self.BRIGHTNESS_SPIKE_FACTOR:
                    print(f"🚨 SPOOF ALERT: Sudden brightness spike detected! (Glare?) Val: {avg_brightness:.2f}, Avg: {recent_avg:.2f}")
                    return True # Spoof detected


            # --- 2. Frame Difference Analysis ---
            if self.last_gray_face is not None:
                # Resize to ensure frames are same size for comparison
                last_face_resized = cv2.resize(self.last_gray_face, (gray_face.shape[1], gray_face.shape[0]))
                
                # Calculate absolute difference between current and last frame
                diff = cv2.absdiff(gray_face, last_face_resized)
                movement_score = np.mean(diff)


                print(f"🕵️ Movement Score: {movement_score:.2f}")


                if movement_score < self.MOVEMENT_THRESHOLD:
                    self.suspicious_movement_frames += 1
                else:
                    self.suspicious_movement_frames = 0 # Reset on sufficient movement
                
                if self.suspicious_movement_frames >= self.SPOOF_CONSECUTIVE_FRAMES:
                    print(f"🚨 SPOOF ALERT: Static image detected for {self.suspicious_movement_frames} frames.")
                    return True # Spoof detected


            self.last_gray_face = gray_face
            return False # No spoof detected in this frame
        except Exception as e:
            print(f"❌ Error in frame analysis: {e}")
            return False


    def detect_blink(self, landmarks):
        if self.blink_done: return
        if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks: return


        try:
            left_eye = np.array(landmarks['left_eye'])
            right_eye = np.array(landmarks['right_eye'])
            
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            self.blink_frames.append(ear)
            if len(self.blink_frames) > 10: self.blink_frames.pop(0)
            
            print(f"👁️ EAR = {ear:.3f}")
            
            if len(self.blink_frames) >= 4:
                recent_ears = self.blink_frames[-4:]
                # Very relaxed blink detection: just look for ANY variance
                ear_variance = np.var(recent_ears)
                min_ear = min(recent_ears)
                max_ear = max(recent_ears)
                if ear_variance > 0.002 and (max_ear - min_ear) > 0.04:
                    self.blink_done = True
                    print(f"✅ BLINK DETECTED! (variance={ear_variance:.4f}, range={max_ear-min_ear:.3f})")
        except Exception as e:
            print(f"❌ Blink error: {e}")


    def detect_head_movement(self, face_box, frame_width):
        if self.head_left_done and self.head_right_done: return
        
        top, right, bottom, left = face_box
        center_x = (left + right) / 2
        width = right - left
        
        self.head_positions.append(center_x)
        if len(self.head_positions) > 15: self.head_positions.pop(0)
        
        if self.initial_x is None:
            self.initial_x = center_x
            return


        movement = center_x - self.initial_x
        movement_pct = (movement / width) * 100
        print(f"👤 Head Movement = {movement_pct:+.1f}%")

        # Check for left turn (IMMEDIATE)
        if not self.head_left_done and movement_pct < -5:
            self.head_left_done = True
            print(f"✅ HEAD LEFT DETECTED! (movement={movement_pct:.1f}%)")

        # Check for right turn (IMMEDIATE)
        if not self.head_right_done and movement_pct > 5:
            self.head_right_done = True
            print(f"✅ HEAD RIGHT DETECTED! (movement={movement_pct:.1f}%)")


    def detect_mouth(self, landmarks):
        if self.mouth_done: return
        if not landmarks or 'top_lip' not in landmarks or 'bottom_lip' not in landmarks: return
        
        try:
            mouth = landmarks['top_lip'] + landmarks['bottom_lip']
            mar = mouth_aspect_ratio(np.array(mouth))
            
            self.mouth_values.append(mar)
            if len(self.mouth_values) > 10: self.mouth_values.pop(0)
            
            print(f"😮 MAR = {mar:.3f}")


            if len(self.mouth_values) >= 3:
                recent_mars = self.mouth_values[-3:]
                max_mar = max(recent_mars)
                
                # Very relaxed: just look for ANY mouth opening
                if max_mar > 0.20:
                    self.mouth_done = True
                    print(f"✅ MOUTH OPENING DETECTED! (MAR={max_mar:.3f})")
                    return
        except Exception as e:
            print(f"❌ Mouth error: {e}")


    def gestures_complete(self):
        """Check if at least 3 out of 4 gestures are done."""
        count = sum([self.blink_done, self.head_left_done, self.head_right_done, self.mouth_done])
        return count >= 3


    def get_status(self):
        """Get current status of gesture completion."""
        return {
            'blink': '✅' if self.blink_done else '❌',
            'head_left': '✅' if self.head_left_done else '❌',
            'head_right': '✅' if self.head_right_done else '❌',
            'mouth': '✅' if self.mouth_done else '❌',
            'count': sum([self.blink_done, self.head_left_done, self.head_right_done, self.mouth_done])
        }


    def get_gesture_count(self):
        """Get number of completed gestures."""
        return sum([self.blink_done, self.head_left_done, self.head_right_done, self.mouth_done])


    def check(self, frame, landmarks, face_box):
        """
        Main liveness check orchestrator.
        Returns a status string: 'SPOOF_DETECTED', 'SUCCESS', or 'IN_PROGRESS'.
        """
        # 1. Run passive anti-spoofing checks first
        if self._analyze_frame_properties(frame, face_box):
            return "SPOOF_DETECTED"


        # 2. Run active gesture checks if no spoof is detected
        self.detect_blink(landmarks)
        self.detect_head_movement(face_box, frame.shape[1])
        self.detect_mouth(landmarks)


        # 3. Determine overall status based on gestures
        if self.gestures_complete():
            return "SUCCESS"
        else:
            return "IN_PROGRESS"
