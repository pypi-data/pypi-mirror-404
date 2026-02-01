# Chromosome Class

## Overview
The `Chromosome` class simulates the structure, behavior, and properties of a biological chromosome, including arms, bands, centromeres, telomeres, and satellite DNA. It supports operations such as replication, crossover, mutation, inversion, transposition, and visualization.

---

## Class Definition

```python
class Chromosome:
    def __init__(self, dna: DNA, name: str):
        """
        Initialize a new Chromosome object.
        :param dna: DNA object representing the chromosome's genetic material
        :param name: Name of the chromosome
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the chromosome. |
| `p_arm` | `ChromosomeArm` | Short arm of the chromosome. |
| `q_arm` | `ChromosomeArm` | Long arm of the chromosome. |
| `centromere_position` | `int` | Position of the centromere. |
| `telomere_length` | `int` | Length of the telomeres. |
| `chromosome_type` | `str` | Type of chromosome (Metacentric, Submetacentric, Acrocentric, Telocentric). |
| `satellite_dna` | `Optional[DNA]` | Satellite DNA associated with the chromosome. |
| `constrictions` | `List[int]` | Positions of constrictions on the chromosome. |

---

## Methods

### Initialization and Arm Management
- **`__init__(self, dna: DNA, name: str)`**
  Initializes a new `Chromosome` instance with the specified DNA and name.

- **`set_arms(self, dna: DNA)`**
  Splits the DNA into p and q arms based on the centromere position.

- **`set_chromosome_type(self, chr_type: str)`**
  Sets the chromosome type.

- **`add_satellite_dna(self, satellite: DNA)`**
  Adds satellite DNA to the chromosome.

- **`add_constriction(self, position: int)`**
  Adds a constriction to the chromosome.

---

### Band Management
- **`add_band(self, arm: str, start: int, end: int, staining_pattern: str)`**
  Adds a band to either the p or q arm.

---

### Replication and Mutation
- **`replicate(self, mutation_rate: float = 0.001)`**
  Replicates the chromosome, potentially introducing mutations.

- **`mutate(self, mutation_rate: float = 0.001)`**
  Introduces random mutations in the chromosome.

- **`_mutate_sequence(self, sequence: str, mutation_rate: float) -> str`**
  Mutates a DNA sequence with a given mutation rate.

---

### Structural Changes
- **`crossover(self, other: 'Chromosome', crossover_points: List[int])`**
  Performs crossover with another chromosome.

- **`invert(self, start: int, end: int)`**
  Inverts a segment of the chromosome.

- **`_invert_dna_segment(self, dna: DNA, start: int, end: int) -> DNA`**
  Inverts a segment of DNA.

- **`transpose(self, start: int, end: int, new_position: int)`**
  Transposes a segment of the chromosome to a new position.

---

### Sequence and Property Retrieval
- **`get_sequence(self) -> str`**
  Retrieves the full DNA sequence of the chromosome.

- **`set_centromere(self, position: int)`**
  Sets the position of the centromere and updates arms.

- **`set_telomere_length(self, length: int)`**
  Sets the length of the telomeres.

- **`get_gc_content(self) -> float`**
  Calculates the GC content of the chromosome.

- **`find_genes(self, min_length: int = 100) -> List[Tuple[int, int, str]]`**
  Finds potential genes in the chromosome.

---

### Visualization
- **`visualize(self)`**
  Visualizes the chromosome structure, including arms, bands, and other features.

---

### Comparison and Serialization
- **`compare(self, other: 'Chromosome') -> float`**
  Compares this chromosome with another and returns a similarity score.

- **`to_dict(self) -> dict`**
  Converts the chromosome to a dictionary representation.

- **`from_dict(cls, data: dict) -> 'Chromosome'`**
  Creates a chromosome from a dictionary representation.

---

### Utility Methods
- **`__str__(self)`**
  Returns a string representation of the chromosome.

- **`__len__(self)`**
  Returns the length of the chromosome.

- **`__eq__(self, other)`**
  Checks if two chromosomes are equal.

- **`__hash__(self)`**
  Returns a hash of the chromosome.

- **`__getitem__(self, index)`**
  Allows indexing of the chromosome with wrap-around behavior.

---

## Example Usage

```python
# Create a DNA object
dna = DNA(sequence="ATGCGATCGATCGATCGATCGATCGATCGATCGATCG")

# Create a chromosome
chromosome = Chromosome(dna=dna, name="Chr1")

# Add a band to the p arm
chromosome.add_band(arm='p', start=0, end=5, staining_pattern="G")

# Replicate the chromosome
new_chromosome = chromosome.replicate(mutation_rate=0.001)

# Perform crossover with another chromosome
other_chromosome = Chromosome(dna=DNA("ATGCGATCGATCGATCGATCGATCGATCGATCGATCG"), name="Chr2")
crossover_chromosome = chromosome.crossover(other=other_chromosome, crossover_points=[10, 20])

# Visualize the chromosome
chromosome.visualize()

# Compare two chromosomes
similarity_score = chromosome.compare(other_chromosome)
print(f"Similarity score: {similarity_score}")

# Convert chromosome to dictionary
chromosome_dict = chromosome.to_dict()
```

---
