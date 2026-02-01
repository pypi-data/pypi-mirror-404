# Infection Class

---

## Overview
The `Infection` class models a biological infection, such as a parasite, bacteria, or virus. It includes properties like spread rate, genetic code, and a list of infected cells. The class provides methods for infecting cells, replicating within cells, exiting cells, and mutating.

---

## Class Definition

```python
class Infection:
    def __init__(self, name: str, infection_type: InfectionType, spread_rate: float, genetic_code: str):
        """
        Initialize a new Infection object.
        :param name: Name of the infection
        :param infection_type: Type of infection (parasite, bacteria, or virus)
        :param spread_rate: Rate at which the infection spreads (0.0 to 1.0)
        :param genetic_code: Genetic code of the infection
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the infection. |
| `infection_type` | `InfectionType` | Type of infection (parasite, bacteria, or virus). |
| `spread_rate` | `float` | Rate at which the infection spreads (0.0 to 1.0). |
| `genetic_code` | `str` | Genetic code of the infection. |
| `infected_cells` | `List[str]` | List of names of infected cells. |

---

## Enums

### InfectionType
```python
class InfectionType(Enum):
    PARASITE = "parasite"
    BACTERIA = "bacteria"
    VIRUS = "virus"
```

---

## Methods

### Initialization
- **`__init__(self, name: str, infection_type: InfectionType, spread_rate: float, genetic_code: str)`**
  Initializes a new `Infection` instance with the specified name, infection type, spread rate, and genetic code.

---

### Infection and Replication
- **`infect(self, cell: Cell) -> bool`**
  Attempts to infect a cell.

  - **Parameters**:
    - `cell`: The cell to attempt to infect.

  - **Returns**: `True` if the infection is successful, `False` otherwise.

- **`replicate(self, cell: Cell) -> None`**
  Simulates replication within an infected cell, reducing the cell's health.

  - **Parameters**:
    - `cell`: The infected cell.

---

### Exit and Mutation
- **`exit_cell(self, cell: Cell) -> Optional[Infection]`**
  Attempts to exit an infected cell, potentially creating a new infection instance.

  - **Parameters**:
    - `cell`: The infected cell.

  - **Returns**: A new `Infection` instance if the exit is successful, `None` otherwise.

- **`mutate(self) -> None`**
  Simulates a random mutation in the infection, affecting either the spread rate or the genetic code.

---

### Description
- **`describe(self) -> str`**
  Provides a detailed description of the infection.

- **`__str__(self) -> str`**
  Returns a string representation of the infection.

---

## Example Usage

```python
# Create an infection
infection = Infection(
    name="Influenza",
    infection_type=InfectionType.VIRUS,
    spread_rate=0.7,
    genetic_code="ATCGATCGATCG"
)

# Create a cell
cell = Cell(name="Cell1", cell_type="epithelial")

# Attempt to infect the cell
success = infection.infect(cell)
print(f"Infection successful: {success}")

# Simulate replication within the cell
infection.replicate(cell)
print(f"Cell health after replication: {cell.health}")

# Attempt to exit the cell
new_infection = infection.exit_cell(cell)
if new_infection:
    print(f"New infection created: {new_infection.name}")

# Simulate mutation
infection.mutate()
print(f"Infection spread rate after mutation: {infection.spread_rate}")
print(f"Infection genetic code after mutation: {infection.genetic_code}")

# Describe the infection
print(infection.describe())
```

---

## Expected Output

```
Infection successful: True
Cell health after replication: 85.0
Random value: 0.65, Spread rate: 0.7
New infection created: Influenza_offspring
Infection spread rate after mutation: 0.774
Infection genetic code after mutation: ATCGGTGATCG
Infection Name: Influenza
Type: virus
Spread Rate: 0.77
Genetic Code: ATCGGTGATCG
Infected Cells: 1
```

---

## Dependencies
- **`random`**: For simulating random events such as infection success and mutation.
- **`typing`**: For type hints.
- **`Enum`**: For defining the `InfectionType` enum.
- **`Cell`**: Class representing a biological cell.

---

## Error Handling
- The `replicate` method includes a check for `cell.health` being `None` to avoid errors.
- The `spread_rate` is clamped between 0.0 and 1.0 to ensure valid values.

---

## Notes
- The `Infection` class is designed to model the behavior of biological infections.
- The `infect` method uses a random number to determine if the infection is successful based on the spread rate.
- The `replicate` method reduces the health of the infected cell.
- The `exit_cell` method creates a new infection instance if the exit is successful.
- The `mutate` method randomly changes either the spread rate or the genetic code.
