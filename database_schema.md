# 🏗️ Wall-E Database Schema & Function Specification

This document outlines the database schema designed for Supabase (PostgreSQL) and the functional requirements for data handling in the Wall-E drone inspection service.

---

## 1. Database Schema (PostgreSQL)

### 1-1. Users (`auth.users` & `public.profiles`)
User authentication is managed by **Supabase Auth**. We extend user data using a `public.profiles` table.

#### `public.profiles`
| Column | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `uuid` (PK) | - | **Foreign Key** to `auth.users.id`. Ensures 1:1 mapping with auth user. |
| `username` | `text` | - | Unique username for display. |
| `full_name` | `text` | - | User's full name. |
| `avatar_url` | `text` | `NULL` | Profile picture URL (from Storage). |
| `created_at` | `timestamptz` | `now()` | Account creation timestamp. |

---

### 1-2. Missions (`public.missions`)
Represents a single drone inspection flight.
**Note:** Only **completed** missions are stored here (as requested, no `status` column needed).

| Column | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` (PK) | `generated always as identity` | Unique Mission ID. |
| `user_id` | `uuid` (FK) | - | **Foreign Key** to `public.profiles.id`. Who performed the mission. |
| `title` | `text` | - | Mission title (e.g., "Gangnam Finance Center Inspection"). |
| `description` | `text` | `NULL` | Optional details about the mission. |
| `location_name` | `text` | - | Name of the location/building (e.g., "COEX East Wing"). |
| `location_address`| `text` | - | Detailed address entered by user locally. |
| `captured_at` | `timestamptz` | `now()` | When the mission data was captured/uploaded. |
| `created_at` | `timestamptz` | `now()` | Record creation timestamp. |

---

### 1-3. Detections (`public.detections`)
Stores individual crack detections found during the mission.
Includes **GPS coordinates** and **bounding box data**.

| Column | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` (PK) | `generated always as identity` | Unique Detection ID. |
| `mission_id` | `bigint` (FK) | - | **Foreign Key** to `public.missions.id`. |
| `image_url` | `text` | - | URL of the **raw original image** stored in Supabase Storage. |
| `label` | `text` | `'crack'` | Type of defect detected (e.g., "crack", "spalling"). |
| `confidence` | `float` | - | AI model confidence score (0.0 ~ 1.0). |
| **`bbox`** | `jsonb` | - | Bounding box coordinates: `[x, y, w, h]` (normalized 0~1) or `[x1, y1, x2, y2]`. |
| `gps_lat` | `float` | `NULL` | Latitude of the drone at the moment of capture. |
| `gps_lng` | `float` | `NULL` | Longitude of the drone at the moment of capture. |
| `created_at` | `timestamptz` | `now()` | Detection timestamp. |

---

## 2. Functional Requirements

### 2-1. Data Flow
1.  **Drone Flight**: The user flies the drone and performs the inspection.
2.  **Real-time Inference**: The YOLOv11n model runs on the video stream.
3.  **Local Buffering**: Detections + GPS + Metadata are stored locally on the device (or backend buffer) during the flight.
4.  **Mission Completion**:
    *   User presses "Finish Mission".
    *   **Review Step (Optional)**: User can select/deselect images to save.
    *   **Upload**:
        1.  Images are uploaded to **Supabase Storage** (Bucket: `detections`).
        2.  `Mission` record is inserted into DB.
        3.  `Detection` records are inserted, linking to the `Mission` and including `image_url` and `bbox`.

### 2-2. Bounding Box Handling
*   **Storage**: We store the **Raw Original Image** (clean, no boxes drawn).
*   **Data**: We store the **Bounding Box Coordinates** in the DB (`bbox` column).
*   **Display**:
    *   The Frontend (Flutter/Web) fetches the image and the `bbox` JSON.
    *   The UI renders the box **dynamically** (using `CustomPainter` in Flutter or `<canvas>`/CSS in Web).
    *   **Benefits**: Allows toggling boxes on/off, changing box color/thickness later, and re-running AI on the raw image if needed.

### 2-3. GPS & Location
*   **GPS (`gps_lat`, `gps_lng`)**: Automatically captured from drone telemetry for each detection.
*   **Location Text (`location_name`, `address`)**: Manually entered by the user to describe the overall mission area (e.g., building name).
