# CRISPR Class

---

## Overview
The `CRISPR` class simulates CRISPR-Cas9 genome editing operations. It provides methods for finding target sequences, cutting DNA, inserting, deleting, and replacing sequences, as well as simulating off-target effects.

---

## Class Definition

```python
class CRISPR:
    def __init__(self, guide_rna: str):
        """
        Initialize a new CRISPR object.
        :param guide_rna: The guide RNA sequence used to target specific DNA sequences
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `guide_rna` | `str` | The guide RNA sequence used to target specific DNA sequences. |

---

## Methods

### Initialization
- **`__init__(self, guide_rna: str)`**
  Initializes a new `CRISPR` instance with the specified guide RNA sequence.

---

### Target Sequence Detection
- **`find_target_sequence(self, dna: DNA) -> List[int]`**
  Finds all occurrences of the target sequence in the DNA.

  - **Parameters**:
    - `dna`: The DNA object to search in.

  - **Returns**: A list of starting indices of the target sequence.

---

### DNA Editing Operations
- **`cut_dna(self, dna: DNA, index: int) -> Tuple[DNA, DNA]`**
  Simulates cutting the DNA at the specified index.

  - **Parameters**:
    - `dna`: The DNA object to cut.
    - `index`: The index at which to cut the DNA.

  - **Returns**: Two DNA objects representing the cut fragments.

- **`insert_sequence(self, dna: DNA, insert_seq: str, index: int) -> DNA`**
  Inserts a sequence into the DNA at the specified index.

  - **Parameters**:
    - `dna`: The DNA object to modify.
    - `insert_seq`: The sequence to insert.
    - `index`: The index at which to insert the sequence.

  - **Returns**: A new DNA object with the inserted sequence.

- **`delete_sequence(self, dna: DNA, start: int, end: int) -> DNA`**
  Deletes a sequence from the DNA between the specified indices.

  - **Parameters**:
    - `dna`: The DNA object to modify.
    - `start`: The starting index of the sequence to delete.
    - `end`: The ending index of the sequence to delete.

  - **Returns**: A new DNA object with the sequence deleted.

- **`replace_sequence(self, dna: DNA, replacement: str, start: int, end: int) -> DNA`**
  Replaces a sequence in the DNA with a new sequence.

  - **Parameters**:
    - `dna`: The DNA object to modify.
    - `replacement`: The replacement sequence.
    - `start`: The starting index of the sequence to replace.
    - `end`: The ending index of the sequence to replace.

  - **Returns**: A new DNA object with the replaced sequence.

---

### Genome Editing
- **`edit_genome(self, dna: DNA, edit_type: str, *args) -> DNA`**
  Performs a CRISPR edit on the DNA.

  - **Parameters**:
    - `dna`: The DNA object to edit.
    - `edit_type`: The type of edit to perform (`'insert'`, `'delete'`, or `'replace'`).
    - `*args`: Additional arguments specific to the edit type.

  - **Returns**: A new DNA object with the edit applied.

  - **Raises**: `ValueError` if the edit type is invalid.

---

### Off-Target Effects
- **`simulate_off_target_effects(self, dna: DNA, mutation_rate: float = 0.1) -> DNA`**
  Simulates off-target effects of CRISPR editing.

  - **Parameters**:
    - `dna`: The DNA object to potentially modify.
    - `mutation_rate`: The probability of an off-target mutation occurring.

  - **Returns**: A potentially modified DNA object.

---

## Example Usage

```python
# Initialize a DNA object
dna = DNA(sequence="ATGCGATCGATCGATCGATCGATCGATCG")

# Initialize a CRISPR object with a guide RNA
guide_rna = "GATC"
crisp = CRISPR(guide_rna)

# Find target sequences
target_sites = crisp.find_target_sequence(dna)
print(f"Target sites: {target_sites}")

# Edit the genome by inserting a sequence
edited_dna = crisp.edit_genome(dna, 'insert', "TTTT")
print(f"Edited DNA sequence: {edited_dna.sequence}")

# Edit the genome by deleting a sequence
edited_dna = crisp.edit_genome(dna, 'delete', 4)
print(f"Edited DNA sequence: {edited_dna.sequence}")

# Edit the genome by replacing a sequence
edited_dna = crisp.edit_genome(dna, 'replace', "AAAA")
print(f"Edited DNA sequence: {edited_dna.sequence}")

# Simulate off-target effects
mutated_dna = crisp.simulate_off_target_effects(dna)
print(f"Mutated DNA sequence: {mutated_dna.sequence}")
```

---

## Expected Output

```
Target sites: [2, 8, 14, 20, 26]
Edited DNA sequence: ATGCGATTTTTTCGATCGATCGATCGATCGATCG
Edited DNA sequence: ATGCGAT
Edited DNA sequence: ATGCAAACGATCGATCGATCGATCGATCG
Off-target mutation occurred at position 12
Mutated DNA sequence: ATGCGATCGATAGATCGATCGATCGATCG
```

---

## Dependencies
- **`random`**: For simulating random off-target effects and selecting target sites.
- **`DNA`**: Class representing DNA sequences.

---

## Error Handling
- The `edit_genome` method raises a `ValueError` if an invalid edit type is provided.
- The `find_target_sequence` method returns an empty list if no target sites are found.

---

## Notes
- The `CRISPR` class is designed to simulate basic CRISPR-Cas9 genome editing operations.
- The `edit_genome` method supports three types of edits: insert, delete, and replace.
- The `simulate_off_target_effects` method simulates potential unintended mutations that can occur during CRISPR editing.
