# GeneRegulatoryNetwork Class

---

## Overview
The `GeneRegulatoryNetwork` class models a gene regulatory network, integrating receptors, proteins, DNA, and their interactions. It supports input processing, network simulation, gene regulation, visualization, and serialization/deserialization.

---

## Class Definition

```python
class GeneRegulatoryNetwork:
    def __init__(self, receptors: List[Protein], proteins: List[Protein], dna: DNA, interactions: Dict[str, List[str]], binding_sites):
        """
        Initialize the Gene Regulatory Network.
        :param receptors: List of receptor proteins that receive inputs
        :param proteins: List of proteins involved in the network
        :param dna: DNA object representing the cell's DNA
        :param interactions: Dictionary defining interactions between proteins
        :param binding_sites: Dictionary defining binding sites for each protein
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `receptors` | `Dict[str, Protein]` | Dictionary of receptor proteins. |
| `proteins` | `Dict[str, Protein]` | Dictionary of proteins involved in the network. |
| `dna` | `DNA` | DNA object representing the cell's DNA. |
| `interactions` | `Dict[str, List[str]]` | Dictionary defining interactions between proteins. |
| `binding_sites` | `Dict[str, str]` | Dictionary defining binding sites for each protein. |
| `active_proteins` | `Set[str]` | Set of currently active proteins. |
| `regulated_genes` | `List[str]` | List of genes regulated by the network. |

---

## Methods

### Initialization
- **`__init__(self, receptors: List[Protein], proteins: List[Protein], dna: DNA, interactions: Dict[str, List[str]], binding_sites)`**
  Initializes a new `GeneRegulatoryNetwork` instance with the specified receptors, proteins, DNA, interactions, and binding sites.

---

### Input Processing and Network Simulation
- **`process_inputs(self, inputs: List[str])`**
  Processes input signals and activates corresponding receptors.

- **`simulate_network(self, steps: int = 10)`**
  Simulates the network for a specified number of steps, propagating activations.

---

### Gene Regulation
- **`regulate_genes(self)`**
  Simulates the regulation of genes based on active proteins and their binding sites.

---

### Visualization
- **`visualize_network(self, regulated_genes)`**
  Visualizes the gene regulatory network, highlighting regulated genes and DNA.

---

### Prediction and Network Management
- **`predict_output(self, inputs)`**
  Predicts the output of the gene regulatory network based on given inputs.

- **`reset_network(self)`**
  Resets the network to its initial state.

- **`get_network_stats(self)`**
  Retrieves statistics about the network.

---

### Data Import and Export
- **`load_interactions_from_json(self, file_path: str)`**
  Loads interactions from a JSON file.

- **`load_interactions_from_csv(self, file_path: str)`**
  Loads interactions from a CSV file.

- **`save_network(self, file_path: str)`**
  Saves the current state of the gene regulatory network to a file.

- **`load_network(file_path: str)`**
  Loads a gene regulatory network from a file.

---

### Serialization and Deserialization
- **`to_json(self)`**
  Converts the network to a JSON string.

- **`from_json(json_str: str)`**
  Creates a `GeneRegulatoryNetwork` instance from a JSON string.

---

## Example Usage

```python
# Define receptors, proteins, DNA, interactions, and binding sites
receptors = [Protein(name="Receptor1", sequence="ACDEFGHIKLMNPQRSTVWY")]
proteins = [Protein(name="Protein1", sequence="ACDEFGHIKLMNPQRSTVWY")]
dna = DNA(sequence="ATGCGATCGATCGATCG")
interactions = {"Receptor1": ["Protein1"]}
binding_sites = {"Protein1": "ACGT"}

# Create a gene regulatory network
network = GeneRegulatoryNetwork(receptors, proteins, dna, interactions, binding_sites)

# Process inputs
network.process_inputs(["Receptor1"])

# Simulate the network
network.simulate_network(steps=5)

# Regulate genes
regulated_genes = network.regulate_genes()

# Visualize the network
network.visualize_network(regulated_genes)

# Predict output
predicted_genes = network.predict_output(["Receptor1"])

# Get network statistics
stats = network.get_network_stats()
print(stats)

# Save and load the network
network.save_network("gene_regulatory_network.pkl")
loaded_network = GeneRegulatoryNetwork.load_network("gene_regulatory_network.pkl")

# Convert the network to JSON
network_json = network.to_json()
print(network_json)

# Create a network from JSON
new_network = GeneRegulatoryNetwork.from_json(network_json)
```

---

## Notes
- The `GeneRegulatoryNetwork` class is designed to model the dynamic behavior of gene regulatory networks in biological systems.
- The `visualize_network` method uses NetworkX and Matplotlib to create a visual representation of the network, highlighting regulated genes and DNA.
- Serialization and deserialization methods (`to_json`, `from_json`, `save_network`, `load_network`) allow for easy storage and retrieval of network data.
- The `predict_output` method simulates the entire process from input processing to gene regulation and visualization.
