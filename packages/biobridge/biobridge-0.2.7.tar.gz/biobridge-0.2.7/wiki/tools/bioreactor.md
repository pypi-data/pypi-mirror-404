# Bioreactor Class

---

## Overview
The `Bioreactor` class simulates a controlled environment for growing and maintaining biological tissues. It allows for adding and removing tissues, adjusting environmental conditions (temperature, pH, oxygen level), managing nutrient and waste levels, and simulating the passage of time to observe the effects on the contained tissues.

---

## Class Definition

```python
class Bioreactor:
    def __init__(self, name: str, capacity: int, temperature: float = 37.0, pH: float = 7.0, oxygen_level: float = 0.2):
        """
        Initialize a new Bioreactor object.
        :param name: Name of the bioreactor
        :param capacity: Maximum number of tissues the bioreactor can hold
        :param temperature: Temperature in degrees Celsius (default: 37.0)
        :param pH: pH level (default: 7.0)
        :param oxygen_level: Oxygen level (default: 0.2)
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the bioreactor. |
| `capacity` | `int` | Maximum number of tissues the bioreactor can hold. |
| `temperature` | `float` | Temperature in degrees Celsius. |
| `pH` | `float` | pH level. |
| `oxygen_level` | `float` | Oxygen level. |
| `tissues` | `List[Tissue]` | List of tissues in the bioreactor. |
| `nutrient_level` | `float` | Nutrient level (0.0 to 1.0). |
| `waste_level` | `float` | Waste level (0.0 to 1.0). |

---

## Methods

### Initialization
- **`__init__(self, name: str, capacity: int, temperature: float = 37.0, pH: float = 7.0, oxygen_level: float = 0.2)`**
  Initializes a new `Bioreactor` instance with the specified name, capacity, temperature, pH, and oxygen level.

---

### Tissue Management
- **`add_tissue(self, tissue: Tissue) -> None`**
  Adds a tissue to the bioreactor.

  - **Parameters**:
    - `tissue`: The tissue to add.

- **`remove_tissue(self, tissue: Tissue) -> None`**
  Removes a tissue from the bioreactor.

  - **Parameters**:
    - `tissue`: The tissue to remove.

---

### Environmental Adjustment
- **`adjust_temperature(self, new_temperature: float) -> None`**
  Adjusts the temperature of the bioreactor.

  - **Parameters**:
    - `new_temperature`: The new temperature in degrees Celsius.

- **`adjust_pH(self, new_pH: float) -> None`**
  Adjusts the pH of the bioreactor.

  - **Parameters**:
    - `new_pH`: The new pH level.

- **`adjust_oxygen_level(self, new_oxygen_level: float) -> None`**
  Adjusts the oxygen level of the bioreactor.

  - **Parameters**:
    - `new_oxygen_level`: The new oxygen level.

---

### Nutrient and Waste Management
- **`add_nutrients(self, amount: float) -> None`**
  Adds nutrients to the bioreactor.

  - **Parameters**:
    - `amount`: The amount of nutrients to add.

- **`remove_waste(self, amount: float) -> None`**
  Removes waste from the bioreactor.

  - **Parameters**:
    - `amount`: The amount of waste to remove.

---

### Simulation
- **`simulate_time_step(self) -> None`**
  Simulates one time step in the bioreactor's operation.

  - **Details**:
    - Applies bioreactor conditions to each tissue.
    - Updates nutrient and waste levels based on the number of tissues.

---

### Status Reporting
- **`get_status(self) -> str`**
  Gets the current status of the bioreactor.

  - **Returns**: A string containing the current status of the bioreactor.

- **`__str__(self) -> str`**
  Returns a string representation of the bioreactor.

  - **Returns**: A string containing the current status of the bioreactor.

---

## Example Usage

```python
# Create a bioreactor
bioreactor = Bioreactor("Liver Bioreactor", 10)

# Print the initial status
print(bioreactor)

# Create a tissue
tissue = Tissue("Liver Tissue", "Liver")

# Add the tissue to the bioreactor
bioreactor.add_tissue(tissue)

# Adjust environmental conditions
bioreactor.adjust_temperature(36.5)
bioreactor.adjust_pH(7.2)
bioreactor.adjust_oxygen_level(0.21)

# Add nutrients
bioreactor.add_nutrients(0.5)

# Simulate a time step
bioreactor.simulate_time_step()

# Print the updated status
print(bioreactor)

# Remove waste
bioreactor.remove_waste(0.3)

# Simulate another time step
bioreactor.simulate_time_step()

# Print the final status
print(bioreactor)
```

---

## Dependencies
- **`biobridge.blocks.tissue.Tissue`**: For tissue objects.

---

## Error Handling
- The class includes checks for capacity limits when adding tissues and ensures that nutrient and waste levels stay within valid ranges (0.0 to 1.0).

---

## Notes
- The `Bioreactor` class is designed to simulate a controlled environment for biological tissues.
- It supports adding and removing tissues, adjusting environmental conditions, and managing nutrient and waste levels.
- The `simulate_time_step` method applies the current conditions to each tissue and updates the nutrient and waste levels.
- The class provides methods for reporting the current status of the bioreactor.
