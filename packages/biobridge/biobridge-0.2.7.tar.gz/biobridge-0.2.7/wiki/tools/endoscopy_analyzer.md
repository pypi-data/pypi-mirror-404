# EndoscopyAnalyzer Class

---

## Overview
The `EndoscopyAnalyzer` class provides advanced tools for analyzing endoscopic images. It supports tissue segmentation, edge detection, texture analysis, abnormality detection, and classification of tissue health. The class integrates machine learning for anomaly detection and provides specialized analysis for different types of endoscopy (gastric, colonoscopy, esophageal).

---

## Class Definition

```python
class EndoscopyAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize a new EndoscopyAnalyzer object.
        :param image_analyzer: ImageAnalyzer instance for image processing
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `image_analyzer` | `ImageAnalyzer` | ImageAnalyzer instance for image processing. |
| `tissue_color_ranges` | `Dict[str, Dict[str, Tuple[int, int]]]` | Color ranges for different tissue conditions in HSV space. |
| `texture_params` | `Dict[str, Any]` | Parameters for texture feature extraction. |

---

## Methods

### Initialization
- **`__init__(self, image_analyzer)`**
  Initializes a new `EndoscopyAnalyzer` instance with the specified `ImageAnalyzer`.

---

### Endoscopy Image Analysis
- **`analyze_endoscopy_image(self, image, endoscopy_type="gastric", enhanced_processing=True) -> Dict[str, Any]`**
  Analyzes an endoscopic image using advanced computer vision techniques.

  - **Parameters**:
    - `image`: Input endoscopic image (2D or 3D array).
    - `endoscopy_type`: Type of endoscopy ('gastric', 'colonoscopy', 'esophageal').
    - `enhanced_processing`: Whether to apply enhanced processing techniques.

  - **Returns**: Dictionary containing comprehensive analysis results.

---

### Image Enhancement
- **`enhance_endoscopy_image(self, rgb_image) -> np.ndarray`**
  Enhances endoscopy image quality using multiple techniques.

  - **Parameters**:
    - `rgb_image`: Input RGB image.

  - **Returns**: Enhanced image.

- **`correct_color_cast(self, image) -> np.ndarray`**
  Corrects color cast in endoscopy images.

  - **Parameters**:
    - `image`: Input image.

  - **Returns**: Color-corrected image.

---

### Tissue Segmentation
- **`segment_endoscopy_tissues(self, hsv_image) -> Dict[str, np.ndarray]`**
  Segments different tissue types and conditions in endoscopy images.

  - **Parameters**:
    - `hsv_image`: HSV color space image.

  - **Returns**: Dictionary of tissue masks.

- **`kmeans_tissue_segmentation(self, hsv_image, n_clusters=5) -> Dict[str, np.ndarray]`**
  Performs tissue segmentation using K-means clustering.

  - **Parameters**:
    - `hsv_image`: HSV image.
    - `n_clusters`: Number of clusters.

  - **Returns**: Dictionary of cluster masks.

---

### Edge Detection
- **`detect_endoscopy_edges(self, image) -> np.ndarray`**
  Detects edges in endoscopy images using multiple methods.

  - **Parameters**:
    - `image`: Input image.

  - **Returns**: Edge map.

---

### Texture Analysis
- **`analyze_texture_patterns(self, image) -> Dict[str, Any]`**
  Analyzes texture patterns in endoscopy images.

  - **Parameters**:
    - `image`: Input image.

  - **Returns**: Texture analysis results.

- **`calculate_fractal_dimension(self, image) -> float`**
  Calculates the fractal dimension of an image texture.

  - **Parameters**:
    - `image`: Grayscale image.

  - **Returns**: Fractal dimension.

---

### Abnormality Detection
- **`detect_abnormalities(self, rgb_image, hsv_image) -> List[Dict[str, Any]]`**
  Detects abnormalities using machine learning and image analysis.

  - **Parameters**:
    - `rgb_image`: RGB image.
    - `hsv_image`: HSV image.

  - **Returns**: List of detected abnormalities.

- **`classify_abnormality_type(self, patch_rgb, patch_hsv) -> str`**
  Classifies the type of abnormality based on color and texture features.

  - **Parameters**:
    - `patch_rgb`: RGB patch.
    - `patch_hsv`: HSV patch.

  - **Returns**: Abnormality type.

---

### Feature Measurement
- **`measure_endoscopy_features(self, tissue_segmentation, rgb_image) -> Dict[str, Any]`**
  Measures various features in endoscopy images.

  - **Parameters**:
    - `tissue_segmentation`: Tissue segmentation results.
    - `rgb_image`: Original RGB image.

  - **Returns**: Measurement results.

---

### Tissue Health Classification
- **`classify_tissue_health(self, rgb_image, tissue_segmentation, texture_analysis) -> Dict[str, float]`**
  Classifies the health status of different tissues.

  - **Parameters**:
    - `rgb_image`: RGB image.
    - `tissue_segmentation`: Tissue segmentation results.
    - `texture_analysis`: Texture analysis results.

  - **Returns**: Tissue health classification.

---

### Specific Condition Detection
- **`detect_specific_conditions(self, tissue_segmentation, endoscopy_type) -> Dict[str, Any]`**
  Detects specific conditions based on endoscopy type.

  - **Parameters**:
    - `tissue_segmentation`: Tissue segmentation.
    - `endoscopy_type`: Type of endoscopy.

  - **Returns**: Specific findings.

- **`detect_gastric_conditions(self, tissue_segmentation) -> Dict[str, Any]`**
  Detects gastric-specific conditions.

  - **Parameters**:
    - `tissue_segmentation`: Tissue segmentation.

  - **Returns**: Gastric-specific findings.

- **`detect_colon_conditions(self, tissue_segmentation) -> Dict[str, Any]`**
  Detects colon-specific conditions.

  - **Parameters**:
    - `tissue_segmentation`: Tissue segmentation.

  - **Returns**: Colon-specific findings.

- **`detect_esophageal_conditions(self, tissue_segmentation) -> Dict[str, Any]`**
  Detects esophageal-specific conditions.

  - **Parameters**:
    - `tissue_segmentation`: Tissue segmentation.

  - **Returns**: Esophageal-specific findings.

---

### Severity Score Calculation
- **`calculate_severity_scores(self, abnormalities, tissue_health) -> Dict[str, float]`**
  Calculates severity scores for different conditions.

  - **Parameters**:
    - `abnormalities`: Detected abnormalities.
    - `tissue_health`: Tissue health classification.

  - **Returns**: Severity scores.

---

## Example Usage

```python
# Initialize ImageAnalyzer
image_analyzer = ImageAnalyzer()

