"""
Sentin-AI Flame Detection CNN Model

MobileNetV2-based architecture optimized for edge deployment
on Snapdragon processor with TensorFlow Lite.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
import numpy as np

class FlameDetectionModel:
    """
    Lightweight CNN for real-time flame detection
    Based on MobileNetV2 with transfer learning
    """
    
    def __init__(self, input_shape=(224, 224, 3), num_classes=2):
        """
        Initialize flame detection model
        
        Args:
            input_shape: Input image dimensions (H, W, C)
            num_classes: Binary classification (flame/no-flame)
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = None
        
    def build_model(self):
        """Build transfer learning model from MobileNetV2"""
        
        # Load pre-trained MobileNetV2 (frozen base)
        base_model = MobileNetV2(
            input_shape=self.input_shape,
            include_top=False,
            weights='imagenet'
        )
        
        # Freeze base model for transfer learning
        base_model.trainable = False
        
        # Build classification head
        inputs = keras.Input(shape=self.input_shape)
        
        # Preprocessing
        x = layers.Rescaling(1./255)(inputs)
        
        # Base model
        x = base_model(x, training=False)
        
        # Global pooling
        x = layers.GlobalAveragePooling2D()(x)
        
        # Dropout for regularization
        x = layers.Dropout(0.2)(x)
        
        # Dense layers
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.1)(x)
        
        # Output layer
        outputs = layers.Dense(
            self.num_classes, 
            activation='softmax',
            name='flame_classifier'
        )(x)
        
        self.model = keras.Model(inputs, outputs)
        
        return self.model
    
    def compile_model(self, learning_rate=0.001):
        """Compile model with optimizer and loss"""
        
        if self.model is None:
            self.build_model()
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return self.model
    
    def fine_tune(self, unfreeze_layers=20):
        """
        Fine-tune the model by unfreezing top layers
        
        Args:
            unfreeze_layers: Number of top layers to unfreeze
        """
        if self.model is None:
            raise ValueError("Model must be built first")
        
        # Unfreeze the base model
        base_model = self.model.layers[2]  # MobileNetV2 layer
        base_model.trainable = True
        
        # Freeze all layers except the top ones
        for layer in base_model.layers[:-unfreeze_layers]:
            layer.trainable = False
        
        # Recompile with lower learning rate
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-5),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return self.model
    
    def convert_to_tflite(self, output_path):
        """
        Convert model to TensorFlow Lite for edge deployment
        
        Args:
            output_path: Path to save .tflite model
        """
        if self.model is None:
            raise ValueError("Model must be built first")
        
        # Convert to TFLite with optimization
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        # Apply optimizations for edge deployment
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Optional: Use float16 quantization for smaller size
        converter.target_spec.supported_types = [tf.float16]
        
        tflite_model = converter.convert()
        
        # Save to file
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        print(f"✓ TFLite model saved to: {output_path}")
        print(f"  Model size: {len(tflite_model) / 1024:.1f} KB")
        
        return output_path
    
    def get_summary(self):
        """Print model architecture summary"""
        if self.model is None:
            self.build_model()
        
        return self.model.summary()


def create_data_augmentation():
    """
    Create data augmentation pipeline for training
    """
    return keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
        layers.RandomBrightness(0.2),
        layers.RandomContrast(0.2),
    ])


def preprocess_image(image_path, target_size=(224, 224)):
    """
    Preprocess single image for inference
    
    Args:
        image_path: Path to image file
        target_size: Target dimensions
    
    Returns:
        Preprocessed image tensor
    """
    img = keras.preprocessing.image.load_img(
        image_path,
        target_size=target_size
    )
    img_array = keras.preprocessing.image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array


if __name__ == "__main__":
    # Demo: Build and display model
    print("Sentin-AI Flame Detection Model")
    print("=" * 50)
    
    model = FlameDetectionModel()
    model.compile_model()
    
    print("\nModel Architecture:")
    model.get_summary()
    
    print("\n✓ Model ready for training")
    print("  Next steps:")
    print("  1. Train on flame dataset (train.py)")
    print("  2. Convert to TFLite for deployment")
    print("  3. Deploy to Snapdragon processor")
