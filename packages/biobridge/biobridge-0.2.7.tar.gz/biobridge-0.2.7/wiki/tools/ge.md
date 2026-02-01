# GelElectrophoresis Class

## Overview
The `GelElectrophoresis` class simulates the process of gel electrophoresis, a technique used to separate DNA fragments based on size. This improved version supports **DNA ladders**, **sample labeling**, **concentration tracking**, **size estimation**, and **detailed reporting**.

---

## Class Definition
```python
class GelElectrophoresis:
    def __init__(
        self,
        gel_length: int = 100,
        voltage: float = 100.0,
        gel_concentration: float = 1.0,
        buffer_type: str = "TAE"
    ):
        """
        Initialize a new GelElectrophoresis object.
        :param gel_length: Length of the gel in millimeters (default: 100)
        :param voltage: Voltage applied during electrophoresis (default: 100.0)
        :param gel_concentration: Concentration of the gel in percent (default: 1.0)
        :param buffer_type: Type of buffer used (default: "TAE")
        """
        ...
```

---

## Attributes


| Attribute | Type | Description |
|-----------|------|-------------|
| `gel_length` | `int` | Length of the gel in millimeters. |
| `voltage` | `float` | Voltage applied during electrophoresis. |
| `gel_concentration` | `float` | Concentration of the gel in percent. |
| `buffer_type` | `str` | Type of buffer used (e.g., "TAE", "TBE"). |
| `samples` | `List[Dict]` | List of loaded DNA samples, each with a label and concentration. |
| `ladder` | `Optional[List[int]]` | List of DNA ladder sizes in base pairs. |
| `run_complete` | `bool` | Whether electrophoresis has been run. |
| `results` | `List[Tuple[DNA, int, str]]` | Results of electrophoresis: DNA, migration distance, and label. |

---

## Methods

### Initialization
- **`__init__(self, gel_length: int = 100, voltage: float = 100.0, gel_concentration: float = 1.0, buffer_type: str = "TAE")`**
  Initializes a new `GelElectrophoresis` instance with the specified parameters.

---

### Sample Management
- **`load_sample(self, dna: DNA, label: str = "", concentration: float = 1.0)`**
  Loads a DNA sample into the gel.
  - **Parameters**:
    - `dna`: The DNA object to load.
    - `label`: Optional label for the sample.
    - `concentration`: Concentration of the sample.

- **`clear_samples(self)`**
  Clears all loaded samples and results.

- **`set_ladder(self, sizes: List[int])`**
  Sets a DNA ladder for size reference.
  - **Parameters**:
    - `sizes`: List of DNA ladder sizes in base pairs.

---

### Electrophoresis Process
- **`run_electrophoresis(self, duration: float) -> List[Tuple[DNA, int, str]]`**
  Simulates the electrophoresis process.
  - **Parameters**:
    - `duration`: Duration of the electrophoresis in minutes.
  - **Returns**: List of tuples: `(DNA, migration distance, label)`, sorted by migration distance.
  - **Details**:
    - Migration distance is calculated using voltage, gel concentration, and DNA length.
    - Shorter DNA fragments migrate further.

---

### Visualization
- **`visualize_results(self, results: Optional[List[Tuple[DNA, int, str]]] = None, show_ladder: bool = True, duration: float = 60.0)`**
  Visualizes the gel electrophoresis results as an ASCII diagram.
  - **Parameters**:
    - `results`: Optional results to visualize (defaults to last run).
    - `show_ladder`: Whether to display the DNA ladder.
    - `duration`: Duration used for ladder position calculation.

---

### Analysis
- **`estimate_size(self, migration_distance: int, duration: float = 60.0) -> Optional[int]`**
  Estimates the size of a DNA fragment based on its migration distance.
  - **Parameters**:
    - `migration_distance`: Distance migrated on the gel.
    - `duration`: Duration of the electrophoresis.
  - **Returns**: Estimated size in base pairs, or `None` if no ladder is set.

- **`generate_report(self) -> str`**
  Generates a detailed report of the electrophoresis run.
  - **Returns**: Formatted report string.

---

## Example Usage
```python
# Initialize the GelElectrophoresis
gel = GelElectrophoresis(gel_length=100, voltage=100.0, gel_concentration=1.0, buffer_type="TAE")

# Set a DNA ladder
gel.set_ladder([100, 200, 300, 400, 500])

# Create and load DNA samples
dna1 = DNA(sequence="ATGCGATCG")
dna2 = DNA(sequence="ATGCGATCGATCGATCGATCG")
dna3 = DNA(sequence="ATGCGATCGATCGATCGATCGATCGATCGATCG")

gel.load_sample(dna1, label="Sample 1")
gel.load_sample(dna2, label="Sample 2")
gel.load_sample(dna3, label="Sample 3")

# Run electrophoresis
results = gel.run_electrophoresis(duration=30.0)

# Visualize the results
gel.visualize_results()

# Generate a report
print(gel.generate_report())

# Estimate size of a band
size = gel.estimate_size(migration_distance=50)
print(f"Estimated size: {size} bp")
```

---

## Expected Output
```
Gel Electrophoresis Results
Voltage: 100.0V | Gel: 1.0% | Buffer: TAE

       +----------------------------------------------------------------------------------------------------+
Ladder | |═                                                                                                   |
Sample 1 | |          █                                                                                      |
Sample 2 | |                     █                                                                           |
Sample 3 | |                                █                                                              |
       +----------------------------------------------------------------------------------------------------+
```

---

## Dependencies
- **`DNA`**: Class representing DNA sequences.

---

## Error Handling
- Raises `ValueError` if electrophoresis is run without loaded samples or if visualization is attempted before running electrophoresis.

---

## Notes
- The **DNA ladder** allows for size estimation of unknown fragments.
- The **visualization** now supports multiple lanes and a ruler for distance reference.
- The **report** provides a detailed summary of experimental conditions and results.
