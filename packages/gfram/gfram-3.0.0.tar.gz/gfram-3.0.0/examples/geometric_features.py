#!/usr/bin/env python3
"""
GFRAM Geometric Features Example
================================

This example demonstrates how to extract geometric features
from facial landmarks without using the full recognition pipeline.

Usage:
    python geometric_features.py

Requirements:
    pip install gfram numpy
"""

import numpy as np


def main():
    print("=" * 60)
    print("🔷 GFRAM Geometric Features Example")
    print("=" * 60)
    
    # Import feature extractor
    from gfram.geometry.features import GeometricFeatureExtractor
    
    # Create extractor (478 landmarks with iris features)
    extractor = GeometricFeatureExtractor(num_landmarks=478)
    
    print(f"\n📐 Feature Categories:")
    print(f"   - Euclidean features: 30")
    print(f"   - Differential features: 40")
    print(f"   - Topological features: 20")
    print(f"   - Statistical features: 30")
    print(f"   - Symmetry features: 15")
    print(f"   - Graph features: 15")
    print(f"   - Iris features: 3")
    print(f"   ─────────────────────")
    print(f"   Total: {extractor.get_feature_count()} features")
    
    # Generate sample landmarks (in real use, get from MediaPipe)
    print(f"\n🎲 Generating sample 478 landmarks...")
    np.random.seed(42)
    landmarks = np.random.randn(478, 3).astype(np.float32)
    landmarks = landmarks * 0.1 + 0.5  # Normalize to [0.4, 0.6] range
    
    print(f"   Shape: {landmarks.shape}")
    print(f"   Range: [{landmarks.min():.3f}, {landmarks.max():.3f}]")
    
    # Extract features
    print(f"\n⚙️ Extracting geometric features...")
    features = extractor.extract(landmarks)
    
    print(f"\n📊 Extracted Features:")
    print(f"   Shape: {features.shape}")
    print(f"   Type: {features.dtype}")
    print(f"   Range: [{features.min():.4f}, {features.max():.4f}]")
    print(f"   Mean: {features.mean():.4f}")
    print(f"   Std: {features.std():.4f}")
    
    # Show feature names
    names = extractor.get_feature_names()
    print(f"\n📋 First 10 feature names:")
    for i, name in enumerate(names[:10]):
        print(f"   {i+1}. {name}: {features[i]:.4f}")
    
    # Iris features (last 3)
    print(f"\n👁️ Iris features:")
    iris_names = names[-3:]
    iris_values = features[-3:]
    for name, val in zip(iris_names, iris_values):
        print(f"   {name}: {val:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ Feature extraction complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
