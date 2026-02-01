# FlowCytometer Class
---
## Overview
The `FlowCytometer` class provides tools for analyzing and managing collections of cells. It supports adding cells, analyzing their properties, profiling based on cell type, sorting cells by various criteria, and providing descriptions of the cells.

---
## Class Definition
```python
from typing import List, Dict
from biobridge.blocks.cell import Cell

class FlowCytometer:
    def __init__(self):
        """
        Initialize a new FlowCytometer object.
        """
        self.cells = []
```
---
## Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| `cells`   | `List[Cell]` | A list to store and manage cell objects. |

---
## Methods
### Initialization
- **`__init__(self)`**
  Initializes a new `FlowCytometer` instance with an empty list of cells.

---
### Adding a Cell
- **`add_cell(self, cell: 'Cell') -> None`**
  Adds a cell to the flow cytometer.
  - **Parameters**:
    - `cell`: The cell to add.

---
### Analyzing Cells
- **`analyze_cells(self) -> List[Dict[str, any]]`**
  Analyzes the cells in the flow cytometer.
  - **Returns**: A list of dictionaries, each containing analysis data for each cell.

---
### Profiling Cells
- **`profile_cells(self) -> Dict[str, List[Dict[str, any]]]`**
  Profiles the cells in the flow cytometer based on cell type.
  - **Returns**: A dictionary with cell types as keys and lists of cell profiles as values.

---
### Sorting Cells
- **`sort_cells(self, criteria: str, ascending: bool = True) -> List['Cell']`**
  Sorts the cells in the flow cytometer based on a specific criterion.
  - **Parameters**:
    - `criteria`: The criterion to sort by (e.g., 'health', 'age', 'metabolism_rate').
    - `ascending`: Whether to sort in ascending order (default is True).
  - **Returns**: A list of cells sorted by the specified criterion.
  - **Raises**: `ValueError` if an invalid sorting criterion is provided.

---
### Describing Cells
- **`describe(self) -> str`**
  Provides a detailed description of the flow cytometer and its cells.
  - **Returns**: A string containing descriptions of all cells in the flow cytometer.

---
### String Representation
- **`__str__(self) -> str`**
  Returns a string representation of the flow cytometer.
  - **Returns**: A string representation of the flow cytometer.

---
## Example Usage
```python
# Initialize a FlowCytometer
flow_cytometer = FlowCytometer()

# Add cells to the flow cytometer
flow_cytometer.add_cell(Cell(name="Cell1", cell_type="Type1", health=0.9))
flow_cytometer.add_cell(Cell(name="Cell2", cell_type="Type2", health=0.7))

# Analyze the cells
analysis_data = flow_cytometer.analyze_cells()
print(analysis_data)

# Profile the cells
profiles = flow_cytometer.profile_cells()
print(profiles)

# Sort the cells by health in ascending order
sorted_cells = flow_cytometer.sort_cells(criteria="health", ascending=True)
for cell in sorted_cells:
    print(cell.describe())

# Describe the flow cytometer
print(flow_cytometer.describe())
```
---
## Dependencies
- **`biobridge.blocks.cell.Cell`**: For creating and managing cell objects.

---
## Error Handling
- The class includes checks for valid sorting criteria in the `sort_cells` method and raises a `ValueError` if an invalid criterion is provided.

---
## Notes
- The `FlowCytometer` class is designed for managing and analyzing collections of cells.
- It supports detailed profiling and analysis of cell properties, making it useful for biological simulations and studies.
