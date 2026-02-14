# Google Colab Training Instructions

## 1. Prepare Environment
Run this cell first to check GPU and install dependencies.
```python
# Check GPU
!nvidia-smi

# Install Ultralytics
!pip install ultralytics
from ultralytics import YOLO
import os
```

## 2. Upload Dataset
Upload the `yolo_dataset.zip` file to the Colab environment (drag & drop to the file browser on the left).

## 3. Unzip Dataset
```python
!unzip -q yolo_dataset.zip -d .
```

## 4. Train Model
Run the training command.
**Note:** `yolo11n.pt` will be downloaded automatically.
We disable default augmentations (`mosaic=0.0`, etc.) as planned.

```python
model = YOLO("yolo11n.pt")

results = model.train(
    data="yolo_dataset/data.yaml",
    epochs=50,
    imgsz=640,
    batch=16,
    name="wall_e_yolo11n",
    device=0, # Use T4 GPU
    patience=10,
    save=True,
    verbose=True,
    # Disable Default Augmentations
    mosaic=0.0,
    mixup=0.0,
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.0,
    translate=0.0,
    scale=0.0,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.0,
)
```

## 5. Download Weights
After training, download the best model weights.
```python
from google.colab import files
files.download('runs/detect/wall_e_yolo11n/weights/best.pt')
```
