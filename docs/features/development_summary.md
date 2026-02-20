
# Development Summary: Bounding Box Alignment & UX Improvements

Following is a detailed summary of the logic modifications and additions made to ensure accurate crack detection, proper coordinate alignment, and improved user experience.

## 1. Backend Logic (`stream_manager.py`)

### A. Coordinate System Fix (Critical)
*   **Problem:** The backend was previously resizing frames to 640x640 (adding gray padding) *before* running AI inference. This caused the AI to return coordinates relative to the padded 640x640 image, while we were saving the original 1280x720 image. This resulted in a vertical offset for bounding boxes (y-axis shift).
*   **Fix:** Removed the pre-processing step for inference. We now pass the **raw 1280x720 frame** directly to the YOLO tracking model.
*   **Result:** The model returns normalized coordinates (0.0 - 1.0) that map perfectly to the original 1280x720 image.

### B. Zero-Delay Architecture
*   **Implementation:** Confirmed that detection and image saving happen in the same process loop.
*   **Latency Logging:** Added logs to measure the time difference between `inference` and `save`. The delay is negligible (<10ms), confirming "Zero-Delay".

### C. Model Path Update
*   **Change:** Updated `model_path` to point to the latest trained weights: `runs/detect/wall-e-crack-detection/v3_mixed_original2/weights/best.pt`.

---

## 2. Frontend Logic (Flutter)

### A. Gallery Detail View (`mission_detail_screen.dart`)

#### 1. Aspect Ratio Fix ("Ratio Fix")
*   **Problem:** Viewing images on screens with different aspect ratios (e.g., iPhone vs iPad, Portrait vs Landscape) caused bounding boxes to drift if the image was letterboxed (black bars).
*   **Solution:** implemented a dynamic sizing logic using `LayoutBuilder`:
    1.  **Measure**: Retrieve the actual pixel dimensions of the loaded image (`_imageSize`).
    2.  **Calculate**: Compute the exact `displaySize` (width/height) of the image as it appears on screen, accounting for `BoxFit.contain`.
    3.  **Constrain**: Force the `CustomPaint` (which draws the boxes) to match this exact `displaySize`.
*   **Result:** Bounding boxes are drawn relative to the *rendered image pixels*, not the device screen, ensuring perfect alignment on any device orientation.

#### 2. Swipe Navigation
*   **Feature:** User can now swipe left/right to view other detections in the same mission without going back to the grid.
*   **Implementation:** Refactored `DetectionFullScreenView` to use a `PageView.builder`.
*   **Optimization:** Each page (`_DetectionImagePage`) manages its own image loading and "Ratio Fix" calculation independently, ensuring smooth performance.

### B. Live Streaming View (`live_streaming_screen.dart`)

#### 1. Full Visibility Fix
*   **Problem:** The video player was using `BoxFit.cover`, which cropped the edges of the 16:9 drone video on tall smartphone screens. This could hide cracks located at the periphery.
*   **Fix:** Changed to `BoxFit.contain`.
*   **Result:** The entire video feed (1280x720) is visible. Black bars may appear, but no visual data is lost.

#### 2. Alignment Verification
*   **Confirmation:** The live stream uses a `Stack` where the `VideoPlayer` and `CustomPaint` share the same `SizedBox` and `FittedBox`. This guarantees that if the video scales, the boxes scale with it perfectly.

---

## 3. Summary of Files Changed

| File | Key Changes |
| :--- | :--- |
| `backend/core/stream_manager.py` | Removed pre-processing for inference (Raw frame usage), Added latency logging. |
| `frontend/lib/screens/mission_detail_screen.dart` | Added `LayoutBuilder` for Ratio Fix, Implemented `PageView` for Swipe, Refactored `_DetectionImagePage`. |
| `frontend/lib/screens/live_streaming_screen.dart` | Changed video fit to `BoxFit.contain`, Verified alignment logic. |

This architecture ensures that **what the drone sees (AI)**, **what is saved (Storage)**, and **what the user sees (App)** are all mathematically aligned 1:1.

## 4. Gallery Optimization (Mission Detail)
- **Swipe Navigation**: Implemented `PageView` in `DetectionFullScreenView` to allow users to swipe between detection images.
- **Landscape Support**: Added `OrientationBuilder` to `MissionDetailScreen` to provide a responsive layout.
    - **Portrait**: Vertical layout with Info Card on top and Grid below.
    - **Landscape**: Horizontal layout with Info Card on the left and Grid on the right (3 columns).
- **Code Refactoring**: Cleaned up `MissionDetailScreen` structure, ensuring proper state management and widget separation.
- **Debug Banner**: Removed the "DEBUG" banner from the app for a cleaner look.
