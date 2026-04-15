// Global variables
let currentStream = null;
let isVerifying = false;
let verificationTimer = null;

// Page navigation functions
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show selected page
    document.getElementById(pageId).classList.add('active');
    
    // Stop any active streams when changing pages
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}

function showHome() {
    showPage('homePage');
    updateRegisteredCount();
}

function showAddStudent() {
    showPage('addStudentPage');
    document.getElementById('newAadhaarInput').focus();
}

function showVerification() {
    showPage('verificationPage');
}

function showSuccess() {
    showPage('successPage');
}

// Format Aadhaar number input
function formatAadhaarInput(input) {
    let value = input.value.replace(/\D/g, ''); // Remove non-digits
    let formatted = value.replace(/(\d{4})(\d{4})(\d{4})/, '$1 $2 $3');
    if (value.length <= 12) {
        input.value = formatted;
    }
}

// Add event listeners for Aadhaar formatting
document.addEventListener('DOMContentLoaded', function() {
    const aadhaarInputs = document.querySelectorAll('#aadhaarInput, #newAadhaarInput');
    aadhaarInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatAadhaarInput(this);
        });
        
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                if (this.id === 'aadhaarInput') {
                    verifyAadhaar();
                }
            }
        });
    });
    
    // Initialize page
    showHome();
});

// Verification functions
async function verifyAadhaar() {
    const aadhaarNumber = document.getElementById('aadhaarInput').value.replace(/\s/g, '');
    
    if (aadhaarNumber.length !== 12) {
        alert('Please enter a valid 12-digit Aadhaar number.');
        return;
    }
    
    try {
        // Check if Aadhaar exists in backend
        const response = await fetch('/api/check-aadhaar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ aadhaar: aadhaarNumber })
        });
        
        const result = await response.json();
        
        if (result.exists) {
            document.getElementById('currentAadhaar').textContent = aadhaarNumber;
            showVerification();
            startVerification(aadhaarNumber);
        } else {
            alert(`Aadhaar number '${aadhaarNumber}' not found in the database.`);
        }
    } catch (error) {
        console.error('Error checking Aadhaar:', error);
        alert('Error connecting to server. Please try again.');
    }
}

async function startVerification(aadhaarNumber) {
    try {
        // Get camera access
        currentStream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 } 
        });
        
        const video = document.getElementById('verifyVideo');
        video.srcObject = currentStream;
        
        // Reset verification status
        resetVerificationStatus();
        
        // Start verification process
        isVerifying = true;
        startVerificationTimer();
        
        // Start face detection loop
        detectFaces(video, aadhaarNumber);
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        alert('Could not access camera. Please ensure camera permissions are granted.');
    }
}

function resetVerificationStatus() {
    const statusItems = [
        'blinkStatus', 'leftStatus', 'rightStatus', 'mouthStatus'
    ];
    
    statusItems.forEach(id => {
        const badge = document.querySelector(`#${id} .status-badge`);
        badge.textContent = '❌ PENDING';
        badge.className = 'status-badge pending';
    });
    
    document.querySelector('#gestureCount .status-badge').textContent = '0 / 4';
    document.querySelector('#faceMatch .status-badge').textContent = '0 / 5';
    document.querySelector('#timer .status-badge').textContent = '60.0s';
}

function startVerificationTimer() {
    let timeRemaining = 60.0;
    
    verificationTimer = setInterval(() => {
        timeRemaining -= 0.1;
        document.querySelector('#timer .status-badge').textContent = `${timeRemaining.toFixed(1)}s`;
        
        if (timeRemaining <= 0) {
            clearInterval(verificationTimer);
            failVerification('Time limit exceeded');
        }
    }, 100);
}

