# EmbryoSimulation Class

---

## Overview
The `EmbryoSimulation` class simulates the developmental stages of an embryo, from a single zygote to a fetus. It models cell division, tissue formation, organogenesis, and system development. The class uses Pygame for visualization and provides methods to simulate each developmental stage.

---

## Class Definition

```python
class EmbryoSimulation:
    def __init__(self, initialCells: int = 1):
        """
        Initialize a new EmbryoSimulation object.
        :param initialCells: Number of initial cells (default: 1)
        """
        ...
```

---

## Enums

### DevelopmentalStage
```python
class DevelopmentalStage(Enum):
    Zygote = 0
    Cleavage = 1
    Blastula = 2
    Gastrula = 3
    Organogenesis = 4
    Fetus = 5
```
- Represents the different stages of embryonic development.

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `cells` | `List[Cell]` | List of cells in the simulation. |
| `tissues` | `List[Tissue]` | List of tissues in the simulation. |
| `organs` | `List[Organ]` | List of organs in the simulation. |
| `systems` | `List[System]` | List of systems in the simulation. |
| `stage` | `DevelopmentalStage` | Current developmental stage. |
| `daysPassed` | `int` | Number of days passed in the simulation. |
| `rng` | `random.Random` | Random number generator for stochastic events. |
| `window` | `pygame.Surface` | Pygame window for visualization. |
| `font` | `pygame.font.Font` | Font for rendering text in the visualization. |

---

## Methods

### Initialization
- **`__init__(self, initialCells: int = 1)`**
  Initializes a new `EmbryoSimulation` instance with the specified number of initial cells.

- **`initialize_pygame(self)`**
  Initializes the Pygame window and font for visualization.

- **`initialize_simulation(self, initialCells: int)`**
  Initializes the simulation with the specified number of initial cells.

---

### Simulation Control
- **`step(self)`**
  Advances the simulation by one day, updating the developmental stage and simulating biological processes.

- **`run(self, steps: int)`**
  Runs the simulation for the specified number of steps.

  - **Parameters**:
    - `steps`: Number of steps to run the simulation.

---

### Developmental Processes
- **`divideCells(self)`**
  Simulates cell division during the cleavage stage.

- **`formBlastula(self)`**
  Simulates the formation of the blastula stage, including the differentiation of trophoblast and inner cell mass.

- **`initiateGastrulation(self)`**
  Simulates gastrulation, including the formation of germ layers.

- **`differentiateGermLayers(self)`**
  Differentiates cells in the germ layers into specialized cell types.

- **`initiateOrganogenesis(self)`**
  Simulates organogenesis, including the formation of organs from tissues.

- **`developFetus(self)`**
  Simulates fetal development, including organ growth.

- **`developSystems(self)`**
  Simulates the development of organ systems.

---

### Visualization
- **`visualize(self)`**
  Visualizes the current state of the simulation using Pygame.

  - **Details**:
    - Displays cells, tissues, organs, and systems.
    - Shows the current developmental stage and day count.
    - Uses different colors to represent different cell types.

- **`get_cell_color(self, cell_type: str) -> Tuple[int, int, int]`**
  Returns the color associated with a specific cell type.

  - **Parameters**:
    - `cell_type`: Type of the cell.

  - **Returns**: RGB color tuple.

---

### Accessor Methods
- **`getCells(self) -> List[Cell]`**
  Returns the list of cells in the simulation.

- **`getTissues(self) -> List[Tissue]`**
  Returns the list of tissues in the simulation.

- **`getOrgans(self) -> List[Organ]`**
  Returns the list of organs in the simulation.

- **`getSystems(self) -> List[System]`**
  Returns the list of systems in the simulation.

- **`getStage(self) -> DevelopmentalStage`**
  Returns the current developmental stage.

---

## Example Usage

```python
# Initialize the embryo simulation
simulation = EmbryoSimulation(initialCells=1)

# Run the simulation for 60 days
simulation.run(steps=60)
```

---

## Dependencies
- **`pygame`**: For visualization and user interaction.
- **`random`**: For simulating stochastic biological processes.
- **`math`**: For mathematical operations.
- **`Cell`**: Class representing cells.
- **`Tissue`**: Class representing tissues.
- **`Organ`**: Class representing organs.
- **`System`**: Class representing organ systems.

---

## Error Handling
- The class does not explicitly handle errors, but it includes checks to ensure valid operations during simulation steps.

---

## Notes
- The `EmbryoSimulation` class is designed to simulate the key stages of embryonic development.
- The simulation progresses through defined stages: Zygote, Cleavage, Blastula, Gastrula, Organogenesis, and Fetus.
- The `visualize` method provides a graphical representation of the simulation state, including cells, tissues, organs, and systems.
- The class uses Pygame for visualization, allowing users to observe the developmental process.
