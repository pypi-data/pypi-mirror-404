# System Class

---

## Overview
The `System` class models a biological system composed of tissues, organs, and individual cells. It supports simulation of time steps, adaptation, stress response, mutation regulation, and visualization. The class also provides methods for serialization and deserialization.

---

## Class Definition

```python
class System:
    def __init__(self, name: str):
        """
        Initialize a new System object.
        :param name: Name of the system
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the system. |
| `tissues` | `List[Tissue]` | List of tissues in the system. |
| `organs` | `List[Organ]` | List of organs in the system. |
| `individual_cells` | `List[Cell]` | List of individual cells in the system. |
| `adaptation_rate` | `float` | Rate at which the system adapts to changes. |
| `stress_level` | `float` | Current stress level of the system. |
| `previous_cell_count` | `int` | Previous total cell count. |
| `previous_tissue_count` | `int` | Previous tissue count. |
| `state` | `np.ndarray` | 5-dimensional state vector of the system. |
| `health` | `float` | Health of the system (0.0 to 1.0). |
| `energy` | `float` | Energy level of the system (0.0 to 1.0). |
| `beneficial_mutation_chance` | `float` | Probability of a beneficial mutation. |

---

## Methods

### Initialization and Management
- **`__init__(self, name: str)`**
  Initializes a new `System` instance with the specified name.

- **`add_tissue(self, tissue: Tissue)`**
  Adds a tissue to the system.

- **`add_organ(self, organ: Organ)`**
  Adds an organ to the system.

- **`remove_tissue(self, tissue: Tissue)`**
  Removes a tissue from the system.

- **`add_cell(self, cell: Cell)`**
  Adds an individual cell to the system.

- **`remove_cell(self, cell: Cell)`**
  Removes an individual cell from the system.

---

### System Analysis
- **`get_tissue_count(self) -> int`**
  Returns the number of tissues in the system.

- **`get_total_cell_count(self) -> int`**
  Returns the total number of cells across all tissues and individual cells.

- **`get_average_system_health(self) -> float`**
  Calculates and returns the average health across all tissues and individual cells.

- **`calculate_growth_factor(self) -> float`**
  Calculates a growth factor based on system conditions.

- **`update_adaptation_rate(self)`**
  Updates the adaptation rate based on system changes.

---

### Simulation
- **`simulate_time_step(self, external_factors: Optional[List[tuple]] = None)`**
  Simulates one time step for the entire system, applying external factors if provided.

- **`apply_system_wide_stress(self, stress_amount: float)`**
  Applies stress to all tissues and individual cells in the system.

- **`simulate_system_adaptation(self)`**
  Simulates the system's adaptation to current conditions.

---

### Mutation Regulation
- **`regulate_mutations(self)`**
  Regulates mutations in the system, allowing only potentially beneficial mutations to persist.

---

### Status and Visualization
- **`get_system_status(self) -> str`**
  Provides a detailed status report of the system.

- **`visualize_network(self)`**
  Visualizes the system's network using NetworkX and Matplotlib.

---

### Serialization and Deserialization
- **`to_json(self) -> str`**
  Converts the system to a JSON string.

- **`from_json(cls, json_str: str) -> "System"`**
  Creates a `System` instance from a JSON string.

---

### Update and Status
- **`update(self, network_output: Dict[str, float])`**
  Updates the system based on neural network output.

- **`get_status(self) -> float`**
  Returns the current status of the system as a float.

---

### Utility Methods
- **`__str__(self) -> str`**
  Returns a string representation of the system.

- **`__getattr__(self, item)`**
  Allows access to attributes via dot notation.

- **`__eq__(self, other)`**
  Compares two systems based on their names.

---

## Example Usage

```python
# Create a system
system = System(name="Circulatory System")

# Add tissues and cells
tissue = Tissue(name="Heart Tissue", tissue_type="cardiac")
system.add_tissue(tissue)

cell = Cell(name="Heart Cell", cell_type="cardiac")
system.add_cell(cell)

# Simulate a time step
system.simulate_time_step(external_factors=[("nutrient", 0.5)])

# Apply system-wide stress
system.apply_system_wide_stress(stress_amount=0.2)

# Get system status
print(system.get_system_status())

# Visualize the system network
system.visualize_network()

# Serialize the system to JSON
system_json = system.to_json()
print(system_json)

# Deserialize the system from JSON
new_system = System.from_json(system_json)
print(new_system)
```

---

## Notes
- The `System` class is designed to model complex biological systems, integrating tissues, organs, and individual cells.
- The `simulate_time_step` method simulates the passage of time, updating the state of all components in the system.
- The `regulate_mutations` method simulates the biological process of mutation and selection, allowing only beneficial mutations to persist.
- Serialization and deserialization methods (`to_json`, `from_json`) allow for easy storage and retrieval of system data.
- The `visualize_network` method uses NetworkX and Matplotlib to create a visual representation of the system's network.
