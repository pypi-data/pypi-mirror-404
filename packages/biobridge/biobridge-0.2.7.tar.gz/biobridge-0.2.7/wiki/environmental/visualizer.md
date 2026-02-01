# Visualizer Class

---

## Overview
The `Visualizer` class provides a graphical interface for visualizing cells within a simulated environment using Pygame. It supports rendering cells, handling user interactions, and updating cell positions dynamically.

---

## Class Definition

```python
class Visualizer:
    def __init__(self, width: int, height: int):
        """
        Initialize a new Visualizer object.
        :param width: Width of the visualization window
        :param height: Height of the visualization window
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `window_width` | `int` | Width of the visualization window. |
| `window_height` | `int` | Height of the visualization window. |
| `window` | `pygame.Surface` | Pygame window surface for rendering. |
| `font` | `pygame.font.Font` | Font used for rendering text. |
| `cells` | `Dict[int, Tuple[pygame.Rect, str]]` | Dictionary of cells with their graphical representation and type. |
| `cellPositions` | `Dict[int, Tuple[int, int]]` | Dictionary of cell positions. |
| `selectedCellId` | `Optional[int]` | ID of the currently selected cell. |
| `m_moveCell` | `Optional[Callable[[int, int, int], None]]` | Callback function for handling cell movements. |

---

## Methods

### Initialization
- **`__init__(self, width: int, height: int)`**
  Initializes a new `Visualizer` instance with the specified window dimensions. It sets up the Pygame window and initializes data structures for storing cell information.

---

### Updating and Rendering
- **`update(self, cell_data: List[CellData])`**
  Updates the visual representation of cells based on the provided cell data.

  - **Parameters**:
    - `cell_data`: List of dictionaries containing cell information (e.g., position, health, type, ID).

- **`run_once(self) -> bool`**
  Renders cells and handles Pygame events.

  - **Returns**: `True` if the visualizer should continue running, `False` if it should quit.

  - **Details**:
    - Handles Pygame events such as quitting the window and mouse interactions.
    - Renders cells and updates the display.

---

### Cell Selection and Movement
- **`selectCell(self, x: int, y: int)`**
  Selects a cell at the specified position if one exists.

  - **Parameters**:
    - `x`: X-coordinate of the cell position.
    - `y`: Y-coordinate of the cell position.

- **`moveSelectedCell(self, x: int, y: int)`**
  Moves the selected cell to a new position.

  - **Parameters**:
    - `x`: New X-coordinate for the cell.
    - `y`: New Y-coordinate for the cell.

  - **Details**:
    - Calls the `m_moveCell` callback function if it is set.
    - Updates the visual position of the cell for immediate feedback.

---

### Callback and Position Retrieval
- **`setMoveCell(self, func: Callable[[int, int, int], None])`**
  Sets the callback function to handle cell movements.

  - **Parameters**:
    - `func`: Callback function that takes cell ID, new X, and new Y coordinates.

- **`getCellPositions(self) -> Dict[int, Tuple[int, int]]`**
  Retrieves the current positions of all cells.

  - **Returns**: A dictionary mapping cell IDs to their positions.

---

## Example Usage

```python
# Initialize the visualizer
visualizer = Visualizer(width=800, height=600)

# Define a callback function for moving cells
def move_cell_callback(cell_id, new_x, new_y):
    print(f"Moving cell {cell_id} to position ({new_x}, {new_y})")

# Set the callback function
visualizer.setMoveCell(move_cell_callback)

# Sample cell data
cell_data = [
    {"x": 10, "y": 10, "health": 100, "type": "Epithelial", "id": 1},
    {"x": 20, "y": 20, "health": 80, "type": "Neuron", "id": 2}
]

# Update the visualizer with cell data
visualizer.update(cell_data)

# Run the visualizer
running = True
while running:
    running = visualizer.run_once()

# Get current cell positions
cell_positions = visualizer.getCellPositions()
print("Current cell positions:", cell_positions)
```

---

## Expected Output
```
Moving cell 1 to position (15, 15)
Current cell positions: {1: (15, 15), 2: (20, 20)}
```

---

## Dependencies
- **`pygame`**: Library for creating the graphical interface and handling events.

---

## Error Handling
- The `run_once` method handles the `pygame.QUIT` event to close the window gracefully.
- The `selectCell` and `moveSelectedCell` methods include checks to ensure valid cell selection and movement.

---

## Notes
- The `Visualizer` class is designed to work with Pygame for rendering and event handling.
- The `update` method clears existing cell data and updates it based on the provided `cell_data`.
- The `run_once` method continuously renders the cells and handles user interactions until the window is closed.
- The `setMoveCell` method allows setting a custom callback function to handle cell movements, enabling integration with other parts of the application.
