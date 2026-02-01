# Environment Class

---

## Overview
The `Environment` class simulates a biological environment containing cells, tissues, organisms, and advanced organisms. It supports adding, removing, and simulating interactions between these entities, as well as applying environmental factors and substances. The class also provides methods for serialization, deserialization, and visualization of the environment's state.

---

## Class Definition

```python
class Environment:
    def __init__(self, name: str, width: int, height: int, temperature: float, humidity: float,
                 env_type: str = "normal",
                 cells: Optional[List[Cell]] = None,
                 tissues: Optional[List[Tissue]] = None,
                 organisms: Optional[List[Organism]] = None,
                 advanced_organisms: Optional[List[AdvancedOrganism]] = None,
                 environmental_factors: Optional[Dict[str, float]] = None,
                 substances: Optional[Dict[str, Substance]] = None):
        """
        Initialize a new Environment object.
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the environment. |
| `width` | `int` | Width of the environment. |
| `height` | `int` | Height of the environment. |
| `temperature` | `float` | Temperature of the environment in Celsius. |
| `humidity` | `float` | Humidity of the environment in percentage. |
| `env_type` | `str` | Type of environment ("normal" or "water"). |
| `cells` | `Dict[Tuple[int, int], Cell]` | Dictionary of cells with their coordinates. |
| `tissues` | `Dict[Tuple[int, int], Tissue]` | Dictionary of tissues with their coordinates. |
| `organisms` | `Dict[Tuple[int, int], Organism]` | Dictionary of organisms with their coordinates. |
| `advanced_organisms` | `Dict[Tuple[int, int], AdvancedOrganism]` | Dictionary of advanced organisms with their coordinates. |
| `environmental_factors` | `Dict[str, float]` | Dictionary of environmental factors and their intensities. |
| `substances` | `Dict[str, Substance]` | Dictionary of substances and their effects. |
| `base_cancer_risk` | `float` | Base cancer risk in the environment. |
| `comfortability_factor` | `float` | Comfortability factor of the environment. |
| `movement_hooks` | `List[Callable[[Tuple[int, int], Cell], Tuple[int, int]]]` | List of movement hooks for modifying cell positions. |

---

## Methods

### Initialization
- **`__init__(self, name: str, width: int, height: int, temperature: float, humidity: float, env_type: str = "normal", cells: Optional[List[Cell]] = None, tissues: Optional[List[Tissue]] = None, organisms: Optional[List[Organism]] = None, advanced_organisms: Optional[List[AdvancedOrganism]] = None, environmental_factors: Optional[Dict[str, float]] = None, substances: Optional[Dict[str, Substance]] = None)`**
  Initializes a new `Environment` instance with the specified parameters.

---

### Position Management
- **`_get_random_position(self) -> Tuple[int, int]`**
  Generates a random position within the environment's boundaries.

- **`add_cell(self, cell: Cell, position: Tuple[int, int])`**
  Adds a cell to the environment at the specified position.

- **`remove_cell(self, position: Tuple[int, int])`**
  Removes a cell from the environment at the specified position.

- **`add_tissue(self, tissue: Tissue, position: Tuple[int, int])`**
  Adds a tissue to the environment at the specified position.

- **`remove_tissue(self, position: Tuple[int, int])`**
  Removes a tissue from the environment at the specified position.

- **`add_organism(self, organism: Organism, position: Tuple[int, int])`**
  Adds an organism to the environment at the specified position.

- **`remove_organism(self, position: Tuple[int, int])`**
  Removes an organism from the environment at the specified position.

- **`add_advanced_organism(self, advanced_organism: AdvancedOrganism, position: Tuple[int, int])`**
  Adds an advanced organism to the environment at the specified position.

- **`remove_advanced_organism(self, position: Tuple[int, int])`**
  Removes an advanced organism from the environment at the specified position.

---

### Simulation and Calculation
- **`calculate_cancer_risk(self) -> float`**
  Calculates the current cancer risk based on environmental factors.

- **`calculate_comfortability(self) -> float`**
  Calculates the current comfortability factor based on environmental conditions.

- **`simulate_time_step(self)`**
  Simulates one time step in the environment, including cell division, organism reproduction, and environmental effects.

- **`apply_environmental_factors(self)`**
  Applies environmental factors to all cells, tissues, organisms, and advanced organisms.

- **`remove_dead_cells(self)`**
  Removes cells with zero health from the environment.

- **`remove_dead_organisms(self)`**
  Removes organisms with zero health from the environment.

---

### Movement and Interaction
- **`get_neighbors(self, position: Tuple[int, int], radius: int = 1) -> List[Tuple[Tuple[int, int], Cell]]`**
  Gets neighboring cells within a specified radius.

- **`add_movement_hook(self, hook: Callable[[Tuple[int, int], Cell], Tuple[int, int]])`**
  Adds a movement hook function to modify cell positions.

- **`apply_movement_hooks(self)`**
  Applies all movement hooks to modify cell positions.

---

### Description and Serialization
- **`describe(self) -> str`**
  Provides a detailed description of the environment.

- **`to_json(self) -> str`**
  Converts the environment to a JSON string.

- **`from_json(cls, json_str: str) -> 'Environment'`**
  Creates an `Environment` instance from a JSON string.

---

### Position Retrieval
- **`get_cell_positions(self) -> List[Dict[str, Any]]`**
  Retrieves the positions and details of all cells.

- **`get_tissue_positions(self) -> List[Dict[str, Any]]`**
  Retrieves the positions and details of all tissues.

- **`get_organism_positions(self) -> List[Dict[str, Any]]`**
  Retrieves the positions and details of all organisms.

- **`get_advanced_organism_positions(self) -> List[Dict[str, Any]]`**
  Retrieves the positions and details of all advanced organisms.

---

### Movement Methods
- **`move_cell(self, cell_id: int, new_x: int, new_y: int)`**
  Moves a cell to a new position.

- **`move_tissue(self, tissue_id: int, new_x: int, new_y: int)`**
  Moves a tissue to a new position.

- **`move_organism(self, org_id: int, new_x: int, new_y: int)`**
  Moves an organism to a new position.

- **`move_advanced_organism(self, org_id: int, new_x: int, new_y: int)`**
  Moves an advanced organism to a new position.

---

## Example Usage

```python
# Create an environment
environment = Environment(
    name="Forest",
    width=100,
    height=100,
    temperature=25.0,
    humidity=50.0,
    env_type="normal",
    environmental_factors={"nutrient": 0.5},
    substances={"DrugA": Substance("DrugA", {"health": 10.0})}
)

# Add a cell
cell = Cell(name="Cell1", cell_type="epithelial")
environment.add_cell(cell, (10, 10))

# Add a tissue
tissue = Tissue(name="Tissue1", tissue_type="epithelial")
environment.add_tissue(tissue, (20, 20))

# Simulate a time step
environment.simulate_time_step()

# Get environment description
print(environment.describe())

# Convert environment to JSON
environment_json = environment.to_json()
print(environment_json)

# Create environment from JSON
new_environment = Environment.from_json(environment_json)
```

---

## Notes
- The `Environment` class is designed to simulate complex biological environments with multiple entities.
- The `simulate_time_step` method simulates the passage of time, updating the state of all entities in the environment.
- The `calculate_cancer_risk` and `calculate_comfortability` methods adjust the environment's conditions based on various factors.
- Serialization and deserialization methods (`to_json`, `from_json`) allow for easy storage and retrieval of environment data.
