# ImageAnalyzer Class

---

## Overview
The `ImageAnalyzer` class provides a suite of tools for analyzing biological images, including cell and tissue analysis, protein structure analysis, X-ray image analysis, and **neuron morphology and connectivity analysis**. It integrates with ImageJ for image processing and uses machine learning for protein classification.

---

## Class Definition

```python
class ImageAnalyzer:
    def __init__(self):
        """
        Initialize the ImageAnalyzer with ImageJ.
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `ij` | `imagej.ImageJ` | ImageJ instance for image processing. |
| `labeled_tissue` | `str` | Label for the analyzed tissue. |
| `xray_analyzer` | `XrayAnalyzer` | X-ray image analyzer. |
| `protein_classifier` | `RandomForestClassifier` | Machine learning classifier for protein types. |
| `scaler` | `StandardScaler` | Scaler for normalizing features for the protein classifier. |

---

## Methods

### Initialization
- **`__init__(self)`**
  Initializes a new `ImageAnalyzer` instance with ImageJ.

---

### Image Loading and Processing
- **`load_image(self, image_path: str)`**
  Loads an image using ImageJ.

  - **Parameters**:
    - `image_path`: Path to the image file.

  - **Returns**: ImageJ dataset.

- **`segment_image(self, imagej_dataset)`**
  Segments an image to identify individual cells or regions.

  - **Parameters**:
    - `imagej_dataset`: ImageJ dataset to segment.

  - **Returns**: Tuple of labeled image and number of labels.

- **`grayscale_image(self, image)`**
  Converts an image to grayscale.

  - **Parameters**:
    - `image`: ImageJ dataset to convert.

  - **Returns**: Grayscale ImageJ dataset.

---

### Fluorescence Analysis
- **`measure_fluorescence(self, image)`**
  Measures fluorescence intensity in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to measure.

  - **Returns**: Dictionary containing mean and max intensity.

---

### Cell and Nuclei Analysis
- **`analyze_nuclei(self, image)`**
  Analyzes nuclei in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.

  - **Returns**: List of nuclei properties.

- **`analyze_mitochondria(self, image)`**
  Analyzes mitochondria in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.

  - **Returns**: List of mitochondria properties.

- **`detect_potential_cancer(self, image, nuclei_data)`**
  Detects potential cancer cells based on nuclear characteristics.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `nuclei_data`: List of nuclei properties.

  - **Returns**: List of potential cancer cells.

---

### Cell Tracking
- **`track_cell_movement(self, image_sequence)`**
  Tracks cell movement across a sequence of images.

  - **Parameters**:
    - `image_sequence`: Sequence of ImageJ datasets.

  - **Returns**: List of tracked cells with their trajectories.

---

### Object Identification
- **`identify_primary_objects(self, image, min_diameter=10, max_diameter=100)`**
  Identifies primary objects (e.g., nuclei) in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `min_diameter`: Minimum diameter of objects to consider.
    - `max_diameter`: Maximum diameter of objects to consider.

  - **Returns**: Labeled image of primary objects.

- **`identify_secondary_objects(self, primary_objects, distance=5)`**
  Identifies secondary objects (e.g., cell bodies) based on primary objects.

  - **Parameters**:
    - `primary_objects`: Labeled image of primary objects.
    - `distance`: Maximum distance to expand from primary objects.

  - **Returns**: Labeled image of secondary objects.

- **`identify_tertiary_objects(self, secondary_objects, primary_objects)`**
  Identifies tertiary objects (e.g., cytoplasm) as the difference between secondary and primary objects.

  - **Parameters**:
    - `secondary_objects`: Labeled image of secondary objects.
    - `primary_objects`: Labeled image of primary objects.

  - **Returns**: Labeled image of tertiary objects.

---

### Property Measurement
- **`measure_object_properties(self, labeled_image, intensity_image)`**
  Measures properties of labeled objects.

  - **Parameters**:
    - `labeled_image`: Labeled image of objects.
    - `intensity_image`: Original intensity image.

  - **Returns**: List of dictionaries containing object properties.

---

### Cellular Analysis
- **`analyze_cellular_objects(self, image)`**
  Performs a complete analysis of cellular objects in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.

  - **Returns**: Dictionary containing analysis results.

- **`analyze_cells(self, image, dna: Optional[str] = None)`**
  Analyzes cells in an image and creates Cell objects.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `dna`: Optional DNA sequence.

  - **Returns**: List of Cell objects.

- **`determine_cell_type(self, nucleus_props: Dict, cell_props: Dict, cytoplasm_props: Dict) -> str`**
  Determines the cell type based on measured properties.

  - **Parameters**:
    - `nucleus_props`: Properties of the nucleus.
    - `cell_props`: Properties of the cell body.
    - `cytoplasm_props`: Properties of the cytoplasm.

  - **Returns**: Determined cell type.

- **`create_cell_object(self, index: int, cell_type: str, cell_props: Dict, cytoplasm_props: Dict, dna: Optional[str] = None) -> Cell`**
  Creates a Cell object based on measured properties.

  - **Parameters**:
    - `index`: Index of the cell.
    - `cell_type`: Determined cell type.
    - `cell_props`: Properties of the cell body.
    - `cytoplasm_props`: Properties of the cytoplasm.
    - `dna`: Optional DNA sequence.

  - **Returns**: Cell object.

---

### Tissue Analysis
- **`analyze_tissue(self, image)`**
  Analyzes tissue structure in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.

  - **Returns**: List of tissue properties.

- **`determine_tissue_type(self, tissue_props) -> str`**
  Determines the tissue type based on measured properties.

  - **Parameters**:
    - `tissue_props`: Properties of the tissue segment.

  - **Returns**: Determined tissue type.

- **`create_tissue_object(self, index: int, tissue_type: str, tissue_props, cells: List[Cell]) -> Tissue`**
  Creates a Tissue object based on measured properties.

  - **Parameters**:
    - `index`: Index of the tissue segment.
    - `tissue_type`: Determined tissue type.
    - `tissue_props`: Properties of the tissue segment.
    - `cells`: List of Cell objects within this tissue.

  - **Returns**: Tissue object.

- **`analyze_cells_for_tissue(self, image)`**
  Analyzes cells in an image and creates Cell objects for tissue analysis.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.

  - **Returns**: Tuple of list of Cell objects and their corresponding binary masks.

- **`analyze_and_create_tissues(self, image_path: str) -> List[Tissue]`**
  Analyzes an image and creates Tissue objects based on the analysis.

  - **Parameters**:
    - `image_path`: Path to the image file.

  - **Returns**: List of Tissue objects.

- **`cell_in_tissue(self, cell_mask, tissue_mask) -> bool`**
  Determines if a cell is within a given tissue segment.

  - **Parameters**:
    - `cell_mask`: Binary mask of the cell.
    - `tissue_mask`: Binary mask of the tissue segment.

  - **Returns**: Boolean indicating if the cell is within the tissue segment.

---

### Drug Detection
- **`detect_drugged_cell(self, image, cell_props: Dict) -> bool`**
  Detects if a cell was drugged based on its properties.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `cell_props`: Properties of the cell.

  - **Returns**: Boolean indicating if the cell is drugged.

---

### Visualization
- **`visualize_mitochondria(self, image, mitochondria_data)`**
  Visualizes mitochondria in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `mitochondria_data`: List of mitochondria properties.

- **`visualize_nuclei(self, image, nuclei_data)`**
  Visualizes nuclei in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `nuclei_data`: List of nuclei properties.

- **`visualize_cancer_cells(self, image, cancer_cells)`**
  Visualizes potential cancer cells in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `cancer_cells`: List of potential cancer cells.

- **`visualize_grayscale_image(self, image)`**
  Visualizes a grayscale image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.

- **`visualize_network_image(self, image_path, analysis_result)`**
  Visualizes the analysis of a network image.

  - **Parameters**:
    - `image_path`: Path to the network image.
    - `analysis_result`: Dictionary containing nodes, edges, and their properties.

- **`visualise_fluorescence(self, image, fluorescence_data)`**
  Visualizes fluorescence data in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `fluorescence_data`: List of fluorescence properties.

- **`plot_trajectories(self, tracked_cells, image)`**
  Plots the trajectories of tracked cells.

  - **Parameters**:
    - `tracked_cells`: List of tracked cells with their trajectories.
    - `image`: ImageJ dataset to visualize.

- **`visualize_primary_objects(self, image, primary_objects)`**
  Visualizes primary objects in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `primary_objects`: List of primary objects.

- **`visualize_secondary_objects(self, image, secondary_objects)`**
  Visualizes secondary objects in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `secondary_objects`: List of secondary objects.

- **`visualize_tertiary_objects(self, image, tertiary_objects)`**
  Visualizes tertiary objects in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `tertiary_objects`: List of tertiary objects.

- **`visualize_measured_properties(self, image, measured_properties)`**
  Visualizes measured properties in an image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `measured_properties`: List of measured properties.

- **`visualise_segmented_image(self, image, labeled_img, num_labels)`**
  Visualizes a segmented image.

  - **Parameters**:
    - `image`: ImageJ dataset to visualize.
    - `labeled_img`: Labeled image.
    - `num_labels`: Number of labels.

- **`display_cells(self, cells)`**
  Displays cells using matplotlib.

  - **Parameters**:
    - `cells`: List of Cell objects.

---

### Protein Analysis
- **`load_protein_structure(self, pdb_file)`**
  Loads a protein structure from a PDB file.

  - **Parameters**:
    - `pdb_file`: Path to the PDB file.

  - **Returns**: PyRosetta Pose object.

- **`analyze_protein_structure(self, pose)`**
  Analyzes the protein structure.

  - **Parameters**:
    - `pose`: PyRosetta Pose object.

  - **Returns**: Dictionary with structure analysis results.

- **`design_protein(self, pose, design_xml)`**
  Performs protein design using RosettaScripts.

  - **Parameters**:
    - `pose`: PyRosetta Pose object.
    - `design_xml`: XML string with RosettaScripts protocol.

  - **Returns**: Designed PyRosetta Pose object.

- **`dock_proteins(self, pose_receptor, pose_ligand)`**
  Performs protein-protein docking.

  - **Parameters**:
    - `pose_receptor`: PyRosetta Pose object of the receptor.
    - `pose_ligand`: PyRosetta Pose object of the ligand.

  - **Returns**: Docked PyRosetta Pose object.

- **`train_protein_classifier(self, training_data)`**
  Trains a Random Forest classifier for protein type prediction.

  - **Parameters**:
    - `training_data`: List of dictionaries, each containing 'features' and 'protein_type'.

- **`extract_features(self, structure_analysis)`**
  Extracts relevant features from the structure analysis for the ML model.

  - **Parameters**:
    - `structure_analysis`: Dictionary with structure analysis results.

  - **Returns**: Numpy array of features.

- **`analyze_and_create_protein(self, image_path: str, pdb_file: str) -> Protein`**
  Analyzes a protein image and creates a Protein object based on the analysis.

  - **Parameters**:
    - `image_path`: Path to the protein image file.
    - `pdb_file`: Path to the PDB file of the protein.

  - **Returns**: Protein object.

- **`determine_protein_type(self, structure_analysis)`**
  Determines protein type based on structure analysis.

  - **Parameters**:
    - `structure_analysis`: Dictionary with structure analysis results.

  - **Returns**: Predicted protein type.

- **`determine_protein_characteristics(self, structure_analysis, protein_type)`**
  Determines protein interactions and bindings based on structure analysis and protein type.

  - **Parameters**:
    - `structure_analysis`: Dictionary with structure analysis results.
    - `protein_type`: Predicted protein type.

  - **Returns**: Tuple of (interactions, bindings).

---

### X-ray Analysis
- **`analyze_xray(self, image_path)`**
  Analyzes an X-ray image.

  - **Parameters**:
    - `image_path`: Path to the X-ray image file.

  - **Returns**: Dictionary containing analysis results.

- **`visualize_xray_analysis(self, image_path, analysis_results)`**
  Visualizes the results of X-ray analysis.

  - **Parameters**:
    - `image_path`: Path to the original X-ray image file.
    - `analysis_results`: Results from analyze_xray method.

---

### Neuron Morphology and Connectivity Analysis

- **`analyze_neuron_morphology(self, image, nucleus_props: Dict, cell_props: Dict) -> Dict[str, float]`**
  Analyzes the morphology of a neuron, including soma, processes, and branching.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `nucleus_props`: Properties of the nucleus.
    - `cell_props`: Properties of the cell body.

  - **Returns**: Dictionary containing morphology metrics.

- **`_detect_branch_points(self, skeleton)`**
  Detects branch points in a skeletonized image.

  - **Parameters**:
    - `skeleton`: Skeletonized image.

  - **Returns**: Binary image of branch points.

- **`estimate_myelination(self, image, cell_props: Dict) -> Dict[str, float]`**
  Estimates myelination properties of a neuron.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `cell_props`: Properties of the cell body.

  - **Returns**: Dictionary containing myelination metrics.

- **`analyze_synaptic_markers(self, image, cell_props: Dict) -> Dict[str, any]`**
  Analyzes synaptic markers in a neuron.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `cell_props`: Properties of the cell body.

  - **Returns**: Dictionary containing synaptic marker metrics.

- **`classify_neuron_type(self, morphology_data: Dict, synapse_data: Dict, myelination_data: Dict) -> str`**
  Classifies the neuron type based on morphology, synapse, and myelination data.

  - **Parameters**:
    - `morphology_data`: Morphology metrics.
    - `synapse_data`: Synaptic marker metrics.
    - `myelination_data`: Myelination metrics.

  - **Returns**: Neuron type as a string.

- **`estimate_neurotransmitter_type(self, image, cell_props: Dict) -> List[str]`**
  Estimates the neurotransmitter type(s) of a neuron.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `cell_props`: Properties of the cell body.

  - **Returns**: List of neurotransmitter types.

- **`analyze_mitochondrial_distribution_neuron(self, image, cell_props: Dict) -> Dict[str, float]`**
  Analyzes mitochondrial distribution in a neuron.

  - **Parameters**:
    - `image`: ImageJ dataset to analyze.
    - `cell_props`: Properties of the cell body.

  - **Returns**: Dictionary containing mitochondrial distribution metrics.

- **`create_neuron_object(self, index: int, cell_props: Dict, nucleus_props: Dict, image, dna: Optional[str] = None) -> Neuron`**
  Creates a Neuron object based on measured properties.

  - **Parameters**:
    - `index`: Index of the neuron.
    - `cell_props`: Properties of the cell body.
    - `nucleus_props`: Properties of the nucleus.
    - `image`: ImageJ dataset to analyze.
    - `dna`: Optional DNA sequence.

  - **Returns**: Neuron object.

- **`create_neural_tissue_object(self, index: int, tissue_type: str, tissue_props: Dict, neurons: List[Neuron]) -> NeuralTissue`**
  Creates a NeuralTissue object based on measured properties.

  - **Parameters**:
    - `index`: Index of the neural tissue.
    - `tissue_type`: Type of the neural tissue.
    - `tissue_props`: Properties of the neural tissue.
    - `neurons`: List of Neuron objects within this tissue.

  - **Returns**: NeuralTissue object.

- **`analyze_neural_connectivity_patterns(self, neurons_props: List[Dict]) -> Dict[str, any]`**
  Analyzes neural connectivity patterns among neurons.

  - **Parameters**:
    - `neurons_props`: List of neuron properties.

  - **Returns**: Dictionary containing connectivity matrix and network metrics.

---

### Cleanup
- **`close(self)`**
  Closes the ImageJ instance.

---

## Example Usage

```python
# Initialize the ImageAnalyzer
analyzer = ImageAnalyzer()

