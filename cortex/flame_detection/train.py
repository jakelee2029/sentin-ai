"""
Training Script for Flame Detection Model

Train MobileNetV2-based CNN on flame/no-flame dataset
"""

import tensorflow as tf
from tensorflow import keras
import numpy as np
from pathlib import Path
import argparse
import json

from model import FlameDetectionModel, create_data_augmentation


def create_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    batch_size=32,
    image_size=(224, 224),
    augment=True
):
    """
    Create training and validation datasets
    
    Expected directory structure:
        data_dir/
            flame/
                img1.jpg
                img2.jpg
                ...
            no_flame/
                img1.jpg
                img2.jpg
                ...
    """
    
    # Data augmentation
    if augment:
        data_augmentation = create_data_augmentation()
    
    # Training dataset
    train_ds = keras.preprocessing.image_dataset_from_directory(
        data_dir,
        validation_split=validation_split,
        subset="training",
        seed=42,
        image_size=image_size,
        batch_size=batch_size
    )
    
    # Validation dataset
    val_ds = keras.preprocessing.image_dataset_from_directory(
        data_dir,
        validation_split=validation_split,
        subset="validation",
        seed=42,
        image_size=image_size,
        batch_size=batch_size
    )
    
    # Apply augmentation to training set
    if augment:
        train_ds = train_ds.map(
            lambda x, y: (data_augmentation(x, training=True), y),
            num_parallel_calls=tf.data.AUTOTUNE
        )
    
    # Optimize performance
    train_ds = train_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    
    return train_ds, val_ds


def train_model(
    data_dir,
    output_dir="cortex/flame_detection/models",
    epochs=10,
    fine_tune_epochs=5,
    batch_size=32
):
    """
    Train flame detection model
    
    Args:
        data_dir: Path to training data
        output_dir: Where to save trained model
        epochs: Initial training epochs
        fine_tune_epochs: Fine-tuning epochs
        batch_size: Batch size
    """
    
    print("Sentin-AI Model Training")
    print("=" * 50)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load datasets
    print(f"\n1. Loading dataset from: {data_dir}")
    train_ds, val_ds = create_dataset_from_directory(
        data_dir,
        batch_size=batch_size
    )
    
    # Build model
    print("\n2. Building model...")
    flame_model = FlameDetectionModel()
    model = flame_model.compile_model()
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=3,
            restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=2
        ),
        keras.callbacks.ModelCheckpoint(
            str(output_path / "checkpoint.h5"),
            save_best_only=True,
            monitor='val_accuracy'
        )
    ]
    
    # Phase 1: Train with frozen base
    print(f"\n3. Training (frozen base) - {epochs} epochs...")
    history1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks
    )
    
    # Phase 2: Fine-tuning
    print(f"\n4. Fine-tuning (unfrozen layers) - {fine_tune_epochs} epochs...")
    flame_model.fine_tune(unfreeze_layers=20)
    
    history2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=fine_tune_epochs,
        callbacks=callbacks
    )
    
    # Evaluate
    print("\n5. Evaluating model...")
    results = model.evaluate(val_ds)
    
    print("\nFinal Metrics:")
    print(f"  Loss: {results[0]:.4f}")
    print(f"  Accuracy: {results[1]:.4%}")
    print(f"  Precision: {results[2]:.4%}")
    print(f"  Recall: {results[3]:.4%}")
    
    # Save Keras model
    keras_path = output_path / "flame_detection.h5"
    model.save(keras_path)
    print(f"\n✓ Keras model saved: {keras_path}")
    
    # Convert to TFLite
    print("\n6. Converting to TensorFlow Lite...")
    tflite_path = output_path / "mobilenet_flame_v1.tflite"
    flame_model.convert_to_tflite(str(tflite_path))
    
    # Save training history
    history_combined = {
        'phase1': {k: [float(v) for v in vals] for k, vals in history1.history.items()},
        'phase2': {k: [float(v) for v in vals] for k, vals in history2.history.items()},
        'final_metrics': {
            'loss': float(results[0]),
            'accuracy': float(results[1]),
            'precision': float(results[2]),
            'recall': float(results[3])
        }
    }
    
    history_path = output_path / "training_history.json"
    with open(history_path, 'w') as f:
        json.dump(history_combined, f, indent=2)
    
    print(f"\n✓ Training complete!")
    print(f"  Models saved to: {output_path}")
    print(f"  TFLite model ready for deployment: {tflite_path}")
    
    return model, history_combined


def validate_model(model_path, test_data_dir):
    """
    Validate trained model on test set
    
    Args:
        model_path: Path to saved model
        test_data_dir: Path to test data
    """
    print("Validating model...")
    
    # Load model
    model = keras.models.load_model(model_path)
    
    # Load test data
    test_ds = keras.preprocessing.image_dataset_from_directory(
        test_data_dir,
        image_size=(224, 224),
        batch_size=32
    )
    
    # Evaluate
    results = model.evaluate(test_ds)
    
    print("\nTest Set Results:")
    print(f"  Accuracy: {results[1]:.4%}")
    print(f"  Precision: {results[2]:.4%}")
    print(f"  Recall: {results[3]:.4%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Sentin-AI flame detection model")
    parser.add_argument("--data", type=str, help="Path to training data directory")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")
    parser.add_argument("--fine-tune", type=int, default=5, help="Fine-tuning epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--validate", action="store_true", help="Run validation mode")
    parser.add_argument("--test-data", type=str, help="Path to test data (for validation)")
    
    args = parser.parse_args()
    
    if args.validate:
        if not args.test_data:
            print("Error: --test-data required for validation")
        else:
            validate_model(
                "cortex/flame_detection/models/flame_detection.h5",
                args.test_data
            )
    else:
        if not args.data:
            print("Error: --data required for training")
            print("\nExample usage:")
            print("  python train.py --data /path/to/flame_dataset --epochs 10")
        else:
            train_model(
                args.data,
                epochs=args.epochs,
                fine_tune_epochs=args.fine_tune,
                batch_size=args.batch_size
            )
