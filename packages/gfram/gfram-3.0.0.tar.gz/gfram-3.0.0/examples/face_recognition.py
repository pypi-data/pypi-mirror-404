#!/usr/bin/env python3
"""
GFRAM Face Recognition Example
==============================

Complete example of face recognition workflow:
1. Add persons to database
2. Recognize unknown faces
3. Verify face pairs

Usage:
    python face_recognition.py --add person_name image.jpg
    python face_recognition.py --recognize image.jpg
    python face_recognition.py --verify image1.jpg image2.jpg

Requirements:
    pip install gfram opencv-python
"""

import argparse
import sys
import gfram


def add_person(name: str, image_path: str):
    """Add a person to the recognition database."""
    print(f"\n👤 Adding person: {name}")
    print(f"📷 Image: {image_path}")
    
    result = gfram.add(name, image_path)
    
    if result.get('success'):
        print(f"✅ Successfully added {name}")
        print(f"   Person ID: {result.get('person_id')}")
    else:
        print(f"❌ Failed to add: {result.get('error', 'Unknown error')}")
    
    return result


def recognize_face(image_path: str):
    """Recognize a face in an image."""
    print(f"\n🔍 Recognizing face in: {image_path}")
    
    result = gfram.recognize(image_path)
    
    if result.get('recognized'):
        print(f"✅ Recognized: {result['name']}")
        print(f"   Confidence: {result['confidence']:.2%}")
    else:
        print(f"❓ Unknown person")
        print(f"   Best match confidence: {result.get('confidence', 0):.2%}")
        if result.get('error'):
            print(f"   Note: {result['error']}")
    
    return result


def verify_faces(image1_path: str, image2_path: str):
    """Verify if two images show the same person."""
    print(f"\n🔐 Verifying faces:")
    print(f"   Image 1: {image1_path}")
    print(f"   Image 2: {image2_path}")
    
    # Use internal API for verification
    from gfram.api.simple_recognizer import SimpleRecognizer
    recognizer = SimpleRecognizer()
    
    # Extract features from both images
    import cv2
    
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)
    
    if img1 is None:
        print(f"❌ Could not load: {image1_path}")
        return None
    if img2 is None:
        print(f"❌ Could not load: {image2_path}")
        return None
    
    features1 = recognizer._extract_features(img1)
    features2 = recognizer._extract_features(img2)
    
    if features1 is None or features2 is None:
        print("❌ Could not detect face in one or both images")
        return None
    
    # Compute similarity
    import numpy as np
    
    geo_sim = 1.0 / (1.0 + np.linalg.norm(features1['geo_features'] - features2['geo_features']))
    deep_sim = np.dot(features1['deep_embedding'], features2['deep_embedding'])
    
    # Hybrid score (30% geo + 70% deep)
    hybrid_score = 0.3 * geo_sim + 0.7 * deep_sim
    
    is_same = hybrid_score >= 0.68  # Threshold
    
    print(f"\n📊 Verification Results:")
    print(f"   Geometric similarity: {geo_sim:.4f}")
    print(f"   Deep similarity: {deep_sim:.4f}")
    print(f"   Hybrid score: {hybrid_score:.4f}")
    print(f"   ────────────────────")
    
    if is_same:
        print(f"   ✅ SAME PERSON (score >= 0.68)")
    else:
        print(f"   ❌ DIFFERENT PERSONS (score < 0.68)")
    
    return {
        'same_person': is_same,
        'score': hybrid_score,
        'geo_similarity': geo_sim,
        'deep_similarity': deep_sim
    }


def list_all():
    """List all persons in database."""
    persons = gfram.list_persons()
    stats = gfram.stats()
    
    print(f"\n📋 Database Contents:")
    print(f"   Total persons: {stats['persons']}")
    print(f"   Device: {stats['device']}")
    
    if persons:
        print(f"\n   Persons:")
        for i, name in enumerate(persons, 1):
            print(f"   {i}. {name}")
    else:
        print(f"\n   (empty database)")


def main():
    parser = argparse.ArgumentParser(
        description='GFRAM Face Recognition Example',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python face_recognition.py --add John john.jpg
    python face_recognition.py --add Alice alice1.jpg alice2.jpg
    python face_recognition.py --recognize test.jpg
    python face_recognition.py --verify photo1.jpg photo2.jpg
    python face_recognition.py --list
    python face_recognition.py --clear
        """
    )
    
    parser.add_argument('--add', nargs='+', metavar=('NAME', 'IMAGE'),
                       help='Add person: --add NAME IMAGE [IMAGE2 ...]')
    parser.add_argument('--recognize', metavar='IMAGE',
                       help='Recognize face in image')
    parser.add_argument('--verify', nargs=2, metavar=('IMAGE1', 'IMAGE2'),
                       help='Verify if two images show same person')
    parser.add_argument('--list', action='store_true',
                       help='List all persons in database')
    parser.add_argument('--clear', action='store_true',
                       help='Clear the database')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🎯 GFRAM Face Recognition")
    print(f"   Version: {gfram.__version__}")
    print("=" * 50)
    
    if args.add:
        if len(args.add) < 2:
            print("❌ Usage: --add NAME IMAGE [IMAGE2 ...]")
            sys.exit(1)
        name = args.add[0]
        images = args.add[1:]
        for img in images:
            add_person(name, img)
    
    elif args.recognize:
        recognize_face(args.recognize)
    
    elif args.verify:
        verify_faces(args.verify[0], args.verify[1])
    
    elif args.list:
        list_all()
    
    elif args.clear:
        gfram.clear()
        print("\n✅ Database cleared")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
