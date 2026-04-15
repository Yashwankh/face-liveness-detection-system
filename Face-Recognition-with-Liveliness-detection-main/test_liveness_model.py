"""
Test liveness model loading
"""

import os
from tensorflow.keras.models import load_model

LIVENESS_MODEL_PATH = 'liveness.model'

print("="*60)
print("Testing Liveness Model Loading")
print("="*60)
print()

# Check if file exists
if os.path.exists(LIVENESS_MODEL_PATH):
    print(f"✅ Model file found: {LIVENESS_MODEL_PATH}")
    print(f"📏 File size: {os.path.getsize(LIVENESS_MODEL_PATH):,} bytes")
    print()
    
    try:
        print("Loading model...")
        model = load_model(LIVENESS_MODEL_PATH, compile=False)
        print("✅ Model loaded successfully!")
        print()
        print("Model summary:")
        model.summary()
        
    except Exception as e:
        print(f"❌ Error loading model:")
        print(f"   {type(e).__name__}: {str(e)}")
        print()
        print("This is likely due to Keras version compatibility.")
        print("The model needs to be re-trained with current TensorFlow version.")
        
else:
    print(f"❌ Model file not found: {LIVENESS_MODEL_PATH}")

print()
print("="*60)
