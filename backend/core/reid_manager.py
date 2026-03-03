import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import cv2
import logging
from typing import List, Tuple
from collections import deque

logger = logging.getLogger("api")

class ReIDManager:
    def __init__(self, threshold: float = 0.85, max_cache_size: int = 50):
        """
        Initializes the Re-Identification Manager using MobileNetV3-small.
        
        Args:
            threshold: Cosine similarity threshold to consider two images as duplicates (0.0 to 1.0)
            max_cache_size: Maximum number of recent embeddings to keep in memory per mission
        """
        self.threshold = threshold
        self.max_cache_size = max_cache_size
        
        # In-memory cache: Dictionary mapping mission_id -> deque of (detection_id, embedding_vector, frame_id, track_id)
        self.embedding_cache = {} 
        
        # Determine device (CPU or MPS for Mac, CUDA for Nvidia)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        logger.info(f"ReIDManager initializing on device: {self.device}")
        
        try:
            # Load pre-trained MobileNetV3-small structure (without downloading weights)
            logger.info("Loading MobileNetV3-small structure for Re-ID...")
            self.model = models.mobilenet_v3_small(weights=None)
            
            # Load local offline weights
            import os
            local_weights_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "models", 
                "mobilenet_v3_small-047dcff4.pth"
            )
            logger.info(f"Loading local weights from: {local_weights_path}")
            self.model.load_state_dict(torch.load(local_weights_path, map_location=self.device))
            
            # Remove the final classification layer (we only want the 576-d feature vector)
            # MobileNetV3's classifier is a Sequential block. We replace it with an Identity layer.
            self.model.classifier = torch.nn.Identity()
            
            self.model.to(self.device)
            self.model.eval() # Set to evaluation mode
            
            logger.info("MobileNetV3-small loaded successfully for Re-ID.")
        except Exception as e:
            logger.error(f"Failed to load Re-ID model: {e}")
            self.model = None

        # Standard ImageNet normalization used by torchvision models
        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def get_embedding(self, cv_image: np.ndarray) -> np.ndarray:
        """
        Extracts a 576-dimensional feature vector from an OpenCV image (BGR).
        """
        if self.model is None or cv_image is None or cv_image.size == 0:
            return None
            
        try:
            # Convert BGR (OpenCV) to RGB (PIL)
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # Preprocess the image
            input_tensor = self.preprocess(pil_image)
            input_batch = input_tensor.unsqueeze(0).to(self.device) # Add batch dimension
            
            # Extract features without computing gradients
            with torch.no_grad():
                features = self.model(input_batch)
                
            # Convert back to numpy array on CPU, flatten to 1D
            embedding = features.squeeze().cpu().numpy()
            
            # Normalize the embedding vector for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
                
            return embedding
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}")
            return None

    def calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculates the Cosine Similarity between two normalized L2 embeddings.
        Since they are normalized, cosine similarity is just the dot product.
        """
        if emb1 is None or emb2 is None:
            return 0.0
        return float(np.dot(emb1, emb2))

    def is_duplicate(self, mission_id: int, new_embedding: np.ndarray, frame_id: int, track_id: int) -> Tuple[bool, float, int]:
        """
        Checks if the new_embedding is a duplicate of any recently saved embeddings for the mission.
        Incorporates Spatial & Temporal awareness to prevent false positives in the same frame.
        
        Returns:
            (is_duplicate_boolean, max_similarity_score, matched_detection_id)
        """
        if new_embedding is None:
            return False, 0.0, None
            
        if mission_id not in self.embedding_cache:
            self.embedding_cache[mission_id] = deque(maxlen=self.max_cache_size)
            return False, 0.0, None
            
        cache = self.embedding_cache[mission_id]
        max_sim = 0.0
        matched_id = None
        
        for cached_detection_id, cached_emb, cached_frame_id, cached_track_id in cache:
            # 1. Temporal filter: If YOLO ByteTrack ID is exactly the same, it's definitely the same object.
            # No need to do cosine similarity.
            if track_id is not None and cached_track_id == track_id:
                return True, 1.0, cached_detection_id # 100% match by tracking ID
            
            # 2. Spatial filter: If the YOLO bounding box was found in the exact same frame (time), 
            # it is physically impossible to be the same object even if they look identical. Skip comparison.
            if cached_frame_id == frame_id:
                continue
                
            sim = self.calculate_similarity(new_embedding, cached_emb)
            if sim > max_sim:
                max_sim = sim
                matched_id = cached_detection_id
                
        is_dup = max_sim >= self.threshold
        return is_dup, max_sim, matched_id if is_dup else None

    def add_to_cache(self, mission_id: int, detection_id: int, embedding: np.ndarray, frame_id: int, track_id: int):
        """
        Adds a new embedding and its spatial/temporal metadata to the cache for future comparisons.
        """
        if embedding is None:
            return
            
        if mission_id not in self.embedding_cache:
            self.embedding_cache[mission_id] = deque(maxlen=self.max_cache_size)
            
        self.embedding_cache[mission_id].append((detection_id, embedding, frame_id, track_id))
        
    def clear_mission_cache(self, mission_id: int):
        """
        Clears the memory cache for a specific mission.
        """
        if mission_id in self.embedding_cache:
            del self.embedding_cache[mission_id]
            logger.info(f"Re-ID cache cleared for mission {mission_id}")
