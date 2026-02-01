# SPECTScanAnalyzer Class

---

## Overview
The `SPECTScanAnalyzer` class provides tools for analyzing Single Photon Emission Computed Tomography (SPECT) scans. It supports various analyses such as activity segmentation, anomaly detection, uptake pattern analysis, and quantitative metrics calculation. The class can generate detailed reports and create activity-based tissue analyses.

---

## Class Definition

```python
class SPECTScanAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize a new SPECTScanAnalyzer object.
        :param image_analyzer: Image analyzer object for handling image data
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `image_analyzer` | `Any` | Image analyzer object for handling image data. |
| `activity_ranges` | `Dict[str, Tuple[float, float]]` | SPECT intensity ranges for different activity levels. |
| `tracer_properties` | `Dict[str, Dict[str, Any]]` | Properties of common SPECT tracers. |

---

## Methods

### Initialization
- **`__init__(self, image_analyzer)`**
  Initializes a new `SPECTScanAnalyzer` instance with the specified image analyzer.

---

### SPECT Scan Analysis
- **`analyze_spect_scan(self, image_stack, tracer_type="Tc-99m_MDP", slice_thickness=5.0) -> Dict[str, Any]`**
  Analyzes a SPECT scan volume.

  - **Parameters**:
    - `image_stack`: Input SPECT scan volume (3D array or list of 2D slices).
    - `tracer_type`: Type of radiotracer used.
    - `slice_thickness`: Thickness of each slice in millimeters.

  - **Returns**: A dictionary containing SPECT analysis results.

---

### Volume Processing
- **`normalize_spect_volume(self, volume) -> np.ndarray`**
  Normalizes a SPECT volume to the 0-1 range.

  - **Parameters**:
    - `volume`: SPECT volume to normalize.

  - **Returns**: Normalized SPECT volume.

- **`enhance_spect_volume(self, normalized_volume) -> np.ndarray`**
  Enhances a SPECT volume using filtering techniques.

  - **Parameters**:
    - `normalized_volume`: Normalized SPECT volume to enhance.

  - **Returns**: Enhanced SPECT volume.

---

### Activity Segmentation
- **`segment_activity_regions(self, normalized_volume, tracer_type) -> Dict[str, np.ndarray]`**
  Segments different activity regions based on normalized intensity values.

  - **Parameters**:
    - `normalized_volume`: Normalized SPECT volume.
    - `tracer_type`: Type of radiotracer used.

  - **Returns**: Dictionary containing segmented activity regions.

---

### Edge and Anomaly Detection
- **`detect_activity_edges(self, enhanced_volume) -> np.ndarray`**
  Detects activity boundaries and transitions.

  - **Parameters**:
    - `enhanced_volume`: Enhanced SPECT volume.

  - **Returns**: Binary array indicating edges.

- **`detect_activity_anomalies(self, normalized_volume) -> List[Dict[str, Any]]`**
  Detects activity anomalies using statistical analysis.

  - **Parameters**:
    - `normalized_volume`: Normalized SPECT volume.

  - **Returns**: List of detected anomalies with their properties.

- **`_classify_activity_anomaly(self, activity_value) -> str`**
  Classifies an activity anomaly based on normalized intensity.

  - **Parameters**:
    - `activity_value`: Normalized activity value.

  - **Returns**: Classification of the anomaly.

---

### Activity Measurements
- **`calculate_activity_measurements(self, activity_segmentation, normalized_volume, slice_thickness) -> Dict[str, Dict[str, float]]`**
  Calculates activity measurements for different regions.

  - **Parameters**:
    - `activity_segmentation`: Segmented activity regions.
    - `normalized_volume`: Normalized SPECT volume.
    - `slice_thickness`: Thickness of each slice in millimeters.

  - **Returns**: Dictionary containing activity measurements for each region.

---

### Uptake Pattern Analysis
- **`analyze_uptake_patterns(self, normalized_volume, tracer_type) -> Dict[str, float]`**
  Analyzes uptake patterns specific to the tracer type.

  - **Parameters**:
    - `normalized_volume`: Normalized SPECT volume.
    - `tracer_type`: Type of radiotracer used.

  - **Returns**: Dictionary containing uptake pattern analysis results.

---

### Hotspot and Coldspot Detection
- **`detect_activity_spots(self, normalized_volume, tracer_type) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`**
  Detects hotspots and coldspots based on tracer type.

  - **Parameters**:
    - `normalized_volume`: Normalized SPECT volume.
    - `tracer_type`: Type of radiotracer used.

  - **Returns**: Tuple containing lists of hotspots and coldspots with their properties.

---

### Quantitative Metrics
- **`calculate_quantitative_metrics(self, normalized_volume, tracer_type) -> Dict[str, float]`**
  Calculates standard quantitative SPECT metrics.

  - **Parameters**:
    - `normalized_volume`: Normalized SPECT volume.
    - `tracer_type`: Type of radiotracer used.

  - **Returns**: Dictionary containing quantitative metrics.

---

### Tissue Analysis
- **`create_activity_tissue_analysis(self, normalized_volume, hotspots, coldspots, tissue_name, tracer_type) -> Dict[str, Any]`**
  Creates an activity-based tissue analysis from SPECT scan results.

  - **Parameters**:
    - `normalized_volume`: Normalized SPECT volume.
    - `hotspots`: List of detected hotspots.
    - `coldspots`: List of detected coldspots.
    - `tissue_name`: Name of the tissue.
    - `tracer_type`: Type of radiotracer used.

  - **Returns**: Dictionary containing tissue analysis results.

---

### Report Generation
- **`generate_spect_report(self, analysis_results) -> str`**
  Generates a comprehensive SPECT scan report.

  - **Parameters**:
    - `analysis_results`: Results from SPECT scan analysis.

  - **Returns**: String containing the SPECT scan report.

---

## Example Usage

```python
# Initialize the SPECTScanAnalyzer
spect_analyzer = SPECTScanAnalyzer(image_analyzer)

# Sample SPECT scan data
image_stack = [np.random.rand(100, 100) for _ in range(20)]

# Analyze the SPECT scan
analysis_results = spect_analyzer.analyze_spect_scan(image_stack, tracer_type="Tc-99m_MDP")

# Generate a SPECT report
report = spect_analyzer.generate_spect_report(analysis_results)
print(report)

# Create an activity-based tissue analysis
tissue_analysis = spect_analyzer.create_activity_tissue_analysis(
    analysis_results["normalized_volume"],
    analysis_results["hotspots"],
    analysis_results["coldspots"],
    "Bone Tissue",
    "Tc-99m_MDP"
)
print(tissue_analysis)
```

---

## Dependencies
- **`numpy`**: For numerical operations and array handling.
- **`scipy.ndimage`**: For image processing functions.
- **`skimage`**: For image filtering, measurement, and morphology operations.
- **`sklearn.ensemble.IsolationForest`**: For anomaly detection.
- **`sklearn.preprocessing.StandardScaler`**: For feature normalization.
- **`biobridge.blocks.cell.Cell`**: For creating cell objects in tissue analysis.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during analysis.
- The `detect_activity_anomalies` method includes a check for empty feature sets.

---

## Notes
- The `SPECTScanAnalyzer` class is designed for advanced SPECT scan analysis.
- It supports multiple tracer types and provides detailed analysis of activity patterns.
- The `generate_spect_report` method creates a comprehensive report suitable for clinical interpretation.
- The class can create activity-based tissue analyses, which can be useful for further biological simulations.
