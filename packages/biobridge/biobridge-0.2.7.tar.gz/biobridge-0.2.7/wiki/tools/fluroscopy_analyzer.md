# FluoroscopyAnalyzer Class
---
## Overview
The `FluoroscopyAnalyzer` class provides advanced tools for analyzing fluoroscopy videos and frames. It supports loading fluoroscopy videos, analyzing individual frames, detecting anatomical structures, tracking contrast agents, estimating radiation dose, detecting motion artifacts, and visualizing analysis results. The class also includes methods for creating enhanced fluoroscopy videos and generating sequence summaries.

---
## Class Definition
```python
from collections import deque
import cv2
import matplotlib.pyplot as plt
import numpy as np
from biobridge.tools.video_analyzer import VideoAnalyzer

class FluoroscopyAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize the FluoroscopyAnalyzer.
        :param image_analyzer: ImageAnalyzer instance for processing individual frames
        """
        self.image_analyzer = image_analyzer
        self.video_analyzer = VideoAnalyzer()
        self.frame_history = deque(maxlen=10)  # Store last 10 frames for temporal analysis
        self.motion_history = []
        self.contrast_agent_tracking = {}
```

---
## Attributes
| Attribute                | Type                     | Description                                                                 |
|--------------------------|--------------------------|-----------------------------------------------------------------------------|
| `image_analyzer`         | `ImageAnalyzer`          | ImageAnalyzer instance for processing individual frames.                  |
| `video_analyzer`         | `VideoAnalyzer`          | VideoAnalyzer instance for handling video data.                           |
| `frame_history`          | `deque`                  | Stores the last 10 frames for temporal analysis.                          |
| `motion_history`         | `List[float]`            | Stores motion magnitude history for temporal analysis.                    |
| `contrast_agent_tracking`| `Dict[str, Any]`         | Tracks contrast agent data across frames.                                  |

---
## Methods
### Initialization
- **`__init__(self, image_analyzer)`**
  Initializes a new `FluoroscopyAnalyzer` instance with the specified `ImageAnalyzer`.

---
### Video Loading
- **`load_fluoroscopy_video(self, video_path)`**
  Loads a fluoroscopy video file.
  - **Parameters**:
    - `video_path`: Path to the fluoroscopy video file.

---
### Frame Analysis
- **`analyze_frame(self, frame) -> Dict[str, Any]`**
  Analyzes a single fluoroscopy frame with enhanced X-ray techniques.
  - **Parameters**:
    - `frame`: Input fluoroscopy frame (numpy array).
  - **Returns**: Dictionary containing analysis results.

---
### Preprocessing
- **`preprocess_fluoroscopy_frame(self, frame) -> np.ndarray`**
  Applies fluoroscopy-specific preprocessing to reduce noise and enhance image quality.
  - **Parameters**:
    - `frame`: Input grayscale frame.
  - **Returns**: Preprocessed frame.

---
### Contrast Enhancement
- **`enhance_fluoroscopy_contrast(self, frame) -> np.ndarray`**
  Enhances contrast for fluoroscopy images.
  - **Parameters**:
    - `frame`: Input frame.
  - **Returns**: Contrast-enhanced frame.

---
### Anatomical Structure Detection
- **`detect_anatomical_structures(self, frame) -> Dict[str, Any]`**
  Detects and segments anatomical structures in fluoroscopy images.
  - **Parameters**:
    - `frame`: Enhanced fluoroscopy frame.
  - **Returns**: Dictionary of detected structures.

---
### Contrast Agent Analysis
- **`analyze_contrast_agent(self, frame) -> Dict[str, Any]`**
  Analyzes contrast agent flow and distribution in fluoroscopy.
  - **Parameters**:
    - `frame`: Enhanced fluoroscopy frame.
  - **Returns**: Contrast agent analysis results.

---
### Radiation Dose Estimation
- **`estimate_radiation_dose(self, frame) -> Dict[str, float]`**
  Estimates radiation dose based on image characteristics.
  - **Parameters**:
    - `frame`: Original grayscale frame.
  - **Returns**: Radiation dose estimate.

---
### Motion Artifact Detection
- **`detect_motion_artifacts(self, frame) -> Dict[str, Any]`**
  Detects motion artifacts in fluoroscopy images.
  - **Parameters**:
    - `frame`: Enhanced frame.
  - **Returns**: Motion artifact analysis.

