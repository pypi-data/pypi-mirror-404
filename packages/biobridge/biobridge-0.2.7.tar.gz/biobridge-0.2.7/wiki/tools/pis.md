# ProteinInteractionSimulator Class

---

## Overview
The `ProteinInteractionSimulator` class provides tools for simulating and analyzing interactions between proteins and biological targets such as cells or viruses. It calculates binding affinity, destructive potential, side effects, and success chances of these interactions.

---

## Class Definition

```python
class ProteinInteractionSimulator:
    def __init__(self, protein: Protein):
        """
        Initialize a new ProteinInteractionSimulator object.
        :param protein: The protein to simulate interactions for
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `protein` | `Protein` | The protein to simulate interactions for. |

---

## Methods

### Initialization
- **`__init__(self, protein: Protein)`**
  Initializes a new `ProteinInteractionSimulator` instance with the specified protein.

---

### Binding Affinity Calculation
- **`calculate_binding_affinity(self, target: Union[Cell, Virus]) -> float`**
  Calculates the binding affinity of the protein to the target (cell or virus).

  - **Parameters**:
    - `target`: The target of the interaction (Cell or Virus).

  - **Returns**: A value between 0 (no binding) and 1 (perfect binding).

  - **Details**:
    - Checks for matching receptors or surface proteins.
    - Considers the protein's activeness.

---

### Destructive Potential Calculation
- **`calculate_destructive_potential(self, target: Union[Cell, Virus]) -> float`**
  Calculates the destructive potential of the protein against the target.

  - **Parameters**:
    - `target`: The target of the interaction (Cell or Virus).

  - **Returns**: A value between 0 (no destruction) and 1 (complete destruction).

  - **Details**:
    - Considers the protein's activeness.
    - Checks for inhibitory interactions.
    - Considers target health (for cells) or virulence (for viruses).

---

### Side Effects Calculation
- **`calculate_side_effects(self) -> List[str]`**
  Calculates potential side effects based on the protein's properties.

  - **Returns**: A list of potential side effects.

  - **Details**:
    - Considers the protein's activeness.
    - Considers the number of interactions and bindings.

---

### Success Chance Calculation
- **`calculate_success_chance(self, target: Union[Cell, Virus]) -> float`**
  Calculates the overall chance of successful interaction with the target.

  - **Parameters**:
    - `target`: The target of the interaction (Cell or Virus).

  - **Returns**: A value between 0 (no chance of success) and 1 (guaranteed success).

  - **Details**:
    - Combines binding affinity and destructive potential.
    - Considers side effects as a negative factor.

---

### Interaction Simulation
- **`simulate_interaction(self, target: Union[Cell, Virus]) -> dict`**
  Simulates the interaction between the protein and the target.

  - **Parameters**:
    - `target`: The target of the interaction (Cell or Virus).

  - **Returns**: A dictionary with the simulation results, including binding affinity, destructive potential, side effects, success chance, and outcome.

  - **Details**:
    - Simulates the interaction based on calculated values.
    - Determines the outcome based on the success chance.

---

### String Representation
- **`__str__(self) -> str`**
  Returns a string representation of the `ProteinInteractionSimulator`.

  - **Returns**: A string describing the simulator and its protein.

---

## Example Usage

```python
# Create a protein
protein = Protein("Antiviral Protein", "MIVSDIEANALLESVTKFHCGVIYDYSTAEYVSYRPSDFGAYLDALEAEVARGGLIVFHNGHKYDVPALTKLAKLQLNREFHLPRENCIDTLVLSRLIHSNLKDTDMGLLRSGKLPGKRFGSHALEAWGYRLGEMKGEYKDDFKRMLEEQGEEYVDGMEWWNFNEEMMDYNVQDVVVTKALLEKLLSDKHYFPPEIDFTDVGYTTFWSESLEAVDIEHRAAWLLAKQERNGFPFDTKAIEELYVELAARRSELLRKLTETFGSWYQPKGGTEMFCHPRTGKPLPKYPRIKTPKVGGIFKKPKNKAQREGREPCELDTREYVAGAPYTPVEHVVFNPSSRDHIQKKLQEAGWVPTKYTDKGAPVVDDEVLEGVRVDDPEKQAAIDLIKEYLMIQKRIGQSAEGDKAWLRYVAEDGKIHGSVNPNGAVTGRATHAFPNLAQIPGVRSPYGEQCRAAFGAEHHLDGITGKPWVQAGIDASGLELRCLAHFMARFDNGEYAHEILNGDIHTKNQIAAELPTRDNAKTFIYGFLYGAGDEKIGQIVGAGKERGKELKKKFLENTPAIAALRESIQQTLVESSQWVAGEQQVKWKRRWIKGLDGRKVHVRSPHAALNTLLQSAGALICKLWIIKTEEMLVEKGLKHGWDGDFAYMAWVHDEIQVGCRTEEIAQVVIETAQEAMRWVGDHWNFRCLLDTEGKMGPNWAICH")

# Create a cell
cell = Cell("Liver Cell", "Liver")
cell.receptors = ["Receptor1", "Receptor2"]
cell.surface_proteins = ["Protein1", "Protein2"]

# Create a virus
virus = Virus("Influenza Virus", "RNA")
virus.virulence = 0.7

# Initialize the simulator
simulator = ProteinInteractionSimulator(protein)

# Calculate binding affinity
binding_affinity_cell = simulator.calculate_binding_affinity(cell)
binding_affinity_virus = simulator.calculate_binding_affinity(virus)
print(f"Binding affinity to cell: {binding_affinity_cell}")
print(f"Binding affinity to virus: {binding_affinity_virus}")

# Calculate destructive potential
destructive_potential_cell = simulator.calculate_destructive_potential(cell)
destructive_potential_virus = simulator.calculate_destructive_potential(virus)
print(f"Destructive potential to cell: {destructive_potential_cell}")
print(f"Destructive potential to virus: {destructive_potential_virus}")

# Calculate side effects
side_effects = simulator.calculate_side_effects()
print(f"Potential side effects: {side_effects}")

# Calculate success chance
success_chance_cell = simulator.calculate_success_chance(cell)
success_chance_virus = simulator.calculate_success_chance(virus)
print(f"Success chance with cell: {success_chance_cell}")
print(f"Success chance with virus: {success_chance_virus}")

# Simulate interaction
simulation_result_cell = simulator.simulate_interaction(cell)
simulation_result_virus = simulator.simulate_interaction(virus)
print(f"Simulation result with cell: {simulation_result_cell}")
print(f"Simulation result with virus: {simulation_result_virus}")

# String representation
print(simulator)
```

---

## Dependencies
- **`random`**: For simulating random events during interaction.
- **`biobridge.blocks.protein.Protein`**: For protein objects.
- **`biobridge.blocks.cell.Cell`**: For cell objects.
- **`biobridge.definitions.virus.Virus`**: For virus objects.

---

## Error Handling
- The class does not explicitly handle errors, but it relies on the underlying methods of the protein, cell, and virus classes to handle their own errors.

---

## Notes
- The `ProteinInteractionSimulator` class is designed to simulate and analyze interactions between proteins and biological targets.
- It supports both cells and viruses as targets.
- The class provides methods for calculating binding affinity, destructive potential, side effects, and success chances.
- The `simulate_interaction` method simulates the interaction and determines the outcome based on calculated values.
