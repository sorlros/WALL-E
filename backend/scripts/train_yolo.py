from ultralytics import YOLO
import os

def train_model():
    # 1. Load the model
    # 'yolo11n.pt' will be automatically downloaded if not present.
    # Note: Ensure you have the latest 'ultralytics' package installed that supports YOLO11.
    # If YOLO11 is not yet available in your version, use 'yolov8n.pt'.
    model = YOLO("yolo11n.pt")  

    # 2. Train the model
    # data: Path to the data.yaml file we created
    # epochs: Number of training epochs (50-100 is usually good for start)
    # imgsz: Image size (640 is standard)
    # batch: Batch size (adjust based on GPU memory, -1 for auto)
    # device: '0' for GPU, 'mps' for Mac M1/M2/M3, 'cpu' for CPU
    results = model.train(
        data="datasets/yolo_dataset4_gray/data.yaml", # Default to Gray dataset v4
        epochs=100,             # Increased epochs
        patience=15,            # Early stopping
        imgsz=640,              # Or 1280 if GPU allows
        batch=16,
        project="wall-e-crack",
        name="yolov11n-strict-aug-gray",
        device="mps",           # Use 'mps' for Mac, change to 0 for Colab
        
        # --- 1. Strictly Disable All Geometry/Color Augmentations ---
        hsv_h=0.0, hsv_s=0.0, hsv_v=0.0,
        degrees=0.0, translate=0.0, scale=0.0,
        shear=0.0, perspective=0.0, 
        flipud=0.0, fliplr=0.0,
        
        # --- 2. Disable Mosaic & Advanced Transforms ---
        mosaic=0.0,      
        mixup=0.0,       
        copy_paste=0.0,  
        erasing=0.0,     

        # --- 3. Other Settings ---
        crop_fraction=1.0, # Keep original aspect ratio
        rect=True,         # Rectangular training (important for non-square images)
        cache=True,        # Cache images for speed
        exist_ok=True,
        verbose=True,
    )

    # 3. Validate
    # Evaluate the model's performance on the validation set
    metrics = model.val()
    print(f"mAP50-95: {metrics.box.map}")

    # 4. Export (Optional)
    # Export to other formats like ONNX, CoreML, etc.
    # model.export(format="onnx")

if __name__ == "__main__":
    # Ensure current working directory is the project root
    print(f"Starting training on device: mps (Mac Metal Performance Shaders)")
    train_model()
