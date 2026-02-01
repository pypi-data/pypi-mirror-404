# Orchestrator Class

---

## Overview
The `Orchestrator` class is designed to manage and simulate the interactions between tissues, gene regulatory networks, metabolic networks, and signaling networks. It provides methods for simulating these components, visualizing their states, and saving/loading their configurations.

---

## Class Definition

```python
class Orchestrator:
    def __init__(self, tissues: Optional[List[Tissue]] = None,
                 gene_networks: Optional[List[GeneRegulatoryNetwork]] = None,
                 metabolic_networks: Optional[List[MetabolicNetwork]] = None,
                 signaling_networks: Optional[List[SignalingNetwork]] = None):
        """
        Initialize the Orchestrator with various tissues and networks.
        :param tissues: List of Tissue objects
        :param gene_networks: List of GeneRegulatoryNetwork objects
        :param metabolic_networks: List of MetabolicNetwork objects
        :param signaling_networks: List of SignalingNetwork objects
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `tissues` | `Optional[List[Tissue]]` | List of `Tissue` objects. |
| `gene_networks` | `Optional[List[GeneRegulatoryNetwork]]` | List of `GeneRegulatoryNetwork` objects. |
| `metabolic_networks` | `Optional[List[MetabolicNetwork]]` | List of `MetabolicNetwork` objects. |
| `signaling_networks` | `Optional[List[SignalingNetwork]]` | List of `SignalingNetwork` objects. |

---

## Methods

### Initialization
- **`__init__(self, tissues: Optional[List[Tissue]] = None, gene_networks: Optional[List[GeneRegulatoryNetwork]] = None, metabolic_networks: Optional[List[MetabolicNetwork]] = None, signaling_networks: Optional[List[SignalingNetwork]] = None)`**
  Initializes a new `Orchestrator` instance with optional lists of tissues, gene networks, metabolic networks, and signaling networks.

---

### Adding Components
- **`add_tissue(self, tissue: Tissue) -> None`**
  Adds a `Tissue` object to the orchestrator.

  - **Parameters**:
    - `tissue`: The `Tissue` object to add.

- **`add_gene_network(self, gene_network: GeneRegulatoryNetwork) -> None`**
  Adds a `GeneRegulatoryNetwork` object to the orchestrator.

  - **Parameters**:
    - `gene_network`: The `GeneRegulatoryNetwork` object to add.

- **`add_metabolic_network(self, metabolic_network: MetabolicNetwork) -> None`**
  Adds a `MetabolicNetwork` object to the orchestrator.

  - **Parameters**:
    - `metabolic_network`: The `MetabolicNetwork` object to add.

- **`add_signaling_network(self, signaling_network: SignalingNetwork) -> None`**
  Adds a `SignalingNetwork` object to the orchestrator.

  - **Parameters**:
    - `signaling_network`: The `SignalingNetwork` object to add.

---

### Simulation
- **`simulate_tissues(self, external_factors: List[tuple] = None) -> None`**
  Simulates one time step in all tissues' life, including growth, healing, and external factors.

  - **Parameters**:
    - `external_factors`: List of tuples (factor, intensity) to apply to all tissues.

- **`simulate_gene_networks(self, inputs: List[str]) -> None`**
  Simulates all gene regulatory networks with given inputs.

  - **Parameters**:
    - `inputs`: List of input signals for the gene networks.

- **`simulate_metabolic_networks(self, input_metabolites: Set[str], steps: int) -> None`**
  Simulates all metabolic networks with given input metabolites.

  - **Parameters**:
    - `input_metabolites`: Set of initial input metabolites.
    - `steps`: Number of reaction steps to simulate.

- **`simulate_signaling_networks(self, molecule_list: List[str], steps: int) -> None`**
  Simulates all signaling networks with given activated molecules.

  - **Parameters**:
    - `molecule_list`: List of molecule names to activate.
    - `steps`: Number of propagation steps.

- **`simulate_network_evolution(self, num_steps: int) -> None`**
  Simulates the evolution of all networks over a given number of time steps.

  - **Parameters**:
    - `num_steps`: Number of time steps to simulate.

---

### Visualization
- **`visualize_gene_networks(self) -> None`**
  Visualizes all gene regulatory networks.

- **`visualize_metabolic_networks(self) -> None`**
  Visualizes all metabolic networks.

- **`visualize_signaling_networks(self) -> None`**
  Visualizes all signaling networks.

---

### State Management
- **`save_state(self, file_path: str) -> None`**
  Saves the current state of the orchestrator to a file using `pickle`.

  - **Parameters**:
    - `file_path`: Path where the state should be saved.

- **`load_state(file_path: str) -> 'Orchestrator'`**
  Loads the orchestrator state from a file.

  - **Parameters**:
    - `file_path`: Path from where the state should be loaded.

  - **Returns**: An instance of `Orchestrator`.

- **`to_json(self) -> str`**
  Converts the orchestrator to a JSON string representation.

  - **Returns**: JSON string representing the orchestrator.

- **`from_json(json_str: str) -> 'Orchestrator'`**
  Creates an `Orchestrator` instance from a JSON string.

  - **Parameters**:
    - `json_str`: JSON string representing the orchestrator.

  - **Returns**: An instance of `Orchestrator`.

---

### Reset
- **`reset(self) -> None`**
  Resets all tissues and networks to their initial states.

---

## Example Usage

```python
# Initialize the Orchestrator
orchestrator = Orchestrator()

