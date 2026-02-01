# VideoAnalyzer Class

---

## Overview
The `VideoAnalyzer` class provides tools for loading, analyzing, and processing video files. It supports frame-by-frame analysis using an `ImageAnalyzer`, saving individual frames, creating timelapse videos, and extracting biological information from video sequences.

---

## Class Definition

```python
class VideoAnalyzer:
    def __init__(self):
        """Initialize the VideoAnalyzer."""
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `video` | `cv2.VideoCapture` | Video capture object. |
| `current_frame` | `np.ndarray` | Current frame as a NumPy array. |
| `frame_count` | `int` | Total number of frames in the video. |
| `fps` | `int` | Frames per second of the video. |
| `image_analyzer` | `ImageAnalyzer` | ImageAnalyzer instance for image processing. |

---

## Methods

### Initialization
- **`__init__(self)`**
  Initializes a new `VideoAnalyzer` instance.

---

### Video Loading
- **`load_video(self, video_path)`**
  Loads a video file.

  - **Parameters**:
    - `video_path`: Path to the video file.

---

### Frame Retrieval
- **`get_frame(self, frame_number=None) -> np.ndarray`**
  Retrieves a specific frame or the next frame if no frame number is specified.

  - **Parameters**:
    - `frame_number`: Optional frame number to retrieve.

  - **Returns**: The frame as a NumPy array.

---

### Frame Saving
- **`save_frame(self, output_path, frame=None)`**
  Saves the current frame or a specific frame as an image.

  - **Parameters**:
    - `output_path`: Path to save the image.
    - `frame`: Optional frame to save (if not provided, saves the current frame).

---

### Frame Analysis
- **`analyze_frame(self, frame=None) -> Dict[str, Any]`**
  Analyzes the current frame or a specific frame using `ImageAnalyzer`.

  - **Parameters**:
    - `frame`: Optional frame to analyze (if not provided, analyzes the current frame).

  - **Returns**: Analysis results, including cells, nuclei, and mitochondria.

---

### Video Analysis
- **`analyze_video(self, frame_interval=1) -> List[Dict[str, Any]]`**
  Analyzes the entire video at specified frame intervals.

  - **Parameters**:
    - `frame_interval`: Interval between frames to analyze.

  - **Returns**: List of analysis results for each analyzed frame.

---

### Timelapse Creation
- **`create_timelapse(self, output_path, start_frame, end_frame, interval=1, resize_factor=1.0)`**
  Creates a timelapse video from a range of frames.

  - **Parameters**:
    - `output_path`: Path to save the timelapse video.
    - `start_frame`: Starting frame number.
    - `end_frame`: Ending frame number.
    - `interval`: Number of frames to skip between each frame in the timelapse.
    - `resize_factor`: Factor by which to resize frames (1.0 means no resizing).

---

### Cleanup
- **`close(self)`**
  Releases the video capture object.

---

## Example Usage

```python
# Initialize VideoAnalyzer
video_analyzer = VideoAnalyzer()

# Load a video file
video_analyzer.load_video("path/to/video.mp4")

# Get a specific frame
frame = video_analyzer.get_frame(100)
print(f"Retrieved frame shape: {frame.shape}")

# Save the current frame
video_analyzer.save_frame("path/to/frame_100.png")

# Analyze a frame
analysis_results = video_analyzer.analyze_frame()
print(f"Analysis results: {analysis_results}")

# Analyze the entire video
video_analysis = video_analyzer.analyze_video(frame_interval=5)
print(f"Video analysis results: {video_analysis}")

# Create a timelapse video
video_analyzer.create_timelapse(
    "path/to/timelapse.mp4",
    start_frame=0,
    end_frame=100,
    interval=2,
    resize_factor=0.5
)

# Close the video capture
video_analyzer.close()
```

---

## Dependencies
- **`cv2` (OpenCV)**: For video processing, frame retrieval, and video writing.
- **`biobridge.tools.image_analyzer.ImageAnalyzer`**: For image analysis.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during video processing and frame analysis.

---

## Notes
- The `VideoAnalyzer` class is designed for analyzing video sequences, particularly those depicting biological processes.
- It supports frame-by-frame analysis using an `ImageAnalyzer` to extract biological information such as cells, nuclei, and mitochondria.
- The class provides methods for saving individual frames and creating timelapse videos.
- The `analyze_frame` method uses an `ImageAnalyzer` to perform detailed analysis of each frame.
- The `analyze_video` method allows for analyzing the entire video at specified frame intervals.
