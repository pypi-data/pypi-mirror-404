# VisualizerWrapper Class

---

## Overview
The `VisualizerWrapper` class provides a wrapper for visualizing an `Environment` object using a visualizer. It manages the lifecycle of the visualizer, updates cell positions, and handles cell movement within the environment.

---

## Class Definition

```python
class VisualizerWrapper:
    def __init__(self, environment: Environment):
        """
        Initialize a new VisualizerWrapper object.
        :param environment: Environment object to visualize
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `environment` | `Environment` | The environment object to visualize. |
| `vis` | `visualizer.Visualizer` | The visualizer instance for rendering the environment. |
| `running` | `bool` | Flag indicating whether the visualizer is running. |

---

## Methods

### Initialization
- **`__init__(self, environment: Environment)`**
  Initializes a new `VisualizerWrapper` instance with the specified environment. It sets up the visualizer with dimensions based on the environment's width and height.

---

### Visualizer Control
- **`start(self)`**
  Starts the visualizer and begins the visualization loop.

- **`stop(self)`**
  Stops the visualizer and returns the current cell positions.

- **`run_visualizer(self)`**
  Runs the visualizer loop, updating cell positions and rendering the environment.

  - **Details**:
    - Continuously updates the visualizer with the latest cell positions from the environment.
    - Runs until `self.running` is set to `False`.
    - Updates every 100 milliseconds.

---

### Cell Movement
- **`move_cell(self, cell_id: int, new_x: int, new_y: int)`**
  Moves a cell within the environment to a new position.

  - **Parameters**:
    - `cell_id`: The ID of the cell to move.
    - `new_x`: The new x-coordinate for the cell.
    - `new_y`: The new y-coordinate for the cell.

---

## Example Usage

```python
# Create an environment
environment = Environment(
    name="Forest",
    width=50,
    height=50,
    temperature=25.0,
    humidity=50.0,
    env_type="normal"
)

# Add some cells to the environment
cell1 = Cell(name="Cell1", cell_type="epithelial")
cell2 = Cell(name="Cell2", cell_type="neuron")
environment.add_cell(cell1, (10, 10))
environment.add_cell(cell2, (20, 20))

# Create a VisualizerWrapper
visualizer_wrapper = VisualizerWrapper(environment)

# Start the visualizer
visualizer_wrapper.start()

# Let the visualizer run for a while (e.g., 5 seconds)
time.sleep(5)

# Stop the visualizer and get cell positions
cell_positions = visualizer_wrapper.stop()
print("Cell positions after visualization:", cell_positions)
```

---

## Expected Output
```
Cell positions after visualization: [
    {'x': 10, 'y': 10, 'health': 100, 'type': 'Cell', 'id': <cell_id_1>},
    {'x': 20, 'y': 20, 'health': 100, 'type': 'Cell', 'id': <cell_id_2>}
]
```

---

## Dependencies
- **`time`**: For managing the timing of visualizer updates.
- **`biobridge.enviromental.visualizer`**: Module providing the `Visualizer` class for rendering the environment.
- **`Environment`**: Class representing the biological environment to visualize.

---

## Error Handling
- The `run_visualizer` method checks the return value of `vis.run_once()` to determine if the visualizer should continue running.
- The `move_cell` method delegates cell movement to the environment, which handles boundary checks and position validation.

---

## Notes
- The `VisualizerWrapper` class is designed to work with the `Environment` class and a visualizer module.
- The visualizer updates at a fixed interval (100ms) to provide a smooth visualization experience.
- The `move_cell` method is set as a callback for the visualizer to handle cell movement events.
