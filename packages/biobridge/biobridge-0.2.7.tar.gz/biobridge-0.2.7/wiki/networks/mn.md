# MetabolicNetwork Class

---

## Overview
The `MetabolicNetwork` class models a biological metabolic network, including metabolites, enzymes, and reactions. It supports adding/removing reactions, predicting metabolic outputs, finding pathways, and visualizing the network.

---

## Class Definition

```python
class MetabolicNetwork:
    def __init__(
        self,
        metabolites: List[str],
        enzymes: List[str],
        reactions: List[Tuple[str, str, str]],
    ):
        """
        Initialize a new MetabolicNetwork object.
        :param metabolites: List of metabolite names in the network
        :param enzymes: List of enzyme names in the network
        :param reactions: List of reactions, each as a tuple (enzyme, substrate, product)
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `metabolites` | `Set[str]` | Set of metabolite names in the network. |
| `enzymes` | `Set[str]` | Set of enzyme names in the network. |
| `reactions` | `List[Tuple[str, str, str]]` | List of reactions, each as a tuple (enzyme, substrate, product). |
| `graph` | `nx.DiGraph` | Directed graph representing the metabolic network. |
| `vertex_map` | `Dict[str, str]` | Mapping of vertex names to their identifiers. |

---

## Methods

### Initialization and Graph Construction
- **`__init__(self, metabolites: List[str], enzymes: List[str], reactions: List[Tuple[str, str, str]])`**
  Initializes a new `MetabolicNetwork` instance with the specified metabolites, enzymes, and reactions.

- **`build_graph(self)`**
  Constructs the directed graph representing the metabolic network.

---

### Vertex and Reaction Management
- **`add_vertex(self, name: str, node_type: str)`**
  Adds a vertex (metabolite or enzyme) to the graph.

- **`add_reaction(self, enzyme: str, substrate: str, product: str)`**
  Adds a reaction to the network.

- **`remove_reaction(self, enzyme: str, substrate: str, product: str)`**
  Removes a reaction from the network.

---

### Network Analysis
- **`get_connected_components(self) -> List[Set[str]]`**
  Retrieves the connected components of the network.

- **`get_metabolite_degrees(self) -> Dict[str, Dict[str, int]]`**
  Retrieves the in-degree and out-degree of each metabolite.

---

### Prediction and Pathway Analysis
- **`predict_outputs(self, input_metabolites: Set[str], steps: int) -> Set[str]`**
  Predicts the output metabolites after a specified number of steps.

- **`get_possible_pathways(self, start_metabolite: str, end_metabolite: str, max_steps: int) -> List[List[str]]`**
  Retrieves all possible pathways from a start metabolite to an end metabolite.

---

### Serialization and Deserialization
- **`to_json(self) -> str`**
  Converts the metabolic network to a JSON string.

- **`from_json(json_str: str) -> "MetabolicNetwork"`**
  Creates a `MetabolicNetwork` instance from a JSON string.

---

### Visualization
- **`visualize_network(self, save_path: Optional[str] = None)`**
  Visualizes the metabolic network using NetworkX and Matplotlib, with options to save the visualization.

---

### Network Management
- **`reset(self)`**
  Resets the metabolic network by clearing all metabolites, enzymes, reactions, and the graph.

---

## Example Usage

```python
# Define metabolites, enzymes, and reactions
metabolites = ["A", "B", "C", "D"]
enzymes = ["E1", "E2"]
reactions = [
    ("E1", "A", "B"),
    ("E2", "B", "C"),
    ("E2", "C", "D")
]

# Create a metabolic network
network = MetabolicNetwork(metabolites, enzymes, reactions)

# Add a new reaction
network.add_reaction("E3", "A", "D")

# Predict outputs
outputs = network.predict_outputs({"A"}, steps=3)
print(f"Predicted outputs: {outputs}")

# Find pathways
pathways = network.get_possible_pathways("A", "D", max_steps=3)
print(f"Possible pathways: {pathways}")

# Visualize the network
network.visualize_network(save_path="metabolic_network.png")

# Convert the network to JSON
network_json = network.to_json()
print(network_json)

# Create a network from JSON
new_network = MetabolicNetwork.from_json(network_json)

# Reset the network
network.reset()
```

---

## Notes
- The `MetabolicNetwork` class is designed to model the dynamic behavior of metabolic pathways in biological systems.
- The `visualize_network` method uses NetworkX and Matplotlib to create a visual representation of the network, with metabolites and enzymes distinguished by color and shape.
- Serialization and deserialization methods (`to_json`, `from_json`) allow for easy storage and retrieval of network data.
- The `predict_outputs` method simulates the propagation of metabolites through the network, updating the set of available metabolites at each step.
- The `get_possible_pathways` method uses depth-first search to find all possible pathways from a start metabolite to an end metabolite within a specified number of steps.
