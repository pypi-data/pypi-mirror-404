# MolecularMachinery Class

---

## Overview
The `MolecularMachinery` class simulates complex molecular machines such as ribosomes, ATP synthases, and DNA polymerases. It models their components, functions, efficiency, energy consumption, and interactions with proteins and cells. The class supports serialization to/from JSON, performance tracking, and maintenance operations.

---

## Class Definition

```python
class MolecularMachinery:
    def __init__(self, name: str, components: List[Union[Protein, Cell]], function: str):
        """
        Initialize a new MolecularMachinery object.
        :param name: Name of the molecular machinery
        :param components: List of Protein or Cell components
        :param function: Biological function of the machinery
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the molecular machinery. |
| `components` | `List[Union[Protein, Cell]]` | List of Protein or Cell components. |
| `function` | `str` | Biological function of the machinery. |
| `efficiency` | `float` | Efficiency of the machinery (0.0 to 1.0). |
| `energy_level` | `float` | Current energy level (0.0 to 100.0). |
| `energy_consumed` | `float` | Total energy consumed. |
| `performance_history` | `List[bool]` | History of performance outcomes. |
| `last_maintenance` | `float` | Timestamp of the last maintenance. |
| `age` | `int` | Age of the machinery. |
| `mutation_rate` | `float` | Probability of mutation. |

---

## Methods

### Initialization
- **`__init__(self, name: str, components: List[Union[Protein, Cell]], function: str)`**
  Initializes a new `MolecularMachinery` instance with the specified name, components, and function.

---

### Factory Methods
- **`create_ribosome(cls)`**
  Creates a ribosome molecular machinery.

  - **Returns**: A `MolecularMachinery` instance representing a ribosome.

- **`create_atp_synthase(cls)`**
  Creates an ATP synthase molecular machinery.

  - **Returns**: A `MolecularMachinery` instance representing an ATP synthase.

- **`create_dna_polymerase(cls)`**
  Creates a DNA polymerase molecular machinery.

  - **Returns**: A `MolecularMachinery` instance representing a DNA polymerase.

- **`create_custom(cls, name: str, components: List[Union[Protein, Cell]], function: str)`**
  Creates a custom molecular machinery.

  - **Parameters**:
    - `name`: Name of the molecular machinery.
    - `components`: List of Protein or Cell components.
    - `function`: Biological function of the machinery.

  - **Returns**: A `MolecularMachinery` instance with the specified parameters.

---

### Interaction
- **`interact(self, target: Union[Protein, Cell]) -> str`**
  Simulates an interaction between the machinery and a target (protein or cell).

  - **Parameters**:
    - `target`: The target to interact with (Protein or Cell).

  - **Returns**: A string describing the interaction.

---

### Function Performance
- **`perform_function(self) -> str`**
  Simulates the machinery performing its function.

  - **Returns**: A string describing the outcome of the function performance.

---

### Energy Management
- **`energy_consumption_report(self) -> str`**
  Reports the total energy consumed by the machinery.

  - **Returns**: A string describing the energy consumption.

- **`recharge(self, amount: float) -> str`**
  Recharges the machinery's energy level.

  - **Parameters**:
    - `amount`: The amount of energy to recharge.

  - **Returns**: A string describing the new energy level.

- **`consume_energy(self, amount: float) -> None`**
  Consumes energy from the machinery.

  - **Parameters**:
    - `amount`: The amount of energy to consume.

---

### Component Management
- **`component_details(self) -> str`**
  Provides details about the machinery's components.

  - **Returns**: A string listing the components and their details.

- **`add_component(self, component: Union[Protein, Cell]) -> str`**
  Adds a component to the machinery.

  - **Parameters**:
    - `component`: The component to add (Protein or Cell).

  - **Returns**: A string confirming the addition or indicating an error.

- **`remove_component(self, component_name: str) -> str`**
  Removes a component from the machinery.

  - **Parameters**:
    - `component_name`: The name of the component to remove.

  - **Returns**: A string confirming the removal or indicating an error.

---

### Aging and Mutation
- **`age_machinery(self, time_units: int) -> str`**
  Simulates the aging of the machinery.

  - **Parameters**:
    - `time_units`: The number of time units to age the machinery.

  - **Returns**: A string describing the new efficiency.

- **`mutate(self) -> str`**
  Simulates a mutation in the machinery.

  - **Returns**: A string describing the mutation outcome.

---

### Maintenance
- **`perform_maintenance(self) -> str`**
  Performs maintenance on the machinery.

  - **Returns**: A string describing the maintenance outcome.

- **`emergency_shutdown(self) -> str`**
  Performs an emergency shutdown of the machinery.

  - **Returns**: A string confirming the shutdown.

---

### Performance Analysis
- **`analyze_performance(self) -> str`**
  Analyzes the performance history of the machinery.

  - **Returns**: A string describing the performance analysis.

- **`optimize(self) -> str`**
  Optimizes the machinery's efficiency.

  - **Returns**: A string describing the optimization outcome.

---

### Internal Interaction
- **`internal_interaction(self) -> str`**
  Simulates an interaction between the machinery's components.

  - **Returns**: A string describing the interaction.

---

### Serialization
- **`to_json(self) -> str`**
  Converts the machinery to a JSON string representation.

  - **Returns**: A JSON string representing the machinery.

- **`from_json(cls, json_str: str) -> 'MolecularMachinery'`**
  Creates a `MolecularMachinery` instance from a JSON string.

  - **Parameters**:
    - `json_str`: A JSON string representing the machinery.

  - **Returns**: A `MolecularMachinery` instance.

---

### String Representation
- **`__str__(self) -> str`**
  Returns a string representation of the machinery.

  - **Returns**: A string describing the machinery.

---

## Example Usage

```python
# Create a ribosome
ribosome = MolecularMachinery.create_ribosome()
print(ribosome)