async function detectFaces(video, aadhaarNumber) {
    // This would integrate with the Python backend for actual face detection
    // For now, we'll simulate the process
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const detectLoop = async () => {
        if (!isVerifying) return;
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        
        // Convert canvas to blob and send to backend
        canvas.toBlob(async (blob) => {
            if (!isVerifying) return;
            
            try {
                const formData = new FormData();
                formData.append('frame', blob);
                formData.append('aadhaar', aadhaarNumber);
                
                const response = await fetch('/api/verify-face', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                updateVerificationStatus(result);
                
                if (result.success) {
                    completeVerification(aadhaarNumber);
                } else if (result.failed) {
                    failVerification(result.message);
                }
                
            } catch (error) {
                console.error('Error processing frame:', error);
            }
            
            // Continue loop
            setTimeout(detectLoop, 100);
        }, 'image/jpeg', 0.8);
    };
    
    // Start detection when video is ready
    video.addEventListener('loadeddata', detectLoop);
}

function updateVerificationStatus(result) {
    // Update gesture status
    if (result.blink_completed) {
        updateStatusBadge('blinkStatus', true);
    }
    if (result.head_left_done) {
        updateStatusBadge('leftStatus', true);
    }
    if (result.head_right_done) {
        updateStatusBadge('rightStatus', true);
    }
    if (result.mouth_opened) {
        updateStatusBadge('mouthStatus', true);
    }
    
    // Update counters
    document.querySelector('#gestureCount .status-badge').textContent = 
        `${result.gesture_count || 0} / 4`;
    document.querySelector('#faceMatch .status-badge').textContent = 
        `${result.face_matches || 0} / 5`;
    
    // Update instruction
    if (result.instruction) {
        const banner = document.getElementById('instructionBanner');
        banner.textContent = result.instruction;
        banner.className = result.instruction.includes('✅') ? 
            'instruction-banner success' : 'instruction-banner';
    }
}

function updateStatusBadge(statusId, completed) {
    const badge = document.querySelector(`#${statusId} .status-badge`);
    if (completed) {
        badge.textContent = '✅ COMPLETE';
        badge.className = 'status-badge complete';
    }
}

function completeVerification(aadhaarNumber) {
    isVerifying = false;
    clearInterval(verificationTimer);
    
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    
    document.getElementById('successAadhaarNumber').textContent = aadhaarNumber;
    showSuccess();
    
    // Mark attendance
    markAttendance(aadhaarNumber);
}

function failVerification(message) {
    isVerifying = false;
    clearInterval(verificationTimer);
    
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    
    alert(`Verification Failed: ${message}`);
    showHome();
}

function cancelVerification() {
    isVerifying = false;
    clearInterval(verificationTimer);
    
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    
    showHome();
}

// Add Student functions
async function startAddCamera() {
    const aadhaarNumber = document.getElementById('newAadhaarInput').value.replace(/\s/g, '');
    
    if (aadhaarNumber.length !== 12) {
        alert('Please enter a valid 12-digit Aadhaar number.');
        return;
    }
    
    try {
        currentStream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 } 
        });
        
        const video = document.getElementById('addVideo');
        video.srcObject = currentStream;
        
        document.getElementById('addStatus').textContent = 'Position your face in the green circle';
        document.querySelector('button[onclick="startAddCamera()"]').disabled = true;
        document.querySelector('button[onclick="capturePhoto()"]').disabled = false;
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        alert('Could not access camera. Please ensure camera permissions are granted.');
    }
}

async function capturePhoto() {
    const aadhaarNumber = document.getElementById('newAadhaarInput').value.replace(/\s/g, '');
    const video = document.getElementById('addVideo');
    
    // Create canvas to capture frame
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    // Convert to blob and send to backend
    canvas.toBlob(async (blob) => {
        try {
            const formData = new FormData();
            formData.append('photo', blob);
            formData.append('aadhaar', aadhaarNumber);
            
            const response = await fetch('/api/add-student', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(`Aadhaar holder '${aadhaarNumber}' was added successfully.`);
                
                // Stop camera
                if (currentStream) {
                    currentStream.getTracks().forEach(track => track.stop());
                    currentStream = null;
                }
                
                showHome();
            } else {
                alert(`Error: ${result.message}`);
            }
            
        } catch (error) {
            console.error('Error adding student:', error);
            alert('Error connecting to server. Please try again.');
        }
    }, 'image/jpeg', 0.9);
}

// Utility functions
async function markAttendance(aadhaarNumber) {
    try {
        await fetch('/api/mark-attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ aadhaar: aadhaarNumber })
        });
    } catch (error) {
        console.error('Error marking attendance:', error);
    }
}

async function updateRegisteredCount() {
    try {
        const response = await fetch('/api/registered-count');
        const result = await response.json();
        document.getElementById('registeredCount').textContent = result.count || 0;
    } catch (error) {
        console.error('Error getting registered count:', error);
        document.getElementById('registeredCount').textContent = '0';
    }
}

// Error handling for camera access
window.addEventListener('error', function(e) {
    if (e.message.includes('camera') || e.message.includes('getUserMedia')) {
        alert('Camera access error. Please check your camera permissions and try again.');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
    }
});