# Load an image
image = analyzer.load_image("path/to/image.tif")

# Segment the image
labeled_img, num_labels = analyzer.segment_image(image)

# Analyze nuclei
nuclei_data = analyzer.analyze_nuclei(image)

# Analyze mitochondria
mitochondria_data = analyzer.analyze_mitochondria(image)

# Detect potential cancer cells
cancer_cells = analyzer.detect_potential_cancer(image, nuclei_data)

# Analyze and create cells
cells = analyzer.analyze_cells(image)

# Analyze and create tissues
tissues = analyzer.analyze_and_create_tissues("path/to/image.tif")

# Visualize mitochondria
analyzer.visualize_mitochondria(image, mitochondria_data)

# Visualize nuclei
analyzer.visualize_nuclei(image, nuclei_data)

# Visualize cancer cells
analyzer.visualize_cancer_cells(image, cancer_cells)

# Load a protein structure
pose = analyzer.load_protein_structure("path/to/protein.pdb")

# Analyze protein structure
structure_analysis = analyzer.analyze_protein_structure(pose)

# Analyze and create a protein
protein = analyzer.analyze_and_create_protein("path/to/protein_image.tif", "path/to/protein.pdb")

# Analyze an X-ray image
xray_results = analyzer.analyze_xray("path/to/xray_image.tif")

