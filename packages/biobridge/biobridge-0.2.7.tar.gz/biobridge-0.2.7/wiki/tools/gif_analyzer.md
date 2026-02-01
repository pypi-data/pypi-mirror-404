# GifAnalyzer Class

---

## Overview
The `GifAnalyzer` class provides tools for loading, analyzing, and processing GIF files. It supports frame-by-frame analysis using an `ImageAnalyzer`, saving individual frames, creating timelapse videos, and extracting biological information from GIF animations.

---

## Class Definition

```python
class GifAnalyzer:
    def __init__(self):
        """Initialize the GifAnalyzer."""
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `gif` | `imageio.Reader` | GIF reader object. |
| `current_frame` | `np.ndarray` | Current frame as a NumPy array. |
| `frame_count` | `int` | Total number of frames in the GIF. |
| `fps` | `int` | Frames per second of the GIF. |
| `image_analyzer` | `ImageAnalyzer` | ImageAnalyzer instance for image processing. |

---

## Methods

### Initialization
- **`__init__(self)`**
  Initializes a new `GifAnalyzer` instance.

---

### GIF Loading
- **`load_gif(self, gif_path)`**
  Loads a GIF file.

  - **Parameters**:
    - `gif_path`: Path to the GIF file.

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

### GIF Analysis
- **`analyze_gif(self, frame_interval=1) -> List[Dict[str, Any]]`**
  Analyzes the entire GIF at specified frame intervals.

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
  Releases the GIF reader object.

---

## Example Usage

```python
# Initialize GifAnalyzer
gif_analyzer = GifAnalyzer()

# Load a GIF file
gif_analyzer.load_gif("path/to/animation.gif")

# Get a specific frame
frame = gif_analyzer.get_frame(5)
print(f"Retrieved frame shape: {frame.shape}")

# Save the current frame
gif_analyzer.save_frame("path/to/frame_5.png")

# Analyze a frame
analysis_results = gif_analyzer.analyze_frame()
print(f"Analysis results: {analysis_results}")

# Analyze the entire GIF
gif_analysis = gif_analyzer.analyze_gif(frame_interval=2)
print(f"GIF analysis results: {gif_analysis}")

# Create a timelapse video
gif_analyzer.create_timelapse(
    "path/to/timelapse.mp4",
    start_frame=0,
    end_frame=20,
    interval=2,
    resize_factor=0.5
)

# Close the GIF reader
gif_analyzer.close()
```

---

## Dependencies
- **`imageio`**: For reading GIF files.
- **`cv2` (OpenCV)**: For image processing and video writing.
- **`biobridge.tools.image_analyzer.ImageAnalyzer`**: For image analysis.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during GIF processing and frame analysis.

---

## Notes
- The `GifAnalyzer` class is designed for analyzing GIF animations, particularly those depicting biological processes.
- It supports frame-by-frame analysis using an `ImageAnalyzer` to extract biological information such as cells, nuclei, and mitochondria.
- The class provides methods for saving individual frames and creating timelapse videos.
- The `analyze_frame` method uses an `ImageAnalyzer` to perform detailed analysis of each frame.
