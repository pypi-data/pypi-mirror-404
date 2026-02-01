# MammographyAnalyzer Class

---

## Overview
The `MammographyAnalyzer` class provides advanced tools for analyzing mammographic images. It supports breast density analysis, mass detection, calcification detection, architectural distortion detection, asymmetry detection, and skin thickening analysis. The class also includes visualization capabilities and methods for generating BI-RADS assessments and comprehensive reports.

---

## Class Definition

```python
class MammographyAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize a new MammographyAnalyzer object.
        :param image_analyzer: ImageAnalyzer instance for image processing
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `image_analyzer` | `ImageAnalyzer` | ImageAnalyzer instance for image processing. |
| `density_categories` | `Dict[str, str]` | BI-RADS density categories. |

---

## Methods

### Initialization
- **`__init__(self, image_analyzer)`**
  Initializes a new `MammographyAnalyzer` instance with the specified `ImageAnalyzer`.

---

### Mammogram Analysis
- **`analyze_mammogram(self, image, view="CC", laterality="L") -> Dict[str, Any]`**
  Performs comprehensive mammography analysis, including density, masses, calcifications, architectural distortions, and asymmetries.

  - **Parameters**:
    - `image`: Input mammographic image (ImageJ DataArray).
    - `view`: Mammographic view ('CC', 'MLO', 'ML', 'LM').
    - `laterality`: Breast laterality ('L' for left, 'R' for right).

  - **Returns**: Dictionary containing comprehensive analysis results.

---

### Preprocessing
- **`preprocess_mammogram(self, image) -> np.ndarray`**
  Preprocesses a mammographic image for optimal analysis.

  - **Parameters**:
    - `image`: Input mammographic image.

  - **Returns**: Preprocessed image.

---

### Breast Region Segmentation
- **`segment_breast_region(self, image) -> np.ndarray`**
  Segments the breast region from the background and artifacts.

  - **Parameters**:
    - `image`: Preprocessed mammographic image.

  - **Returns**: Binary mask of the breast region.

---

### Image Enhancement
- **`enhance_mammogram(self, image, breast_mask) -> np.ndarray`**
  Enhances a mammographic image for better feature visibility.

  - **Parameters**:
    - `image`: Preprocessed image.
    - `breast_mask`: Breast region mask.

  - **Returns**: Enhanced image.

---

### Breast Density Analysis
- **`analyze_breast_density(self, image, breast_mask) -> Dict[str, Any]`**
  Analyzes breast density according to BI-RADS categories.

  - **Parameters**:
    - `image`: Enhanced mammographic image.
    - `breast_mask`: Breast region mask.

  - **Returns**: Density analysis results.

---

### Mass Detection
- **`detect_masses(self, image, breast_mask) -> List[Dict[str, Any]]`**
  Detects potential masses in a mammographic image.

  - **Parameters**:
    - `image`: Enhanced image.
    - `breast_mask`: Breast region mask.

  - **Returns**: List of detected masses with properties.

---

### Calcification Detection
- **`detect_calcifications(self, image, breast_mask) -> List[Dict[str, Any]]`**
  Detects microcalcifications and macrocalcifications.

  - **Parameters**:
    - `image`: Enhanced image.
    - `breast_mask`: Breast region mask.

  - **Returns**: List of detected calcifications with properties.

---

### Architectural Distortion Detection
- **`detect_architectural_distortion(self, image, breast_mask) -> List[Dict[str, Any]]`**
  Detects architectural distortion patterns.

  - **Parameters**:
    - `image`: Enhanced image.
    - `breast_mask`: Breast region mask.

  - **Returns**: List of detected distortions with properties.

---

### Asymmetry Detection
- **`detect_asymmetries(self, image, breast_mask) -> List[Dict[str, Any]]`**
  Detects focal asymmetries and developing asymmetries.

  - **Parameters**:
    - `image`: Enhanced image.
    - `breast_mask`: Breast region mask.

  - **Returns**: List of detected asymmetries with properties.

---

### Skin Thickening Analysis
- **`analyze_skin_thickening(self, image, breast_mask) -> Dict[str, Any]`**
  Analyzes skin thickening, which can indicate inflammatory conditions.

  - **Parameters**:
    - `image`: Enhanced image.
    - `breast_mask`: Breast region mask.

  - **Returns**: Skin analysis results.

---

### Suspicion Assessment
- **`assess_mass_suspicion(self, circularity, contrast, area) -> str`**
  Assesses the suspicion level of a detected mass.

  - **Parameters**:
    - `circularity`: Mass circularity measure.
    - `contrast`: Mass contrast with surroundings.
    - `area`: Mass area.

  - **Returns**: Suspicion level string.

---

### Calcification Clustering Analysis
- **`analyze_calcification_clustering(self, calcifications) -> List[Dict[str, Any]]`**
  Analyzes clustering patterns of calcifications.

  - **Parameters**:
    - `calcifications`: List of detected calcifications.

  - **Returns**: Updated calcifications with clustering analysis.

---

### Duplicate Removal
- **`remove_duplicate_masses(self, masses, distance_threshold=30) -> List[Dict[str, Any]]`**
  Removes duplicate mass detections.

  - **Parameters**:
    - `masses`: List of detected masses.
    - `distance_threshold`: Minimum distance between masses.

  - **Returns**: Filtered list of masses.

- **`remove_overlapping_distortions(self, distortions, distance_threshold=50) -> List[Dict[str, Any]]`**
  Removes overlapping architectural distortion detections.

  - **Parameters**:
    - `distortions`: List of detected distortions.
    - `distance_threshold`: Minimum distance between distortions.

  - **Returns**: Filtered list of distortions.

---

### Cancer Risk Assessment
- **`calculate_cancer_risk(self, masses, calcifications, distortions, asymmetries) -> Dict[str, Any]`**
  Calculates overall cancer risk assessment.

  - **Parameters**:
    - `masses`: Detected masses.
    - `calcifications`: Detected calcifications.
    - `distortions`: Detected architectural distortions.
    - `asymmetries`: Detected asymmetries.

  - **Returns**: Risk assessment dictionary.

---

### Visualization
- **`visualize_mammography_analysis(self, analysis_results)`**
  Visualizes the results of mammography analysis.

  - **Parameters**:
    - `analysis_results`: Results from `analyze_mammogram` method.

---

### BI-RADS Assessment
- **`generate_birads_assessment(self, analysis_results) -> Dict[str, Any]`**
  Generates a BI-RADS assessment based on analysis results.

  - **Parameters**:
    - `analysis_results`: Results from `analyze_mammogram` method.

  - **Returns**: BI-RADS assessment dictionary.

---

### Breast Tissue Creation
- **`create_breast_tissue_from_mammogram(self, image, analysis_results, tissue_name: str) -> BoneTissue`**
  Creates a breast tissue representation from mammography analysis.

  - **Parameters**:
    - `image`: Original mammographic image.
    - `analysis_results`: Analysis results.
    - `tissue_name`: Name for the tissue.

  - **Returns**: Tissue object with mammography-derived properties.

---

### Bilateral Comparison
- **`compare_bilateral_mammograms(self, left_analysis, right_analysis) -> Dict[str, Any]`**
  Compares bilateral mammographic findings for asymmetry assessment.

  - **Parameters**:
    - `left_analysis`: Analysis results for the left breast.
    - `right_analysis`: Analysis results for the right breast.

  - **Returns**: Bilateral comparison results.

---

### Report Generation
- **`export_analysis_report(self, analysis_results, birads_assessment=None) -> str`**
  Exports a comprehensive analysis report.

  - **Parameters**:
    - `analysis_results`: Analysis results.
    - `birads_assessment`: Optional BI-RADS assessment.

  - **Returns**: Formatted report string.

---

## Example Usage

```python
# Initialize ImageAnalyzer
image_analyzer = ImageAnalyzer()

