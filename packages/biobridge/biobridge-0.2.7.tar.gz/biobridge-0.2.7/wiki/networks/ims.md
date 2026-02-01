# Immune System Classes

---

## Overview
The `ImmuneSystem` and its associated cell classes (`ImmuneCell`, `Macrophage`, `TCell`, `BCell`) model the behavior of immune cells in response to infections. These classes support cell activation, deactivation, attack mechanisms, and visualization of immune responses.

---

## Class Definitions

### `ImmuneCell` (Abstract Base Class)
```python
class ImmuneCell(ABC):
    def __init__(self, name: str, strength: float, py_cell: Any):
        ...
```

### `Macrophage`
```python
class Macrophage(ImmuneCell):
    ...
```

### `TCell`
```python
class TCell(ImmuneCell):
    ...
```

### `BCell`
```python
class BCell(ImmuneCell):
    ...
```

### `ImmuneSystem`
```python
class ImmuneSystem:
    def __init__(self, cell_class: Any, cells: List[Tuple[str, float, str]]):
        ...
```

---

## Attributes

### `ImmuneCell`
| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the immune cell. |
| `strength` | `float` | Strength of the immune cell. |
| `py_cell` | `Any` | Associated biological cell object. |
| `activated` | `bool` | Activation status of the immune cell. |

### `Macrophage`, `TCell`, `BCell`
Inherit all attributes from `ImmuneCell`.

### `ImmuneSystem`
| Attribute | Type | Description |
|-----------|------|-------------|
| `cell_class` | `Any` | Class of the biological cell. |
| `immune_cells` | `List[Tuple[str, float, str]]` | List of immune cells with their properties. |
| `cells` | `List[ImmuneCell]` | List of `ImmuneCell` objects. |
| `fig`, `ax` | `matplotlib.figure.Figure`, `matplotlib.axes.Axes` | Figure and axes for visualization. |

---

## Methods

### `ImmuneCell` (Abstract)
- **`attack(self, infection: Any)`**
  Abstract method to define how the immune cell attacks an infection.

- **`getType(self) -> str`**
  Abstract method to return the type of the immune cell.

- **`activate(self)`**
  Activates the immune cell, increasing its strength.

- **`deactivate(self)`**
  Deactivates the immune cell, decreasing its strength.

- **`getName(self) -> str`**
  Returns the name of the immune cell.

- **`getStrength(self) -> float`**
  Returns the strength of the immune cell.

- **`getPyCell(self) -> Any`**
  Returns the associated biological cell object.

- **`isActivated(self) -> bool`**
  Returns the activation status of the immune cell.

---

### `Macrophage`
- **`attack(self, infection: Any)`**
  Engulfs the infection, reducing its spread rate.

- **`getType(self) -> str`**
  Returns "Macrophage".

- **`activate(self)`**
  Activates the macrophage, releasing cytokines and adding MHC-II surface protein.

- **`deactivate(self)`**
  Deactivates the macrophage, stopping cytokine release and removing MHC-II surface protein.

---

### `TCell`
- **`attack(self, infection: Any)`**
  Attacks infected cells, reducing the number of infected cells.

- **`getType(self) -> str`**
  Returns "T Cell".

- **`activate(self)`**
  Activates the T cell, producing cytokines and adding CD28 surface protein.

- **`deactivate(self)`**
  Deactivates the T cell, stopping cytokine production and removing CD28 surface protein.

---

### `BCell`
- **`attack(self, infection: Any)`**
  Produces antibodies, reducing the infection's spread rate.

- **`getType(self) -> str`**
  Returns "B Cell".

- **`activate(self)`**
  Activates the B cell, differentiating into plasma cells and adding CD19 surface protein.

- **`deactivate(self)`**
  Deactivates the B cell, stopping differentiation into plasma cells and removing CD19 surface protein.

---

### `ImmuneSystem`
- **`createImmuneCells(self)`**
  Creates immune cells based on the provided list.

- **`respond(self, infection: Any, cells: List[Any])`**
  Simulates the immune system's response to an infection.

- **`updateImmuneCell(self, cell: ImmuneCell)`**
  Updates the state of an immune cell, including metabolism and structural integrity.

- **`visualize(self, infection: Any, cells: List[Any])`**
  Visualizes the immune system's response to an infection.

- **`getCells(self) -> List[Any]`**
  Returns the list of biological cells associated with immune cells.

---

## Example Usage

```python
# Define a simple cell class for demonstration
class SimpleCell:
    def __init__(self, name, cell_type, surface_proteins, health=100):
        self.name = name
        self.cell_type = cell_type
        self.surface_proteins = surface_proteins
        self.health = health
        self.activated = False

    def add_surface_protein(self, protein):
        self.surface_proteins.append(protein)

    def remove_surface_protein(self, protein):
        if protein in self.surface_proteins:
            self.surface_proteins.remove(protein)

    def metabolize(self):
        self.health -= 1

    def update_structural_integrity(self):
        pass

    def getName(self):
        return self.name

    def getATPProduction(self):
        return 10

# Define a simple infection class for demonstration
class SimpleInfection:
    def __init__(self, spread_rate=0.5):
        self.spread_rate = spread_rate
        self.infected_cells = []

    def infect(self, cell):
        if cell.health > 50:
            self.infected_cells.append(cell)
            return True
        return False

# Create immune cells
immune_cells = [
    ("Macrophage1", 1.0, "Macrophage"),
    ("TCell1", 1.0, "TCell"),
    ("BCell1", 1.0, "BCell")
]

# Create immune system
immune_system = ImmuneSystem(SimpleCell, immune_cells)

# Create infection and cells
infection = SimpleInfection(spread_rate=0.5)
cells = [SimpleCell(f"Cell{i}", "Generic", []) for i in range(5)]

# Simulate immune response
immune_system.respond(infection, cells)

# Visualize the immune response
immune_system.visualize(infection, cells)
```

---

## Notes
- The `ImmuneCell` class is an abstract base class that defines the common interface for all immune cells.
- The `Macrophage`, `TCell`, and `BCell` classes implement specific behaviors for each type of immune cell.
- The `ImmuneSystem` class manages a collection of immune cells and simulates their response to infections.
- The `visualize` method uses Matplotlib to create a visual representation of the immune response.
