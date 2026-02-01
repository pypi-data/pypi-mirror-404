# PCR Class

---

## Overview
The `PCR` (Polymerase Chain Reaction) class simulates the PCR amplification process. It allows for the identification of primer binding sites, amplification of DNA sequences, and introduction of random mutations during the amplification process.

---

## Class Definition

```python
class PCR:
    def __init__(self, sequence, forward_primer, reverse_primer, cycles=30, mutation_rate=0.001):
        """
        Initialize a new PCR object.
        :param sequence: The nucleotide sequence of the DNA or RNA strand
        :param forward_primer: The forward primer sequence
        :param reverse_primer: The reverse primer sequence
        :param cycles: Number of PCR cycles (default is 30)
        :param mutation_rate: The probability of a mutation occurring at each nucleotide (default is 0.001)
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sequence` | `str` | The nucleotide sequence of the DNA or RNA strand. |
| `forward_primer` | `str` | The forward primer sequence. |
| `reverse_primer` | `str` | The reverse primer sequence. |
| `cycles` | `int` | Number of PCR cycles. |
| `mutation_rate` | `float` | Probability of a mutation occurring at each nucleotide. |

---

## Methods

### Initialization
- **`__init__(self, sequence, forward_primer, reverse_primer, cycles=30, mutation_rate=0.001)`**
  Initializes a new `PCR` instance with the specified sequence, primers, number of cycles, and mutation rate.

---

### Primer Binding Site Detection
- **`find_primer_binding_sites(self) -> Tuple[List[int], List[int]]`**
  Finds the binding sites of the forward and reverse primers in the sequence.

  - **Returns**: A tuple containing lists of start positions for the forward and reverse primers.

---

### PCR Amplification
- **`amplify(self) -> List[str]`**
  Simulates the PCR amplification process.

  - **Returns**: A list of amplified sequences.

  - **Details**:
    - For each cycle, the method finds the binding sites of the primers and amplifies the sequence between them.
    - Each amplified sequence may contain mutations introduced during the amplification process.

---

### Mutation Introduction
- **`introduce_mutations(self, sequence) -> str`**
  Introduces random mutations into a nucleotide sequence.

  - **Parameters**:
    - `sequence`: The nucleotide sequence to mutate.

  - **Returns**: The mutated sequence.

  - **Details**:
    - Each nucleotide in the sequence has a probability of being mutated, as specified by the `mutation_rate`.

---

### Description
- **`describe(self) -> str`**
  Provides a detailed description of the PCR process.

  - **Returns**: A string containing the description of the PCR process, including the sequence, primers, number of cycles, and mutation rate.

- **`__str__(self) -> str`**
  Returns a string representation of the PCR process.

  - **Returns**: A string representation of the PCR process.

---

## Example Usage

```python
# Initialize a PCR object
sequence = "ATGCGATCGATCGATCGATCGATCGATCGATCG"
forward_primer = "ATGCG"
reverse_primer = "CGATC"
pcr = PCR(sequence, forward_primer, reverse_primer, cycles=3, mutation_rate=0.01)

# Find primer binding sites
forward_positions, reverse_positions = pcr.find_primer_binding_sites()
print(f"Forward primer positions: {forward_positions}")
print(f"Reverse primer positions: {reverse_positions}")

# Simulate PCR amplification
amplified_sequences = pcr.amplify()
print(f"Amplified sequences: {amplified_sequences}")

# Describe the PCR process
print(pcr.describe())

# String representation of the PCR process
print(pcr)
```

---

## Expected Output

```
Forward primer positions: [0]
Reverse primer positions: [24]
Amplified sequences: ['ATGCGATCGATCGATCGATCGATCGATC', 'ATGCGATCGATCGATCGATCGATCGATC', 'ATGCGATCGATCGATCGATCGATCGATG']
PCR Process:
Sequence: ATGCGATCGATCGATCGATCGATCGATCGATCG
Forward Primer: ATGCG
Reverse Primer: CGATC
Cycles: 3
Mutation Rate: 0.001
```

---

## Dependencies
- **`random`**: For introducing random mutations.
- **`re`**: For finding primer binding sites using regular expressions.

---

## Error Handling
- The class does not explicitly handle errors, but it relies on the `re` module for finding primer binding sites, which will raise an error if the input is not a string.

---

## Notes
- The `PCR` class is designed to simulate the basic principles of the Polymerase Chain Reaction.
- The `amplify` method simulates the amplification process over a specified number of cycles.
- The `introduce_mutations` method simulates the introduction of random mutations during the amplification process.
- The `describe` and `__str__` methods provide a human-readable description of the PCR process.