# Initialize MammographyAnalyzer
mammography_analyzer = MammographyAnalyzer(image_analyzer)

# Load a mammographic image
image = image_analyzer.load_image("path/to/mammogram.tif")

# Analyze the mammogram
analysis_results = mammography_analyzer.analyze_mammogram(image, view="CC", laterality="L")

# Visualize the mammography analysis
mammography_analyzer.visualize_mammography_analysis(analysis_results)

# Generate a BI-RADS assessment
birads_assessment = mammography_analyzer.generate_birads_assessment(analysis_results)
print(birads_assessment)

# Create a breast tissue object from the mammogram analysis
breast_tissue = mammography_analyzer.create_breast_tissue_from_mammogram(
    image, analysis_results, "Left Breast Tissue"
)
print(breast_tissue)

# Export an analysis report
report = mammography_analyzer.export_analysis_report(analysis_results, birads_assessment)
print(report)
```

---

## Dependencies
- **`cv2` (OpenCV)**: For image processing tasks such as filtering, edge detection, and segmentation.
- **`numpy`**: For numerical operations and array handling.
- **`scipy`**: For scientific computing and image processing.
- **`skimage`**: For image processing and analysis.
- **`sklearn.cluster.KMeans`**: For clustering-based segmentation.
- **`matplotlib`**: For visualization.
- **`biobridge.blocks.cell.Cell`**: For creating cell objects.
- **`biobridge.definitions.tissues.bone.BoneTissue`**: For creating tissue objects.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing and analysis.

---

## Notes
- The `MammographyAnalyzer` class is designed for advanced mammographic image analysis.
- It supports multiple mammographic views and provides detailed analysis of breast density, masses, calcifications, architectural distortions, and asymmetries.
- The `visualize_mammography_analysis` method provides a graphical representation of the analysis results.
- The `generate_birads_assessment` method generates a BI-RADS assessment based on the analysis results.
- The `create_breast_tissue_from_mammogram` method creates a tissue object based on the analysis results, which can be used for further biological simulations.
- The `export_analysis_report` method generates a comprehensive report suitable for clinical interpretation.
