# UltrasoundAnalyzer Class

---

## Overview
The `UltrasoundAnalyzer` class provides advanced tools for analyzing ultrasound images and volumes. It supports preprocessing, speckle noise reduction, contrast enhancement, echogenicity classification, anatomical structure detection, abnormality detection, and Doppler flow analysis. The class also includes visualization capabilities and methods for creating tissue objects from ultrasound analysis results.

---

## Class Definition

```python
class UltrasoundAnalyzer:
    def __init__(self, image_analyzer):
        """
        Initialize a new UltrasoundAnalyzer object.
        :param image_analyzer: ImageAnalyzer instance for image processing
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `image_analyzer` | `ImageAnalyzer` | ImageAnalyzer instance for image processing. |
| `echogenicity_ranges` | `Dict[str, Tuple[float, float]]` | Echogenicity ranges for different tissue types. |
| `frequency_penetration` | `Dict[str, Dict[str, Any]]` | Ultrasound frequency ranges and their penetration depths. |

---

## Methods

### Initialization
- **`__init__(self, image_analyzer)`**
  Initializes a new `UltrasoundAnalyzer` instance with the specified `ImageAnalyzer`.

---

### Ultrasound Analysis
- **`analyze_ultrasound(self, image_stack, frequency_mhz=7.5, depth_mm=100, gain_compensation=True, is_doppler=False) -> Dict[str, Any]`**
  Analyzes an ultrasound image or volume using specialized techniques.

  - **Parameters**:
    - `image_stack`: Input ultrasound data (2D image or 3D volume).
    - `frequency_mhz`: Transducer frequency in MHz.
    - `depth_mm`: Imaging depth in mm.
    - `gain_compensation`: Whether to apply time-gain compensation.
    - `is_doppler`: Whether this is Doppler ultrasound data.

  - **Returns**: Dictionary containing comprehensive analysis results.

---

### Time-Gain Compensation
- **`apply_time_gain_compensation(self, volume, depth_mm) -> np.ndarray`**
  Applies time-gain compensation to correct for attenuation with depth.

  - **Parameters**:
    - `volume`: Input ultrasound volume.
    - `depth_mm`: Maximum imaging depth in mm.

  - **Returns**: TGC-corrected volume.

---

### Speckle Noise Reduction
- **`reduce_speckle_noise(self, volume) -> np.ndarray`**
  Reduces speckle noise while preserving edges using adaptive filtering.

  - **Parameters**:
    - `volume`: Input ultrasound volume.

  - **Returns**: Despeckled volume.

---

### Contrast Enhancement
- **`enhance_ultrasound_contrast(self, volume) -> np.ndarray`**
  Enhances contrast using CLAHE and other techniques.

  - **Parameters**:
    - `volume`: Input volume.

  - **Returns**: Enhanced volume.

---

### Echogenicity Classification
- **`classify_echogenicity(self, volume) -> Dict[str, np.ndarray]`**
  Classifies pixels by echogenicity level.

  - **Parameters**:
    - `volume`: Enhanced ultrasound volume.

  - **Returns**: Dictionary of echogenicity masks.

---

### Acoustic Property Analysis
- **`analyze_acoustic_properties(self, volume) -> Dict[str, Any]`**
  Analyzes acoustic shadows and enhancements.

  - **Parameters**:
    - `volume`: Enhanced ultrasound volume.

  - **Returns**: Dictionary of acoustic property analysis.

---

### Edge Detection
- **`detect_ultrasound_edges(self, volume) -> np.ndarray`**
  Detects edges optimized for ultrasound imaging characteristics.

  - **Parameters**:
    - `volume`: Enhanced ultrasound volume.

  - **Returns**: Edge map.

---

### Anatomical Structure Detection
- **`detect_anatomical_structures(self, volume, echogenicity_map, frequency_mhz) -> Dict[str, List[Dict[str, Any]]]`**
  Detects common anatomical structures based on echogenicity patterns.

  - **Parameters**:
    - `volume`: Enhanced ultrasound volume.
    - `echogenicity_map`: Echogenicity classification.
    - `frequency_mhz`: Ultrasound frequency.

  - **Returns**: Dictionary of detected structures.

---

### Ultrasound Measurements
- **`perform_ultrasound_measurements(self, structure_detection) -> Dict[str, List[Dict[str, Any]]]`**
  Performs standard ultrasound measurements.

  - **Parameters**:
    - `structure_detection`: Detected anatomical structures.

  - **Returns**: Dictionary of measurements.

---

### Abnormality Detection
- **`detect_ultrasound_abnormalities(self, volume, echogenicity_map, structure_detection) -> List[Dict[str, Any]]`**
  Detects potential abnormalities in ultrasound images.

  - **Parameters**:
    - `volume`: Enhanced ultrasound volume.
    - `echogenicity_map`: Echogenicity classification.
    - `structure_detection`: Detected anatomical structures.

  - **Returns**: List of potential abnormalities.

---

### Doppler Flow Analysis
- **`analyze_doppler_flow(self, volume) -> Dict[str, Any]`**
  Analyzes Doppler flow patterns for blood flow assessment.

  - **Parameters**:
    - `volume`: Doppler ultrasound volume.

  - **Returns**: Flow analysis results.

---

### Texture Analysis
- **`analyze_ultrasound_texture(self, volume) -> Dict[str, Any]`**
  Analyzes texture features for tissue characterization.

  - **Parameters**:
    - `volume`: Enhanced ultrasound volume.

  - **Returns**: Texture feature analysis.

---

### Visualization
- **`visualize_ultrasound_analysis(self, analysis_results, slice_index=None)`**
  Visualizes ultrasound analysis results.

  - **Parameters**:
    - `analysis_results`: Results from `analyze_ultrasound` method.
    - `slice_index`: Index of slice to visualize (None for 2D or middle slice).

---

### Tissue Creation
- **`create_tissue_from_ultrasound(self, volume, echogenicity_map, structure_detection, tissue_type="muscle", tissue_name="UltrasoundTissue") -> Union[MuscleTissue, OrganTissue]`**
  Creates tissue objects from ultrasound analysis results.

  - **Parameters**:
    - `volume`: Enhanced ultrasound volume.
    - `echogenicity_map`: Echogenicity classification.
    - `structure_detection`: Detected structures.
    - `tissue_type`: Type of tissue to create ("muscle", "organ").
    - `tissue_name`: Name for the tissue.

  - **Returns**: Tissue object.

---

### Real-Time Analysis
- **`perform_real_time_analysis(self, image_stream, analysis_params=None) -> Generator[Dict[str, Any], None, None]`**
  Performs real-time ultrasound analysis on a stream of images.

  - **Parameters**:
    - `image_stream`: Generator or iterator of ultrasound images.
    - `analysis_params`: Dictionary of analysis parameters.

  - **Returns**: Generator of real-time analysis results.

- **`quick_ultrasound_analysis(self, frame) -> Dict[str, Any]`**
  Performs quick analysis suitable for real-time processing.

  - **Parameters**:
    - `frame`: Single ultrasound frame.

  - **Returns**: Quick analysis results.

---

### Motion Detection
- **`detect_motion(self, previous_frame, current_frame) -> Dict[str, Any]`**
  Detects motion between consecutive ultrasound frames.

  - **Parameters**:
    - `previous_frame`: Previous ultrasound frame.
    - `current_frame`: Current ultrasound frame.

  - **Returns**: Motion detection results.

---

### Structural Change Detection
- **`detect_structural_changes(self, previous_frame, current_frame) -> Dict[str, Any]`**
  Detects structural changes between frames.

  - **Parameters**:
    - `previous_frame`: Previous ultrasound frame.
    - `current_frame`: Current ultrasound frame.

  - **Returns**: Structural change analysis.

---

### Image Quality Assessment
- **`assess_image_quality(self, frame) -> Dict[str, Any]`**
  Assesses the quality of an ultrasound image.

  - **Parameters**:
    - `frame`: Ultrasound frame.

  - **Returns**: Quality metrics.

---

### Calibration
- **`calibrate_measurements(self, pixel_size_mm=None, depth_calibration=None) -> Dict[str, Any]`**
  Calibrates pixel measurements to physical units.

  - **Parameters**:
    - `pixel_size_mm`: Size of one pixel in mm.
    - `depth_calibration`: Depth calibration parameters.

  - **Returns**: Calibration parameters.

---

### DICOM Export
- **`export_measurements_to_dicom(self, analysis_results, patient_info=None) -> Dict[str, Any]`**
  Exports measurements in DICOM-like format.

  - **Parameters**:
    - `analysis_results`: Results from ultrasound analysis.
    - `patient_info`: Patient information dictionary.

  - **Returns**: Dictionary with DICOM-like measurement data.

---

## Example Usage

```python
# Initialize ImageAnalyzer
image_analyzer = ImageAnalyzer()

