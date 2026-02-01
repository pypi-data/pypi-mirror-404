# XrayAnalyzer Class

---

## Overview
The `XrayAnalyzer` class provides tools for analyzing X-ray images, including contrast enhancement, edge detection, image segmentation, anomaly detection, and bone density measurement. It integrates with an `ImageAnalyzer` for image processing and provides visualization capabilities.

---

## Class Definition

```python
class XrayAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize a new XrayAnalyzer object.
        :param image_analyzer: ImageAnalyzer instance for image processing
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `image_analyzer` | `ImageAnalyzer` | ImageAnalyzer instance for image processing. |

---

## Methods

### Initialization
- **`__init__(self, image_analyzer)`**
  Initializes a new `XrayAnalyzer` instance with the specified `ImageAnalyzer`.

---

### X-ray Analysis
- **`analyze_xray(self, image)`**
  Analyzes an X-ray image using advanced techniques.

  - **Parameters**:
    - `image`: Input X-ray image (ImageJ DataArray).

  - **Returns**: Dictionary containing analysis results, including enhanced image, edges, segmented image, anomalies, and bone density.

---

### Contrast Enhancement
- **`enhance_contrast(self, image)`**
  Enhances the contrast of the X-ray image using adaptive histogram equalization.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Contrast-enhanced image.

---

### Edge Detection
- **`detect_edges(self, image)`**
  Detects edges in the X-ray image using Canny edge detection with automatic threshold selection.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Edge image.

---

### Image Segmentation
- **`segment_image(self, image)`**
  Segments the X-ray image using K-means clustering.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Segmented image.

---

### Anomaly Detection
- **`detect_anomalies(self, image, segmented)`**
  Detects potential anomalies in the X-ray image using Isolation Forest.

  - **Parameters**:
    - `image`: Original grayscale image.
    - `segmented`: Segmented image.

  - **Returns**: List of potential anomalies with coordinates and scores.

---

### Bone Density Measurement
- **`measure_bone_density(self, image)`**
  Measures approximate bone density from the X-ray image using histogram analysis.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Dictionary containing estimated bone density value and histogram.

---

### Visualization
- **`visualize_xray_analysis(self, original_image, analysis_results)`**
  Visualizes the results of X-ray analysis.

  - **Parameters**:
    - `original_image`: Original X-ray image.
    - `analysis_results`: Results from `analyze_xray` method.

---

### Bone Tissue Creation
- **`create_bone_tissue_from_xray(self, image, tissue_name: str) -> BoneTissue`**
  Creates a `BoneTissue` object from X-ray analysis results.

  - **Parameters**:
    - `image`: Input grayscale image.
    - `tissue_name`: Name for the new `BoneTissue` object.

  - **Returns**: `BoneTissue` object.

---

## Example Usage

```python
# Initialize ImageAnalyzer
image_analyzer = ImageAnalyzer()

# Initialize XrayAnalyzer
xray_analyzer = XrayAnalyzer(image_analyzer)

# Load an X-ray image
image = image_analyzer.load_image("path/to/xray_image.tif")

# Analyze the X-ray image
analysis_results = xray_analyzer.analyze_xray(image)

# Visualize the X-ray analysis
xray_analyzer.visualize_xray_analysis(image, analysis_results)

# Create a BoneTissue object from the X-ray analysis
bone_tissue = xray_analyzer.create_bone_tissue_from_xray(image, "Femur Tissue")
print(bone_tissue)
```

---

## Dependencies
- **`cv2` (OpenCV)**: For image processing tasks such as contrast enhancement and edge detection.
- **`numpy`**: For numerical operations and array handling.
- **`sklearn.ensemble.IsolationForest`**: For anomaly detection.
- **`sklearn.preprocessing.StandardScaler`**: For feature normalization.
- **`matplotlib`**: For visualization.
- **`biobridge.blocks.cell.Cell`**: For creating cell objects.
- **`biobridge.definitions.tissues.bone.BoneTissue`**: For creating bone tissue objects.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing and analysis.

---

## Notes
- The `XrayAnalyzer` class is designed for advanced X-ray image analysis.
- It supports contrast enhancement, edge detection, segmentation, anomaly detection, and bone density measurement.
- The `visualize_xray_analysis` method provides a graphical representation of the analysis results.
- The `create_bone_tissue_from_xray` method creates a `BoneTissue` object based on the analysis results, which can be used for further biological simulations.
