# Augmentation Experiment Log: v2 (Enhanced Contrast & Sharpness)
**Date**: 2026-02-14  
**Experiment Config**: `planned_v2.json`  
**Target Dataset**: `merged_dataset` (729 images)  
**Output Path**: `ai_research/augmentation_experiments/outputs/planned_v2`

## 1. Experiment Objectives
*   **Drone Inspection Conditions**: Simulate conditions typical of drone-based infrastructure inspection.
    *   **Distance**: ~3m
    *   **Angle**: Front-facing
    *   **Focus**: Vertical movement (scanning cracks on walls/columns)
*   **Quality Enhancement**: Improve defect visibility in suboptimal lighting/focus conditions.
    *   **Shadows**: Determine if CLAHE helps detect cracks in shadowed areas.
    *   **Blur/Shake**: Compensate for drone vibration and focus hunting.

## 2. Augmentation Pipeline Configuration
The following transformations were applied using `Albumentations`:

| Transform | Params | Reason |
| :--- | :--- | :--- |
| **Motion/GaussianBlur** (OneOf) | `p=0.3`, `blur_limit=7` | Simulates camera shake and focus errors during flight. |
| **ISONoise** | `p=0.3`, `intensity=[0.1, 0.5]` | Simulates sensor noise common in low-light/high-ISO scenarios. |
| **CLAHE** | `p=0.5`, `clip_limit=2.0` | **(Key)** Enhances local contrast to reveal cracks hiding in shadows. |
| **Sharpen** | `p=0.5`, `alpha=[0.2, 0.5]` | **(Key)** Enhances edge definitions of fine cracks against concrete texture. |
| **ShiftScaleRotate** | `shift_y=0.1`, `rotate=5` | Simulates slight vertical drift and stable flight (small rotation). |
| **Resize** | `512x512` | Optimized input size for YOLOv11n inference speed on embedded devices. |

## 3. Data Processing & Issues Resolved
### A. Class Unification
*   **Issue**: The `merged_dataset` contained two conflicting class IDs due to a typo in the merging process.
    *   `ID 0`: "defect" (479 images)
    *   `ID 1`: "defecct" (455 images) - *Typo*
*   **Resolution**: Implemented a forced re-mapping logic in `augmentation_template.py`.
    *   **Action**: All input annotations (whether ID 0 or 1) are forced to **Class ID 0 (Crack)**.
    *   **Result**: Generated annotations are clean and consistent.

### B. Format Conversion
*   **Input**: COCO JSON (Single file)
*   **Output**: YOLO `.txt` (Per image)
    *   Converted bounding box coordinates from `[x_min, y_min, w, h]` (pixel) to `[x_center, y_center, w, h]` (normalized 0-1).

## 4. Execution Results
*   **Total Images Processed**: 729
*   **Success Rate**: 100%
*   **Output Verification**:
    *   Images are resized to 512x512.
    *   Label files match image names.
    *   All label classes are `0`.

---
**Next Steps**:
1.  Split `planned_v2` output into `train` (80%) and `val` (20%) folders.
2.  Create `data.yaml` file pointing to these paths.
3.  Train YOLOv11n model using this dataset.