# Visualize X-ray analysis
analyzer.visualize_xray_analysis("path/to/xray_image.tif", xray_results)

# Close the ImageJ instance
analyzer.close()
```

---

## Dependencies
- **`imagej`**: For image processing and analysis.
- **`numpy`**: For numerical operations and array handling.
- **`scipy`**: For scientific computing and image processing.
- **`skimage`**: For image processing and analysis.
- **`sklearn`**: For machine learning and data preprocessing.
- **`cv2` (OpenCV)**: For computer vision tasks.
- **`matplotlib`**: For visualization.
- **`pyrosetta`**: For protein structure analysis and design.
- **`biobridge.blocks.cell.Cell`**: For creating cell objects.
- **`biobridge.blocks.tissue.Tissue`**: For creating tissue objects.
- **`biobridge.blocks.protein.Protein`**: For creating protein objects.
- **`biobridge.blocks.neuron.Neuron`**: For creating neuron objects.
- **`biobridge.blocks.neural_tissue.NeuralTissue`**: For creating neural tissue objects.
- **`biobridge.tools.xray_analyzer.XrayAnalyzer`**: For X-ray image analysis.

---

## Error Handling
- The class includes checks for valid input data and handles potential errors during image processing and analysis.
- The `visualise_fluorescence` and related visualization methods include error handling for JSON parsing.

---

## Notes
- The `ImageAnalyzer` class is designed for advanced biological image analysis, including neuron morphology and connectivity.
- It supports a wide range of analyses, including cell and tissue analysis, protein structure analysis, X-ray image analysis, and neural network analysis.
- The class integrates with ImageJ for image processing and uses machine learning for protein classification.
- Visualization methods provide graphical representations of analysis results.
