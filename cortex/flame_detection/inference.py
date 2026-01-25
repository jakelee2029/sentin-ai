"""
Real-time Flame Detection Inference

Runs TensorFlow Lite model on USB camera feed (Logitech Brio 101)
for edge AI flame verification.
"""

import numpy as np
import cv2
import tensorflow as tf
from pathlib import Path
import time

class FlameInference:
    """Real-time flame detection using TFLite model"""
    
    def __init__(self, model_path, confidence_threshold=0.85):
        """
        Initialize inference engine
        
        Args:
            model_path: Path to .tflite model file
            confidence_threshold: Minimum confidence for positive detection
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.input_shape = None
        
        self._load_model()
    
    def _load_model(self):
        """Load TFLite model and allocate tensors"""
        
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        # Load TFLite model
        self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()
        
        # Get input and output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.input_shape = self.input_details[0]['shape'][1:3]  # (H, W)
        
        print(f"✓ Model loaded: {self.model_path}")
        print(f"  Input shape: {self.input_shape}")
    
    def preprocess_frame(self, frame):
        """
        Preprocess camera frame for model input
        
        Args:
            frame: OpenCV image (BGR format)
        
        Returns:
            Preprocessed tensor
        """
        # Resize to model input size
        resized = cv2.resize(frame, tuple(self.input_shape))
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1] (model expects this)
        normalized = rgb.astype(np.float32) / 255.0
        
        # Add batch dimension
        input_tensor = np.expand_dims(normalized, axis=0)
        
        return input_tensor
    
    def detect_flame(self, frame):
        """
        Run inference on a single frame
        
        Args:
            frame: OpenCV image
        
        Returns:
            dict with 'flame_detected', 'confidence', 'inference_time'
        """
        start_time = time.time()
        
        # Preprocess
        input_tensor = self.preprocess_frame(frame)
        
        # Set input tensor
        self.interpreter.set_tensor(
            self.input_details[0]['index'],
            input_tensor
        )
        
        # Run inference
        self.interpreter.invoke()
        
        # Get output (softmax probabilities)
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Extract probabilities [no_flame, flame]
        no_flame_prob = output[0][0]
        flame_prob = output[0][1]
        
        inference_time = (time.time() - start_time) * 1000  # ms
        
        return {
            'flame_detected': flame_prob >= self.confidence_threshold,
            'confidence': float(flame_prob),
            'no_flame_confidence': float(no_flame_prob),
            'inference_time_ms': inference_time
        }
    
    def detect_with_visualization(self, frame):
        """
        Detect flame and annotate frame
        
        Args:
            frame: OpenCV image
        
        Returns:
            Annotated frame, detection result
        """
        result = self.detect_flame(frame)
        annotated = frame.copy()
        
        # Determine color based on detection
        if result['flame_detected']:
            color = (0, 0, 255)  # Red
            label = f"FLAME DETECTED ({result['confidence']:.2%})"
        else:
            color = (0, 255, 0)  # Green
            label = f"Clear ({result['no_flame_confidence']:.2%})"
        
        # Draw bounding box and label
        h, w = frame.shape[:2]
        cv2.rectangle(annotated, (10, 10), (w-10, 60), color, 2)
        cv2.putText(
            annotated, 
            label,
            (20, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )
        
        # Show inference time
        cv2.putText(
            annotated,
            f"{result['inference_time_ms']:.1f}ms",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        return annotated, result


class CameraCapture:
    """USB camera interface for Logitech Brio 101"""
    
    def __init__(self, camera_id=0, resolution=(640, 480), fps=30):
        """
        Initialize USB camera
        
        Args:
            camera_id: USB camera device ID (typically 0-2, varies by system)
            resolution: Target resolution (W, H) - default 640x480 for optimal AI performance
            fps: Frames per second - Brio 101 supports up to 30fps @ 1080p
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.fps = fps
        self.cap = None
        
    def open(self):
        """Open USB camera stream with optimized settings for Logitech Brio 101"""
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Failed to open camera ID {self.camera_id}. "
                f"Ensure Logitech Brio 101 is connected via USB. "
                f"Run: python -c 'import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])' "
                f"to find available cameras."
            )
        
        # Configure camera resolution and frame rate
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Optimize Brio 101 settings for fire detection
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Auto exposure for varying light conditions
        
        # Verify actual settings (camera may not support requested values)
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        print(f"✓ Camera opened: {actual_width}x{actual_height} @ {actual_fps}fps")
        
        if (actual_width, actual_height) != self.resolution:
            print(f"  ⚠ Requested {self.resolution[0]}x{self.resolution[1]}, got {actual_width}x{actual_height}")
    
    def read_frame(self):
        """Read single frame"""
        if self.cap is None:
            raise RuntimeError("Camera not opened")
        
        ret, frame = self.cap.read()
        
        if not ret:
            return None
        
        return frame
    
    def close(self):
        """Release camera"""
        if self.cap is not None:
            self.cap.release()


if __name__ == "__main__":
    """Demo: Test inference on static image or camera"""
    
    import sys
    
    print("Sentin-AI Flame Detection Inference")
    print("=" * 50)
    
    model_path = "cortex/flame_detection/models/mobilenet_flame_v1.tflite"
    
    # Check if model exists
    if not Path(model_path).exists():
        print("⚠ Model not found. Please train the model first:")
        print("  python cortex/flame_detection/train.py")
        sys.exit(1)
    
    # Initialize inference
    detector = FlameInference(model_path)
    
    # Test with camera
    print("\nStarting camera test...")
    camera = CameraCapture()
    
    try:
        camera.open()
        
        print("Press 'q' to quit")
        
        while True:
            frame = camera.read_frame()
            
            if frame is None:
                break
            
            # Run detection
            annotated, result = detector.detect_with_visualization(frame)
            
            # Display
            cv2.imshow("Sentin-AI Flame Detection", annotated)
            
            if result['flame_detected']:
                print(f"🔥 FLAME DETECTED! Confidence: {result['confidence']:.2%}")
            
            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        camera.close()
        cv2.destroyAllWindows()