# Initialize EndoscopyAnalyzer
endoscopy_analyzer = EndoscopyAnalyzer(image_analyzer)

# Load an endoscopic image
image = image_analyzer.load_image("path/to/endoscopy_image.jpg")

# Analyze the endoscopic image
analysis_results = endoscopy_analyzer.analyze_endoscopy_image(image, endoscopy_type="gastric")

# Access analysis results
print(f"Tissue segmentation: {analysis_results['tissue_segmentation']}")
print(f"Abnormalities: {analysis_results['abnormalities']}")
print(f"Tissue health: {analysis_results['tissue_health']}")
print(f"Specific findings: {analysis_results['specific_findings']}")
print(f"Severity scores: {analysis_results['severity_scores']}")
```

---

## Dependencies
- **`numpy`**: For numerical operations and array handling.
- **`cv2` (OpenCV)**: For image processing tasks such as color space conversion, filtering, and edge detection.
- **`skimage`**: For image processing and analysis, including texture feature extraction.
- **`sklearn.cluster.KMeans`**: For clustering-based segmentation.
- **`sklearn.ensemble.IsolationForest`**: For anomaly detection.
- **`sklearn.preprocessing.StandardScaler`**: For feature normalization.
- **`biobridge.tools.image_analyzer.ImageAnalyzer`**: For image processing and analysis.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing and analysis.

---

## Notes
- The `EndoscopyAnalyzer` class is designed for advanced endoscopic image analysis.
- It supports multiple types of endoscopy and provides detailed analysis of tissue health, abnormalities, and specific conditions.
- The class integrates machine learning for anomaly detection and provides specialized analysis for different types of endoscopy.
- The `analyze_endoscopy_image` method provides a comprehensive analysis of endoscopic images, including tissue segmentation, edge detection, texture analysis, and abnormality detection.
