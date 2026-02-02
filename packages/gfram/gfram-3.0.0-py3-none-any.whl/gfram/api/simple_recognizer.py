"""
GFRAM Simple Recognizer
=======================

Simplified face recognizer for end users.

NO save/load methods - model is downloaded automatically.
NO complex parameters - everything is automatic.

Author: Ortiqova F.S.
"""

import torch
import numpy as np
from pathlib import Path
from typing import Union, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SimpleRecognizer:
    """
    Simple Face Recognizer.
    
    - Auto downloads model from server
    - Auto sends data for training
    - Always uses hybrid matching
    - No save/load needed
    
    Usage:
        recognizer = SimpleRecognizer()
        recognizer.add("John", "john.jpg")
        result = recognizer.recognize("test.jpg")
    """
    
    def __init__(self):
        """Initialize recognizer with auto model download."""
        # Device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"GFRAM initialized on {self.device}")
        
        # Lazy loading - components created on first use
        self._detector = None
        self._extractor = None
        self._normalizer = None
        self._model = None
        self._geo_index = None
        self._deep_index = None
        
        # Person database
        self._persons = {}  # name -> person_id
        self._person_names = {}  # person_id -> name
        self._num_persons = 0
        self._total_recognitions = 0
        
        logger.info("GFRAM ready!")
    
    @property
    def detector(self):
        """Lazy load face detector"""
        if self._detector is None:
            from ..detectors import FaceDetector, LandmarkNormalizer
            self._detector = FaceDetector()
            self._normalizer = LandmarkNormalizer()
        return self._detector
    
    @property
    def normalizer(self):
        """Lazy load normalizer"""
        if self._normalizer is None:
            from ..detectors import LandmarkNormalizer
            self._normalizer = LandmarkNormalizer()
        return self._normalizer
    
    @property
    def extractor(self):
        """Lazy load feature extractor"""
        if self._extractor is None:
            from ..geometry.features import GeometricFeatureExtractor
            self._extractor = GeometricFeatureExtractor()
        return self._extractor
    
    @property
    def model(self):
        """Lazy load model with auto-download"""
        if self._model is None:
            self._model = self._load_model()
        return self._model
    
    @property
    def geo_index(self):
        """Lazy load geometric index"""
        if self._geo_index is None:
            from ..matching import FaceIndex
            self._geo_index = FaceIndex(metric='cosine')
        return self._geo_index
    
    @property
    def deep_index(self):
        """Lazy load deep index"""
        if self._deep_index is None:
            from ..matching import FaceIndex
            self._deep_index = FaceIndex(metric='cosine')
        return self._deep_index
    
    def _load_model(self):
        """Load model - auto downloads from server if needed"""
        from ..models import create_geometric_transformer
        from ..cloud.model_loader import ensure_model_available
        
        # Create model
        model = create_geometric_transformer(config_name='base', num_classes=None)
        model.to(self.device)
        model.eval()
        
        # Try to load pretrained weights
        try:
            model_path = ensure_model_available()
            
            if model_path and model_path.exists():
                checkpoint = torch.load(model_path, map_location=self.device)
                
                if 'model_state_dict' in checkpoint:
                    model.load_state_dict(checkpoint['model_state_dict'], strict=False)
                    logger.info(f"✅ Model loaded: {model_path.name}")
                else:
                    logger.warning("⚠️ No model_state_dict in checkpoint")
            else:
                logger.warning("⚠️ Model not found, using random initialization")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load model: {e}")
        
        return model
    
    def _load_image(self, image: Union[str, np.ndarray]) -> np.ndarray:
        """Load image from path or return as-is"""
        if isinstance(image, str):
            import cv2
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"Could not load image: {image}")
            return img
        return image
    
    def _extract_features(self, image: np.ndarray) -> Optional[Dict]:
        """Extract face features from image"""
        # Detect face
        faces = self.detector.detect(image)
        
        if not faces:
            return None
        
        if len(faces) > 1:
            logger.warning(f"Multiple faces detected ({len(faces)}), using first")
        
        face = faces[0]
        landmarks = face['landmarks']
        
        # Normalize landmarks
        landmarks = self.normalizer.normalize(landmarks)
        
        # Extract geometric features
        geo_features = self.extractor.extract(landmarks)
        
        # Get deep embedding
        with torch.no_grad():
            landmarks_tensor = torch.FloatTensor(landmarks).unsqueeze(0).to(self.device)
            deep_embedding = self.model(landmarks_tensor)
            
            if isinstance(deep_embedding, tuple):
                deep_embedding = deep_embedding[0]
            
            deep_embedding = deep_embedding.cpu().numpy().squeeze()
        
        return {
            'landmarks': landmarks,
            'geo_features': geo_features,
            'deep_embedding': deep_embedding,
            'bbox': face.get('bbox')
        }
    
    def add(self, name: str, image: Union[str, np.ndarray]) -> Dict:
        """
        Add a person for recognition.
        
        Args:
            name: Person's name
            image: Image path or numpy array
        
        Returns:
            Result dict
        """
        logger.info(f"Adding person: {name}")
        
        # Load image
        img = self._load_image(image)
        
        # Extract features
        features = self._extract_features(img)
        
        if features is None:
            return {
                'success': False,
                'error': 'No face detected in image'
            }
        
        # Check if person already exists
        if name in self._persons:
            person_id = self._persons[name]
            logger.info(f"Updating existing person: {name}")
        else:
            person_id = self._num_persons
            self._persons[name] = person_id
            self._person_names[person_id] = name
            self._num_persons += 1
        
        # Add to indices
        metadata = {'person_id': person_id, 'name': name}
        
        self.geo_index.add(features['geo_features'], metadata=metadata)
        self.deep_index.add(features['deep_embedding'], metadata=metadata)
        
        # Send to server for global model training
        self._send_to_server(name, features)
        
        logger.info(f"✅ Added: {name} (ID: {person_id})")
        
        return {
            'success': True,
            'name': name,
            'person_id': person_id
        }
    
    def _send_to_server(self, name: str, features: Dict):
        """Send data to server for training"""
        try:
            from ..cloud.server_client import contribute
            
            result = contribute(
                person_id=name,
                landmarks=features['landmarks'],
                geometric_features=features['geo_features'],
                embedding=features['deep_embedding']
            )
            
            if result.get('status') == 'success':
                logger.debug(f"Data sent to server for training")
            else:
                logger.debug(f"Server contribution: {result.get('status', 'unknown')}")
                
        except Exception as e:
            # Don't fail if server is unavailable
            logger.debug(f"Could not send to server: {e}")
    
    def recognize(self, image: Union[str, np.ndarray]) -> Dict:
        """
        Recognize a person in image.
        
        Always uses hybrid matching (30% geometric + 70% deep).
        
        Args:
            image: Image path or numpy array
        
        Returns:
            Recognition result dict
        """
        # Load image
        img = self._load_image(image)
        
        # Extract features
        features = self._extract_features(img)
        
        if features is None:
            return {
                'name': 'Unknown',
                'confidence': 0.0,
                'recognized': False,
                'error': 'No face detected'
            }
        
        self._total_recognitions += 1
        
        # No persons added yet
        if self._num_persons == 0:
            return {
                'name': 'Unknown',
                'confidence': 0.0,
                'recognized': False,
                'error': 'No persons in database'
            }
        
        # Search in both indices (hybrid approach)
        geo_matches = self.geo_index.search(features['geo_features'], k=5)
        deep_matches = self.deep_index.search(features['deep_embedding'], k=5)
        
        # Fuse results (30% geo + 70% deep)
        final_match = self._fuse_results(geo_matches, deep_matches)
        
        if final_match and final_match['score'] >= 0.7:
            return {
                'name': final_match['name'],
                'confidence': float(final_match['score']),
                'recognized': True,
                'person_id': final_match['person_id'],
                'bbox': features.get('bbox')
            }
        else:
            return {
                'name': 'Unknown',
                'confidence': float(final_match['score']) if final_match else 0.0,
                'recognized': False,
                'bbox': features.get('bbox')
            }
    
    def _fuse_results(
        self, 
        geo_results: List[Dict], 
        deep_results: List[Dict]
    ) -> Optional[Dict]:
        """Fuse geometric and deep results"""
        if not geo_results and not deep_results:
            return None
        
        scores = {}
        
        # Collect geometric scores
        for result in geo_results:
            pid = result['metadata']['person_id']
            scores[pid] = {
                'geo_score': result['score'],
                'deep_score': 0.0,
                'name': result['metadata']['name']
            }
        
        # Collect deep scores
        for result in deep_results:
            pid = result['metadata']['person_id']
            if pid in scores:
                scores[pid]['deep_score'] = result['score']
            else:
                scores[pid] = {
                    'geo_score': 0.0,
                    'deep_score': result['score'],
                    'name': result['metadata']['name']
                }
        
        # Calculate final scores (30% geo + 70% deep)
        best_match = None
        best_score = -1
        
        for pid, data in scores.items():
            final_score = 0.3 * data['geo_score'] + 0.7 * data['deep_score']
            
            if final_score > best_score:
                best_score = final_score
                best_match = {
                    'person_id': pid,
                    'name': data['name'],
                    'score': final_score,
                    'geo_score': data['geo_score'],
                    'deep_score': data['deep_score']
                }
        
        return best_match
    
    def list_persons(self) -> List[str]:
        """List all added persons"""
        return list(self._persons.keys())
    
    def remove(self, name: str) -> bool:
        """Remove a person"""
        if name not in self._persons:
            return False
        
        # Note: We can't easily remove from FAISS index
        # So we just mark as removed in our database
        person_id = self._persons.pop(name)
        del self._person_names[person_id]
        
        logger.info(f"Removed: {name}")
        return True
    
    def clear(self):
        """Clear all persons"""
        self._persons.clear()
        self._person_names.clear()
        self._num_persons = 0
        
        # Reset indices
        self._geo_index = None
        self._deep_index = None
        
        logger.info("Cleared all persons")
    
    def stats(self) -> Dict:
        """Get statistics"""
        return {
            'persons': len(self._persons),
            'total_recognitions': self._total_recognitions,
            'device': str(self.device)
        }
