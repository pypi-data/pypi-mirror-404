# GammaRayAnalyzer Class

---

## Overview
The `GammaRayAnalyzer` class provides advanced tools for analyzing gamma ray images. It supports noise reduction, contrast enhancement, hot spot detection, image segmentation, anomaly detection, and radiation intensity measurement. The class also includes visualization capabilities and methods for creating radiation-affected tissue and bone tissue objects.

---

## Class Definition

```python
class GammaRayAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize a new GammaRayAnalyzer object.
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
  Initializes a new `GammaRayAnalyzer` instance with the specified `ImageAnalyzer`.

---

### Gamma Ray Analysis
- **`analyze_gamma_ray(self, image) -> Dict[str, Any]`**
  Analyzes a gamma ray image using advanced techniques.

  - **Parameters**:
    - `image`: Input gamma ray image (ImageJ DataArray).

  - **Returns**: Dictionary containing analysis results, including denoised image, enhanced image, hot spots, segmented image, anomalies, and radiation intensity.

---

### Noise Reduction
- **`reduce_noise(self, image) -> np.ndarray`**
  Reduces noise in the gamma ray image using Non-local Means Denoising.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Denoised image.

---

### Contrast Enhancement
- **`enhance_contrast(self, image) -> np.ndarray`**
  Enhances the contrast of the gamma ray image using adaptive histogram equalization.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Contrast-enhanced image.

---

### Hot Spot Detection
- **`detect_hot_spots(self, image) -> np.ndarray`**
  Detects hot spots in the gamma ray image using thresholding.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Binary image with hot spots.

---

### Image Segmentation
- **`segment_image(self, image) -> np.ndarray`**
  Segments the gamma ray image using K-means clustering.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Segmented image.

---

### Anomaly Detection
- **`detect_anomalies(self, image, segmented) -> List[Dict[str, Any]]`**
  Detects potential anomalies in the gamma ray image using Isolation Forest.

  - **Parameters**:
    - `image`: Original grayscale image.
    - `segmented`: Segmented image.

  - **Returns**: List of potential anomalies with coordinates and scores.

---

### Radiation Intensity Measurement
- **`measure_radiation_intensity(self, image) -> Dict[str, Any]`**
  Measures radiation intensity from the gamma ray image using histogram analysis.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Estimated radiation intensity value and histogram.

---

### Visualization
- **`visualize_gamma_ray_analysis(self, original_image, analysis_results)`**
  Visualizes the results of gamma ray analysis.

  - **Parameters**:
    - `original_image`: Original gamma ray image.
    - `analysis_results`: Results from `analyze_gamma_ray` method.

---

### Radiation-Affected Tissue Creation
- **`create_radiation_affected_tissue(self, image, tissue_name: str) -> RadiationAffectedTissue`**
  Creates a `RadiationAffectedTissue` object from gamma ray analysis results.

  - **Parameters**:
    - `image`: Input grayscale image.
    - `tissue_name`: Name for the new `RadiationAffectedTissue` object.

  - **Returns**: `RadiationAffectedTissue` object.

---

### Bone Tissue Creation
- **`create_bone_tissue_from_gamma(self, image, tissue_name: str) -> BoneTissue`**
  Creates a `BoneTissue` object from gamma ray analysis results.

  - **Parameters**:
    - `image`: Input grayscale image.
    - `tissue_name`: Name for the new `BoneTissue` object.

  - **Returns**: `BoneTissue` object.

---

### X-ray and Gamma Ray Comparison
- **`compare_xray_and_gamma_bone_analysis(self, xray_image, gamma_image, tissue_name: str) -> dict`**
  Compares bone analysis results from X-ray and gamma ray images.

  - **Parameters**:
    - `xray_image`: X-ray image of the bone.
    - `gamma_image`: Gamma ray image of the bone.
    - `tissue_name`: Name for the bone tissue.

  - **Returns**: Dictionary containing comparison results.

---

## Example Usage

```python
# Initialize ImageAnalyzer
image_analyzer = ImageAnalyzer()

# Initialize GammaRayAnalyzer
gamma_ray_analyzer = GammaRayAnalyzer(image_analyzer)

# Load a gamma ray image
image = image_analyzer.load_image("path/to/gamma_ray_image.tif")

# Analyze the gamma ray image
analysis_results = gamma_ray_analyzer.analyze_gamma_ray(image)

# Visualize the gamma ray analysis
gamma_ray_analyzer.visualize_gamma_ray_analysis(image, analysis_results)

# Create a radiation-affected tissue object from the gamma ray analysis
radiation_affected_tissue = gamma_ray_analyzer.create_radiation_affected_tissue(
    image, "Radiation Affected Tissue"
)
print(radiation_affected_tissue)

# Create a bone tissue object from the gamma ray analysis
bone_tissue = gamma_ray_analyzer.create_bone_tissue_from_gamma(
    image, "Bone Tissue"
)
print(bone_tissue)

# Compare X-ray and gamma ray bone analysis
xray_image = image_analyzer.load_image("path/to/xray_image.tif")
comparison_results = gamma_ray_analyzer.compare_xray_and_gamma_bone_analysis(
    xray_image, image, "Femur"
)
print(comparison_results)
```

---

## Dependencies
- **`numpy`**: For numerical operations and array handling.
- **`cv2` (OpenCV)**: For image processing tasks such as noise reduction, contrast enhancement, and thresholding.
- **`sklearn.ensemble.IsolationForest`**: For anomaly detection.
- **`sklearn.preprocessing.StandardScaler`**: For feature normalization.
- **`matplotlib`**: For visualization.
- **`biobridge.definitions.tissues.radiation_affected.RadiationAffectedTissue`**: For creating radiation-affected tissue objects.
- **`biobridge.blocks.cell.Cell`**: For creating cell objects.
- **`biobridge.tools.xray_analyzer.XrayAnalyzer`**: For X-ray image analysis.
- **`biobridge.tools.xray_analyzer.BoneTissue`**: For creating bone tissue objects.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing and analysis.

---

## Notes
- The `GammaRayAnalyzer` class is designed for advanced gamma ray image analysis.
- It supports noise reduction, contrast enhancement, hot spot detection, image segmentation, and anomaly detection.
- The `visualize_gamma_ray_analysis` method provides a graphical representation of the analysis results.
- The `create_radiation_affected_tissue` and `create_bone_tissue_from_gamma` methods create tissue objects based on the analysis results, which can be used for further biological simulations.
- The `compare_xray_and_gamma_bone_analysis` method allows for comparative analysis of X-ray and gamma ray images.