# Add a tissue
tissue = Tissue("Liver Tissue", "Liver")
orchestrator.add_tissue(tissue)

# Add a gene regulatory network
gene_network = GeneRegulatoryNetwork()
orchestrator.add_gene_network(gene_network)

# Add a metabolic network
metabolic_network = MetabolicNetwork()
orchestrator.add_metabolic_network(metabolic_network)

# Add a signaling network
signaling_network = SignalingNetwork()
orchestrator.add_signaling_network(signaling_network)

# Simulate tissues with external factors
orchestrator.simulate_tissues([("radiation", 0.5), ("nutrient", 0.8)])

# Simulate gene networks with inputs
orchestrator.simulate_gene_networks(["signal_1", "signal_2"])

# Simulate metabolic networks with input metabolites
orchestrator.simulate_metabolic_networks({"glucose", "oxygen"}, 10)

# Simulate signaling networks with activated molecules
orchestrator.simulate_signaling_networks(["molecule_1", "molecule_2"], 5)

# Visualize networks
orchestrator.visualize_gene_networks()
orchestrator.visualize_metabolic_networks()
orchestrator.visualize_signaling_networks()

# Save the orchestrator state
orchestrator.save_state("orchestrator_state.pkl")

# Load the orchestrator state
loaded_orchestrator = Orchestrator.load_state("orchestrator_state.pkl")

# Convert the orchestrator to JSON
orchestrator_json = orchestrator.to_json()
print(orchestrator_json)

# Create an orchestrator from JSON
new_orchestrator = Orchestrator.from_json(orchestrator_json)

# Simulate network evolution
orchestrator.simulate_network_evolution(10)

# Reset the orchestrator
orchestrator.reset()
```

---

## Dependencies
- **`pickle`**: For saving and loading the orchestrator state.
- **`json`**: For JSON serialization and deserialization.
- **`biobridge.blocks.tissue.Tissue`**: For tissue objects.
- **`metabolic_network.MetabolicNetwork`**: For metabolic network objects.
- **`biobridge.networks.grn.GeneRegulatoryNetwork`**: For gene regulatory network objects.
- **`signaling_network.SignalingNetwork`**: For signaling network objects.

---

## Error Handling
- The class does not explicitly handle errors, but it relies on the underlying methods of the network and tissue classes to handle their own errors.

---

## Notes
- The `Orchestrator` class is designed to manage and simulate complex biological systems.
- It supports adding and simulating tissues, gene networks, metabolic networks, and signaling networks.
- The class provides methods for visualizing the networks and saving/loading their states.
- The `simulate_network_evolution` method allows for simulating the evolution of all networks over multiple time steps.
