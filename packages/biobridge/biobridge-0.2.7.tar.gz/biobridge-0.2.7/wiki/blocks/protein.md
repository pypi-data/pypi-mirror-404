# Protein Class

## Overview
The `Protein` class simulates the structure, properties, interactions, and mutations of biological proteins. It supports sequence analysis, structure prediction, interaction simulation, and 3D visualization.

---

## Class Definition

```python
class Protein:
    def __init__(self, name, sequence, structure=None, secondary_structure=None, id=None, description=None, annotations=None):
        """
        Initialize a new Protein object.
        :param name: Name of the protein
        :param sequence: Sequence of amino acids (as a string of single-letter codes)
        :param structure: Tertiary structure of the protein (optional)
        :param secondary_structure: Secondary structure of the protein (optional)
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the protein. |
| `sequence` | `str` | Amino acid sequence (single-letter codes). |
| `structure` | `Optional[pyrosetta.Pose]` | Tertiary structure of the protein. |
| `secondary_structure` | `Optional[str]` | Secondary structure of the protein. |
| `interactions` | `List[dict]` | List of protein-protein interactions. |
| `id` | `Optional[str]` | Unique identifier for the protein. |
| `description` | `Optional[str]` | Description of the protein. |
| `annotations` | `Optional[dict]` | Annotations for the protein. |
| `bindings` | `List[dict]` | List of binding sites and their affinities. |
| `mutation_probabilities` | `Dict[str, float]` | Mutation probabilities for each amino acid. |
| `protein_analysis` | `ProteinAnalysis` | BioPython ProteinAnalysis object for sequence properties. |

---

## Methods

### Initialization
- **`__init__(self, name, sequence, structure=None, secondary_structure=None, id=None, description=None, annotations=None)`**
  Initializes a new `Protein` instance with the specified attributes.

---

### Mutation Methods
- **`absolute_mutate(self, position, new_amino_acid, probability)`**
  Mutates the sequence at a specific position with an absolute probability.

- **`mutate_sequence(self, position, new_amino_acid)`**
  Mutates the sequence at a specific position based on amino acid-specific probabilities.

- **`random_absolute_mutate(self, probability)`**
  Randomly mutates the sequence with an absolute probability.

- **`random_mutate(self)`**
  Randomly mutates the sequence based on amino acid-specific probabilities.

---

### Interaction Management
- **`add_interaction(self, other_protein, interaction_type, strength)`**
  Adds an interaction with another protein.

- **`remove_interaction(self, other_protein)`**
  Removes an interaction with another protein.

- **`add_binding(self, binding_site, affinity)`**
  Adds a binding site with a specified affinity.

- **`update_binding(self, binding_site, affinity=None)`**
  Updates an existing binding site's affinity.

- **`remove_binding(self, binding_site)`**
  Removes a binding site.

- **`update_interaction(self, other_protein, interaction_type=None, strength=None)`**
  Updates an existing interaction's type or strength.

---

### Property Calculation
- **`calculate_properties(self)`**
  Calculates and returns properties like length, molecular weight, isoelectric point, aromaticity, instability index, and GRAVY.

- **`activeness(self)`**
  Determines the activeness score based on interactions and bindings.

---

### Simulation and Visualization
- **`simulate_interactions(self)`**
  Simulates and visualizes interactions using a graph.

- **`interact_with_cell(self, cell)`**
  Simulates interaction between the protein and a cell.

- **`describe_interactions(self)`**
  Prints details of the protein's interactions.

- **`describe_bindings(self)`**
  Prints details of the protein's binding sites.

---

### Structure Prediction and Visualization
- **`predict_structure(self)`**
  Predicts the protein's 3D structure using PyRosetta.

- **`display_3d_structure(self)`**
  Displays the protein's 3D structure in a web browser using py3Dmol.

- **`pose_to_pdb_string(self, pose)`**
  Converts a PyRosetta Pose object to a PDB string.

---

### Serialization and Deserialization
- **`save_protein(self, file_path)`**
  Saves the protein to a file using pickle.

- **`load_protein(file_path)`**
  Loads a protein from a file using pickle.

- **`to_json(self)`**
  Converts the protein to a JSON string.

- **`from_json(cls, json_str)`**
  Creates a `Protein` instance from a JSON string.

- **`recreate_interactions(self, protein_dict)`**
  Recreates protein interactions after loading from JSON.

---

### Utility Methods
- **`search_motif(self, motif)`**
  Searches for a motif in the protein sequence using regular expressions.

- **`to_dict(self)`**
  Converts the protein to a dictionary.

- **`from_dict(cls, data)`**
  Creates a `Protein` instance from a dictionary.

- **`__getattr__(self, item)`**
  Allows access to attributes via dot notation.

- **`__eq__(self, other)`**
  Compares two proteins based on their sequences.

- **`__getstate__(self)`**
  Returns the state of the protein for pickling.

- **`__setstate__(self, state)`**
  Restores the state of the protein from a pickled state.

- **`__str__(self)`**
  Returns a string representation of the protein.

- **`get_id(self)`**
  Returns the protein's ID.

---

## Example Usage

```python
# Create a protein
protein = Protein(name="MyProtein", sequence="ACDEFGHIKLMNPQRSTVWY")

# Add a binding site
protein.add_binding(binding_site="10-20", affinity="high")

# Predict structure
protein.predict_structure()

# Display 3D structure
protein.display_3d_structure()

# Calculate properties
properties = protein.calculate_properties()
print(properties)

# Simulate interactions
protein.simulate_interactions()

# Save and load protein
protein.save_protein("my_protein.pkl")
loaded_protein = Protein.load_protein("my_protein.pkl")
```

---