# Initialize UltrasoundAnalyzer
ultrasound_analyzer = UltrasoundAnalyzer(image_analyzer)

# Load an ultrasound image
image = image_analyzer.load_image("path/to/ultrasound_image.tif")

# Analyze the ultrasound image
analysis_results = ultrasound_analyzer.analyze_ultrasound(image, frequency_mhz=7.5, depth_mm=100)

# Visualize the ultrasound analysis
ultrasound_analyzer.visualize_ultrasound_analysis(analysis_results)

# Create a tissue object from the ultrasound analysis
muscle_tissue = ultrasound_analyzer.create_tissue_from_ultrasound(
    analysis_results["enhanced_volume"],
    analysis_results["echogenicity_map"],
    analysis_results["structure_detection"],
    tissue_type="muscle",
    tissue_name="Bicep Tissue"
)
print(muscle_tissue)

# Perform real-time ultrasound analysis
def image_generator():
    for i in range(10):
        yield image_analyzer.load_image(f"path/to/ultrasound_frame_{i}.tif")

real_time_results = ultrasound_analyzer.perform_real_time_analysis(image_generator())
for result in real_time_results:
    print(result)

# Export measurements to DICOM-like format
dicom_data = ultrasound_analyzer.export_measurements_to_dicom(analysis_results)
print(dicom_data)
```

---

## Dependencies
- **`numpy`**: For numerical operations and array handling.
- **`scipy`**: For scientific computing and image processing.
- **`skimage`**: For image processing and analysis.
- **`matplotlib`**: For visualization.
- **`biobridge.blocks.cell.Cell`**: For creating cell objects.
- **`biobridge.definitions.tissues.muscle.MuscleTissue`**: For creating muscle tissue objects.
- **`biobridge.definitions.tissues.organ.OrganTissue`**: For creating organ tissue objects.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing and analysis.

---

## Notes
- The `UltrasoundAnalyzer` class is designed for advanced ultrasound image analysis.
- It supports both 2D and 3D ultrasound data.
- The class provides detailed analysis of echogenicity, anatomical structures, and abnormalities.
- The `visualize_ultrasound_analysis` method provides a graphical representation of the analysis results.
- The `create_tissue_from_ultrasound` method creates tissue objects based on the analysis results, which can be used for further biological simulations.
- The `perform_real_time_analysis` method allows for real-time analysis of ultrasound image streams.
