# GitHub Copilot Instructions for Airbot Grasping Project

This project implements a robotic pick-and-place system using an Airbot arm, Intel RealSense camera, and YOLO object detection.

## Architecture Overview

The system operates as a script-based pipeline:
1.  **Initialization**: `DetectionSystem` initializes the camera, robot connection, and YOLO model.
2.  **Perception**: Captures RGB-D images, detects objects using YOLO (`ultralytics`), and calculates 3D coordinates.
3.  **Coordinate Transformation**: Converts 2D pixel coordinates + Depth -> Camera 3D Frame -> Robot Base Frame using a calibrated extrinsics matrix.
4.  **Control**: Executes a grasp sequence (Hover -> Descend -> Grasp -> Lift) using the `airbot_py` SDK.

## Key Components & Files

-   **Main Entry Point**: `test_grasp09fianl.py` (currently the active integration script).
    -   Contains `DetectionSystem` class and the main execution loop.
    -   Handles the full grasp lifecycle: detection, filtering, and robot control.
-   **Configuration**: `config/camera.yaml`
    -   Stores critical parameters: `camera_extrinsics` (matrix), `model_path`, and camera stream settings.
-   **Calibration**: `cam_calibration_real_3.0/`
    -   `cam_calib.py`: Camera calibration logic using chessboard images.
    -   `airbot_calibration.py`: Hand-eye calibration routines.
-   **Dependencies**:
    -   `airbot_py`: Custom wheel for robot control.
    -   `pyrealsense2`: Intel RealSense SDK.
    -   `ultralytics`: YOLOv8 for object detection.

## Critical Workflows

### 1. Running the Grasp Demo
The main script is `test_grasp09fianl.py`. It connects to a local robot simulation or hardware at `localhost:50000`.
```python
# Initialize system
detector = DetectionSystem(config_path="config/camera.yaml")
# The script automatically moves the robot, detects, and attempts to grasp.
```

### 2. Configuration Management
-   **Extrinsics**: The `camera_extrinsics.matrix` in `config/camera.yaml` MUST match the current physical setup. If the camera moves, recalibration is required.
-   **Model**: Update `model_path` in `config/camera.yaml` to point to the latest trained YOLO weights (e.g., `best.pt`).

### 3. Robot Control Patterns
-   **Movement**: Use `self.robot.move_to_cart_pose([position, quaternion])`.
    -   `position`: `[x, y, z]` in meters.
    -   `quaternion`: `[qx, qy, qz, qw]`.
-   **Gripper**: Use `self.robot.move_eef_pos([value])`.
    -   `0.00` typically means closed/grasping.
-   **Coordinate Systems**:
    -   Camera Frame: Z-forward.
    -   Robot Frame: Base frame.
    -   Conversion relies on `pixel2cam` (intrinsics) followed by matrix multiplication (extrinsics).

## Coding Conventions

-   **Data Filtering**: The system uses a multi-sample approach (e.g., 10 samples) with IQR (Interquartile Range) filtering to stabilize detection coordinates before moving the robot.
-   **Depth Handling**: Depth is retrieved from the aligned depth frame. If the center pixel is invalid (0), it falls back to a median of the surrounding region.
-   **File Naming**: Note that multiple versions of scripts exist (e.g., `copy`, `final`). Always check `test_grasp09fianl.py` as the reference implementation.

## Common Issues
-   **Connection**: Ensure the robot server is running and accessible at `localhost:50000`.
-   **Depth Scale**: Depth values are multiplied by `self.depth_scale` to convert to meters.
-   **Alignment**: RGB and Depth frames are aligned using `rs.align(rs.stream.color)`.
