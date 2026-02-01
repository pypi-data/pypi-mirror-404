# SignalingNetwork Class

## Overview
The `SignalingNetwork` class models a biological signaling network, including molecules and their interactions. It supports activation, signal propagation, visualization, and serialization/deserialization of the network.

---

## Class Definition

```python
class SignalingNetwork:
    def __init__(self, molecules: List[str], interactions: Dict[str, List[str]]):
        """
        Initialize a new SignalingNetwork object.
        :param molecules: List of molecule names in the network
        :param interactions: Dictionary mapping each molecule to its target molecules
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `molecules` | `Set[str]` | Set of molecule names in the network. |
| `interactions` | `Dict[str, List[str]]` | Dictionary mapping each molecule to its target molecules. |
| `active_molecules` | `Set[str]` | Set of currently active molecules. |

---

## Methods

### Initialization
- **`__init__(self, molecules: List[str], interactions: Dict[str, List[str]])`**
  Initializes a new `SignalingNetwork` instance with the specified molecules and interactions.

---

### Molecule Activation and Signal Propagation
- **`activate_molecules(self, molecule_list: List[str])`**
  Activates a list of molecules in the network.

- **`propagate_signals(self, steps: int = 10)`**
  Propagates signals through the network for a specified number of steps.

---

### Visualization
- **`visualize_network(self)`**
  Visualizes the signaling network using NetworkX and Matplotlib, highlighting active molecules.

---

### Serialization and Deserialization
- **`save_network(self, file_path: str)`**
  Saves the network to a JSON file.

- **`load_network(file_path: str)`**
  Loads a network from a JSON file.

- **`to_json(self)`**
  Converts the network to a JSON string.

- **`from_json(json_str: str)`**
  Creates a `SignalingNetwork` instance from a JSON string.

---

### Network Management
- **`reset(self)`**
  Resets the network by clearing active molecules and interactions.

---

## Example Usage

```python
# Define molecules and interactions
molecules = ["A", "B", "C", "D"]
interactions = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D"]
}

# Create a signaling network
network = SignalingNetwork(molecules, interactions)

# Activate molecules
network.activate_molecules(["A"])

# Propagate signals
network.propagate_signals(steps=5)

# Visualize the network
network.visualize_network()

# Save the network to a file
network.save_network("signaling_network.json")

# Load the network from a file
loaded_network = SignalingNetwork.load_network("signaling_network.json")

# Convert the network to JSON
network_json = network.to_json()
print(network_json)

# Create a network from JSON
new_network = SignalingNetwork.from_json(network_json)

# Reset the network
network.reset()
```

---

## Notes
- The `SignalingNetwork` class is designed to model the dynamic behavior of signaling pathways in biological systems.
- The `visualize_network` method uses NetworkX and Matplotlib to create a visual representation of the network, with active molecules highlighted in red.
- Serialization and deserialization methods (`save_network`, `load_network`, `to_json`, `from_json`) allow for easy storage and retrieval of network data.
- The `propagate_signals` method simulates the propagation of signals through the network, updating the set of active molecules at each step.
