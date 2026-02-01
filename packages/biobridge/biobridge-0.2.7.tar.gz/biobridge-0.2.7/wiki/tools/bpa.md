# BodyPartAnalyzer Class

---

## Overview
The `BodyPartAnalyzer` class extends `ImageAnalyzer` to provide specialized tools for analyzing body parts from images, extracting contours, detecting landmarks, calculating measurements, generating 3D models, and designing prosthetics. It integrates with MediaPipe for landmark detection and uses PyRosetta for molecular modeling.

---

## Class Definition

```python
class BodyPartAnalyzer(ImageAnalyzer):
    def __init__(self):
        """
        Initialize a new BodyPartAnalyzer object.
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `body_part_models` | `Dict` | Dictionary to store 3D models of body parts. |
| `pose` | `mediapipe.solutions.pose.Pose` | MediaPipe pose detection model. |

---

## Methods

### Initialization
- **`__init__(self)`**
  Initializes a new `BodyPartAnalyzer` instance, setting up MediaPipe pose detection and PyRosetta.

---

### Body Part Analysis
- **`analyze_body_part(self, image_path, part_name) -> Dict[str, Any]`**
  Analyzes a specific body part from an image.

  - **Parameters**:
    - `image_path`: Path to the image file.
    - `part_name`: Name of the body part (e.g., 'hand', 'foot', 'leg').

  - **Returns**: Dictionary containing analysis results, including contours, landmarks, and measurements.

---

### Contour Extraction
- **`extract_contours(self, segmented_image) -> List[np.ndarray]`**
  Extracts contours from a segmented image.

  - **Parameters**:
    - `segmented_image`: Segmented image array.

  - **Returns**: List of contours.

---

### Landmark Detection
- **`detect_landmarks(self, image_path) -> Dict[str, Tuple[float, float, float]]`**
  Detects specific landmarks on the body part using MediaPipe.

  - **Parameters**:
    - `image_path`: Path to the input image.

  - **Returns**: Dictionary of detected landmarks or an empty dictionary if no landmarks are found.

---

### Measurement Calculation
- **`calculate_measurements(self, contours, landmarks) -> Dict[str, float]`**
  Calculates key measurements of the body part.

  - **Parameters**:
    - `contours`: List of contours.
    - `landmarks`: Dictionary of landmarks.

  - **Returns**: Dictionary of measurements.

---

### 3D Model Generation
- **`generate_3d_model(self, analysis_result, resolution=100) -> mesh.Mesh`**
  Generates a 3D model based on the analysis result.

  - **Parameters**:
    - `analysis_result`: Result from `analyze_body_part` method.
    - `resolution`: Resolution of the 3D model.

  - **Returns**: 3D mesh object.

---

### Prosthetic Design
- **`design_prosthetic(self, analysis_result, attachment_type='socket') -> Dict[str, Any]`**
  Designs a prosthetic based on the analysis result.

  - **Parameters**:
    - `analysis_result`: Result from `analyze_body_part` method.
    - `attachment_type`: Type of attachment (e.g., 'socket', 'osseointegration').

  - **Returns**: Dictionary containing prosthetic design parameters.

---

### Visualization
- **`visualize_body_part(self, analysis_result)`**
  Visualizes the analyzed body part with contours and landmarks.

  - **Parameters**:
    - `analysis_result`: Result from `analyze_body_part` method.

- **`visualize_prosthetic(self, prosthetic_design)`**
  Visualizes the designed prosthetic using py3Dmol in a web browser.

  - **Parameters**:
    - `prosthetic_design`: Result from `design_prosthetic` method.

---

### Combined Analysis and Design
- **`analyze_and_design_prosthetic(self, image_path, part_name, attachment_type='socket') -> Tuple[Dict[str, Any], Dict[str, Any]]`**
  Analyzes a body part and designs a prosthetic replacement.

  - **Parameters**:
    - `image_path`: Path to the image file.
    - `part_name`: Name of the body part.
    - `attachment_type`: Type of prosthetic attachment.

  - **Returns**: Tuple of (analysis_result, prosthetic_design).

---

## Example Usage

```python
# Initialize BodyPartAnalyzer
analyzer = BodyPartAnalyzer()

# Analyze a body part
analysis_result = analyzer.analyze_body_part("path/to/hand_image.jpg", "hand")
print(analysis_result)

# Visualize the analyzed body part
analyzer.visualize_body_part(analysis_result)

# Design a prosthetic
prosthetic_design = analyzer.design_prosthetic(analysis_result, attachment_type='socket')
print(prosthetic_design)

# Visualize the prosthetic design
analyzer.visualize_prosthetic(prosthetic_design)

# Combined analysis and design
analysis_result, prosthetic_design = analyzer.analyze_and_design_prosthetic(
    "path/to/hand_image.jpg", "hand", attachment_type='socket'
)
```

---

## Dependencies
- **`numpy`**: For numerical operations and array handling.
- **`sklearn.cluster.KMeans`**: For clustering points in 3D model generation.
- **`scipy.spatial.Delaunay`**: For Delaunay triangulation in 3D model generation.
- **`stl.mesh`**: For creating and handling 3D mesh objects.
- **`biobridge.tools.image_analyzer.ImageAnalyzer`**: For image processing and analysis.
- **`pyrosetta`**: For molecular modeling.
- **`py3Dmol`**: For 3D visualization in a web browser.
- **`cv2` (OpenCV)**: For image processing tasks such as contour extraction.
- **`matplotlib`**: For visualization.
- **`mediapipe`**: For pose and landmark detection.
- **`webbrowser`**: For opening the 3D visualization in a web browser.
- **`tempfile`**: For creating temporary files.
- **`os`**: For file operations.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing, landmark detection, and 3D model generation.

---

## Notes
- The `BodyPartAnalyzer` class is designed for advanced analysis of body parts from images.
- It supports contour extraction, landmark detection, measurement calculation, 3D model generation, and prosthetic design.
- The class integrates with MediaPipe for pose and landmark detection, and with PyRosetta for molecular modeling.
- The `visualize_prosthetic` method provides an interactive 3D visualization of the prosthetic design in a web browser.
