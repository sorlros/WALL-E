import cv2
import os
import sys

# Add core to path so we can import reid_manager
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
from reid_manager import ReIDManager

def run_test():
    print("Initializing ReIDManager...")
    manager = ReIDManager(threshold=0.85)
    
    # Pick a random saved image to act as a crop
    img_path = "storage/images/2026-02-16/183c6204-e4a6-439e-a658-54bcd726de7b.jpg"
    print(f"Loading test image: {img_path}")
    
    img1 = cv2.imread(img_path)
    if img1 is None:
        print("Failed to load image.")
        return
        
    # Create a slightly shifted/cropped version of img1 to simulate drone movement
    h, w, _ = img1.shape
    img2 = img1[int(h*0.05):int(h*0.95), int(w*0.05):int(w*0.95)] # 5% crop
    
    # Also load a completely different image to verify it rejects distinct cracks
    img_diff_path = "storage/images/2026-02-17/dfb1f987-904f-43d7-b80a-e1bc4b060f81.jpg"
    img3 = cv2.imread(img_diff_path)
    
    print("Extracting embeddings...")
    emb1 = manager.get_embedding(img1)
    emb2 = manager.get_embedding(img2)
    emb3 = manager.get_embedding(img3) if img3 is not None else None
    
    print("\n--- Results ---")
    sim_same = manager.calculate_similarity(emb1, emb2)
    print(f"1. Similarity between original and slightly cropped (shifted) version: {sim_same:.4f}")
    if sim_same >= manager.threshold:
        print("   ✅ SUCCESS: Correctly identified as duplicate!")
    else:
        print("   ❌ FAIL: Failed to identify duplicate.")
        
    if emb3 is not None:
        sim_diff = manager.calculate_similarity(emb1, emb3)
        print(f"2. Similarity between two completely different images: {sim_diff:.4f}")
        if sim_diff < manager.threshold:
            print("   ✅ SUCCESS: Correctly rejected distinct image!")
        else:
            print("   ❌ FAIL: Incorrectly identified distinct image as duplicate.")

if __name__ == "__main__":
    run_test()