# Create an ATP synthase
atp_synthase = MolecularMachinery.create_atp_synthase()
print(atp_synthase)

# Create a DNA polymerase
dna_polymerase = MolecularMachinery.create_dna_polymerase()
print(dna_polymerase)

# Create a custom molecular machinery
protein1 = Protein("Custom Protein 1", "ATGCGATCG")
protein2 = Protein("Custom Protein 2", "TACGTAGCT")
custom_machinery = MolecularMachinery.create_custom("Custom Machinery", [protein1, protein2], "Custom Function")
print(custom_machinery)

# Perform a function
print(ribosome.perform_function())

# Interact with a protein
protein = Protein("Target Protein", "GATCGATCG")
print(ribosome.interact(protein))

# Recharge energy
print(ribosome.recharge(50))

# Add a component
print(ribosome.add_component(protein))

# Remove a component
print(ribosome.remove_component("Small subunit"))

# Age the machinery
print(ribosome.age_machinery(10))

# Mutate the machinery
print(ribosome.mutate())

# Perform maintenance
print(ribosome.perform_maintenance())

# Analyze performance
print(ribosome.analyze_performance())

# Optimize the machinery
print(ribosome.optimize())

# Emergency shutdown
print(ribosome.emergency_shutdown())

# Serialize to JSON
json_str = ribosome.to_json()
print(json_str)

# Deserialize from JSON
new_ribosome = MolecularMachinery.from_json(json_str)
print(new_ribosome)
```

---

## Dependencies
- **`random`**: For simulating random events such as mutations and interactions.
- **`json`**: For JSON serialization and deserialization.
- **`time`**: For tracking the last maintenance time.
- **`biobridge.blocks.protein.Protein`**: For protein components.
- **`biobridge.blocks.cell.Cell`**: For cell components.

---

## Error Handling
- The class includes basic checks for valid component types and handles potential errors during component addition and removal.

---

## Notes
- The `MolecularMachinery` class is designed to simulate complex molecular machines.
- It supports common molecular machines such as ribosomes, ATP synthases, and DNA polymerases.
- The class models energy consumption, efficiency, and performance history.
- Serialization methods allow for saving and loading the machinery's state.
