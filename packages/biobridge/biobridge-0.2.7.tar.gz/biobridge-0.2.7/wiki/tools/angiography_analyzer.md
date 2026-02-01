# AngiographyAnalyzer Class

---

## Overview
The `AngiographyAnalyzer` class provides advanced tools for analyzing angiographic images. It supports vessel contrast enhancement, vessel centerline detection, vessel segmentation, stenosis detection, aneurysm detection, vascular density calculation, and collateral circulation detection. The class also includes visualization capabilities and methods for creating vascular tissue objects.

---

## Class Definition

```python
class AngiographyAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize a new AngiographyAnalyzer object.
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
  Initializes a new `AngiographyAnalyzer` instance with the specified `ImageAnalyzer`.

---

### Angiogram Analysis
- **`analyze_angiogram(self, image) -> Dict[str, Any]`**
  Analyzes an angiographic image using advanced vessel detection techniques.

  - **Parameters**:
    - `image`: Input angiography image (ImageJ DataArray).

  - **Returns**: Dictionary containing analysis results, including enhanced image, vessel centerlines, vessel mask, vessel measurements, stenosis analysis, aneurysm analysis, vascular density, and collateral vessels.

---

### Vessel Contrast Enhancement
- **`enhance_vessel_contrast(self, image) -> np.ndarray`**
  Enhances vessel contrast using a multi-scale vessel enhancement filter.

  - **Parameters**:
    - `image`: Input grayscale image.

  - **Returns**: Vessel-enhanced image.

---

### Vessel Centerline Detection
- **`detect_vessel_centerlines(self, image) -> np.ndarray`**
  Detects vessel centerlines using morphological thinning.

  - **Parameters**:
    - `image`: Enhanced vessel image.

  - **Returns**: Binary image with vessel centerlines.

---

### Vessel Segmentation
- **`segment_vessels(self, image) -> np.ndarray`**
  Segments blood vessels using adaptive thresholding and morphological operations.

  - **Parameters**:
    - `image`: Enhanced vessel image.

  - **Returns**: Binary vessel mask.

---

### Vessel Parameter Measurement
- **`measure_vessel_parameters(self, vessel_mask, centerlines) -> Dict[str, Any]`**
  Measures vessel parameters, including diameter, length, and tortuosity.

  - **Parameters**:
    - `vessel_mask`: Binary vessel mask.
    - `centerlines`: Binary centerline image.

  - **Returns**: Dictionary with vessel measurements.

---

### Stenosis Detection
- **`detect_stenosis(self, vessel_measurements) -> List[Dict[str, Any]]`**
  Detects potential stenosis (vessel narrowing) locations.

  - **Parameters**:
    - `vessel_measurements`: Vessel measurement data.

  - **Returns**: List of potential stenosis locations with properties.

---

### Aneurysm Detection
- **`detect_aneurysms(self, vessel_mask) -> List[Dict[str, Any]]`**
  Detects potential aneurysms using morphological analysis.

  - **Parameters**:
    - `vessel_mask`: Binary vessel mask.

  - **Returns**: List of potential aneurysm locations with properties.

---

### Vascular Density Calculation
- **`calculate_vascular_density(self, vessel_mask) -> Dict[str, float]`**
  Calculates vascular density metrics.

  - **Parameters**:
    - `vessel_mask`: Binary vessel mask.

  - **Returns**: Dictionary with density measurements.

---

### Collateral Circulation Detection
- **`detect_collateral_circulation(self, centerlines) -> Dict[str, Any]`**
  Detects potential collateral circulation patterns.

  - **Parameters**:
    - `centerlines`: Binary centerline image.

  - **Returns**: Information about collateral vessels.

---

### Visualization
- **`visualize_angiogram_analysis(self, original_image, analysis_results)`**
  Visualizes the results of angiography analysis.

  - **Parameters**:
    - `original_image`: Original angiogram image.
    - `analysis_results`: Results from `analyze_angiogram` method.

---

### Vascular Tissue Creation
- **`create_vascular_tissue_from_angiogram(self, image, tissue_name: str) -> VascularTissue`**
  Creates a `VascularTissue` object from angiography analysis results.

  - **Parameters**:
    - `image`: Input grayscale image.
    - `tissue_name`: Name for the new `VascularTissue` object.

  - **Returns**: `VascularTissue` object.

---

## Example Usage

```python
# Initialize ImageAnalyzer
image_analyzer = ImageAnalyzer()

# Initialize AngiographyAnalyzer
angiography_analyzer = AngiographyAnalyzer(image_analyzer)

# Load an angiographic image
image = image_analyzer.load_image("path/to/angiogram.tif")

# Analyze the angiogram
analysis_results = angiography_analyzer.analyze_angiogram(image)

# Visualize the angiography analysis
angiography_analyzer.visualize_angiogram_analysis(image, analysis_results)

# Create a vascular tissue object from the angiogram analysis
vascular_tissue = angiography_analyzer.create_vascular_tissue_from_angiogram(
    image, "Coronary Artery Tissue"
)
print(vascular_tissue)
```

---

## Dependencies
- **`cv2` (OpenCV)**: For image processing tasks such as filtering, edge detection, and segmentation.
- **`numpy`**: For numerical operations and array handling.
- **`scipy`**: For scientific computing and image processing.
- **`skimage`**: For image processing and analysis.
- **`sklearn.cluster.DBSCAN`**: For clustering-based analysis.
- **`matplotlib`**: For visualization.
- **`biobridge.blocks.cell.Cell`**: For creating cell objects.
- **`biobridge.definitions.tissues.vascular.VascularTissue`**: For creating vascular tissue objects.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing and analysis.

---

## Notes
- The `AngiographyAnalyzer` class is designed for advanced angiographic image analysis.
- It supports vessel contrast enhancement, vessel centerline detection, vessel segmentation, stenosis detection, aneurysm detection, vascular density calculation, and collateral circulation detection.
- The `visualize_angiogram_analysis` method provides a graphical representation of the analysis results.
- The `create_vascular_tissue_from_angiogram` method creates a `VascularTissue` object based on the analysis results, which can be used for further biological simulations.