---
### Bone Density Measurement
- **`measure_bone_density(self, frame) -> Dict[str, Any]`**
  Measures bone density from a fluoroscopy frame.
  - **Parameters**:
    - `frame`: Enhanced fluoroscopy frame.
  - **Returns**: Bone density measurements.

---
### Frame Quality Assessment
- **`assess_frame_quality(self, frame) -> Dict[str, float]`**
  Assesses the quality of a fluoroscopy frame.
  - **Parameters**:
    - `frame`: Enhanced frame.
  - **Returns**: Quality assessment score (0-100).

---
### Sequence Analysis
- **`analyze_fluoroscopy_sequence(self, frame_interval=1, max_frames=None) -> Dict[str, Any]`**
  Analyzes an entire fluoroscopy video sequence.
  - **Parameters**:
    - `frame_interval`: Interval between analyzed frames.
    - `max_frames`: Maximum number of frames to analyze.
  - **Returns**: Sequence analysis results.

---
### Sequence Summary Generation
- **`generate_sequence_summary(self, temporal_analysis) -> Dict[str, Any]`**
  Generates a summary of the fluoroscopy sequence analysis.
  - **Parameters**:
    - `temporal_analysis`: Temporal analysis data.
  - **Returns**: Summary dictionary.

---
### Recommendations Generation
- **`generate_recommendations(self, temporal_analysis) -> List[str]`**
  Generates recommendations based on fluoroscopy analysis.
  - **Parameters**:
    - `temporal_analysis`: Temporal analysis data.
  - **Returns**: List of recommendations.

---
### Visualization
- **`visualize_fluoroscopy_analysis(self, frame_analysis)`**
  Visualizes the results of fluoroscopy frame analysis.
  - **Parameters**:
    - `frame_analysis`: Results from `analyze_frame` method.

---
### Enhanced Video Creation
- **`create_enhanced_fluoroscopy_video(self, output_path, enhancement_type="contrast")`**
  Creates an enhanced version of the fluoroscopy video.
  - **Parameters**:
    - `output_path`: Path to save the enhanced video.
    - `enhancement_type`: Type of enhancement ("contrast", "edges", "motion").

---
### Resource Cleanup
- **`close(self)`**
  Releases resources used by the `FluoroscopyAnalyzer`.

---
## Example Usage
```python
# Initialize ImageAnalyzer and FluoroscopyAnalyzer
image_analyzer = ImageAnalyzer()
fluoroscopy_analyzer = FluoroscopyAnalyzer(image_analyzer)

# Load a fluoroscopy video
fluoroscopy_analyzer.load_fluoroscopy_video("path/to/fluoroscopy_video.mp4")

# Analyze a specific frame
frame = fluoroscopy_analyzer.video_analyzer.get_frame(0)
frame_analysis = fluoroscopy_analyzer.analyze_frame(frame)

# Visualize the analysis
fluoroscopy_analyzer.visualize_fluoroscopy_analysis(frame_analysis)

# Analyze the entire sequence
sequence_analysis = fluoroscopy_analyzer.analyze_fluoroscopy_sequence()

# Create an enhanced video
fluoroscopy_analyzer.create_enhanced_fluoroscopy_video("path/to/enhanced_video.mp4")

# Release resources
fluoroscopy_analyzer.close()
```

---
## Dependencies
- **`collections.deque`**: For storing frame history.
- **`cv2` (OpenCV)**: For image and video processing.
- **`matplotlib.pyplot`**: For visualization.
- **`numpy`**: For numerical operations and array handling.
- **`biobridge.tools.video_analyzer.VideoAnalyzer`**: For video analysis.

---
## Error Handling
- The class includes checks for valid input data and handles potential errors during image and video processing.

---
## Notes
- The `FluoroscopyAnalyzer` class is designed for advanced fluoroscopy video and frame analysis.
- It supports contrast enhancement, anatomical structure detection, motion artifact detection, and radiation dose estimation.
- The `visualize_fluoroscopy_analysis` method provides a graphical representation of the analysis results.
- The `create_enhanced_fluoroscopy_video` method creates an enhanced video based on the specified enhancement type.
