# rRNA Class

## Overview
The `rRNA` class represents a ribosomal RNA molecule, focusing on its sequence, processing, folding, and translation capabilities. It includes methods for simulating rRNA processing, cleavage, folding into secondary structures, and translation into protein sequences.

---

## Class Definition

```python
class rRNA:
    def __init__(self, sequence, id):
        """
        Initialize a new rRNA object.
        rRNA is typically a long precursor that undergoes processing to become functional.
        :param sequence: The nucleotide sequence of the rRNA strand (pre-rRNA)
        :param id: Unique identifier for the rRNA
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sequence` | `str` | Nucleotide sequence of the rRNA. |
| `mutation_probabilities` | `Dict[str, float]` | Mutation probabilities for each nucleotide. |
| `processed_rRNA` | `List[str]` | List of mature rRNA sequences after processing. |
| `cleavage_sites` | `List[str]` | List of known cleavage site sequences. |
| `id` | `str`/`int` | Unique identifier for the rRNA. |

---

## Methods

### Initialization
- **`__init__(self, sequence, id)`**
  Initializes a new `rRNA` instance with the specified sequence and unique identifier.

---

### Mutation
- **`mutate(self, index, new_nucleotide)`**
  Mutates the rRNA sequence at a specific index.

---

### Processing and Cleavage
- **`simulate_rRNA_processing(self)`**
  Simulates the processing of rRNA, cleaving the precursor into mature rRNA forms.

- **`find_cleavage_sites(self)`**
  Finds and returns positions of all cleavage sites in the RNA sequence.

- **`cleave_at_sites(self)`**
  Cleaves the RNA at all known cleavage sites.

---

### Folding and Structure
- **`simulate_folding(self)`**
  Simulates the folding of rRNA into a secondary structure.

- **`find_stem_loop(self, min_stem_length=4, max_loop_length=10)`**
  Identifies potential stem-loop structures in the RNA sequence.

- **`is_complementary(self, seq1, seq2)`**
  Checks if two sequences are complementary.

- **`display_stem_loop_structure(self)`**
  Displays the RNA sequence with potential stem-loop structures highlighted.

---

### Sequence Analysis
- **`gc_content(self)`**
  Calculates the GC content of the rRNA sequence.

---

### Translation
- **`transcribe_to_mrna(self)`**
  Transcribes the RNA sequence to mRNA, incorporating post-transcriptional modifications.

- **`translate_using_trna(self, coding_sequence)`**
  Translates the coding sequence of mRNA into a protein sequence using tRNA.

---

### Serialization and Deserialization
- **`to_dict(self)`**
  Converts the `rRNA` object to a dictionary.

- **`from_dict(cls, data)`**
  Creates an `rRNA` object from a dictionary.

- **`to_json(self)`**
  Converts the `rRNA` object to a JSON string.

- **`from_json(cls, json_str)`**
  Creates an `rRNA` object from a JSON string.

---

### Utility Methods
- **`__str__(self)`**
  Returns a string representation of the `rRNA` object.

- **`__len__(self)`**
  Returns the length of the rRNA sequence.

- **`__eq__(self, other)`**
  Checks if two `rRNA` objects are equal.

- **`__getitem__(self, index)`**
  Allows indexing of the rRNA sequence.

---

## Example Usage

```python
# Create an rRNA object
rrna = rRNA(sequence="GGCUCGAAUCAGCUCAUUACGUGAAGUUAGCUCGAAUCGGCUCGAAUCAGCUCA", id=1)

# Simulate rRNA processing
processed_rrna = rrna.simulate_rRNA_processing()
print(f"Processed rRNA: {processed_rrna}")

# Calculate GC content
gc_percent = rrna.gc_content()
print(f"GC content: {gc_percent:.2f}%")

# Find cleavage sites
cleavage_sites = rrna.find_cleavage_sites()
print(f"Cleavage sites: {cleavage_sites}")

# Simulate folding
stem_loops = rrna.simulate_folding()
print(f"Stem-loops: {stem_loops}")

# Transcribe to mRNA and translate
mrna, protein_sequence = rrna.transcribe_to_mrna()
print(f"Protein sequence: {protein_sequence}")

# Convert rRNA to dictionary and JSON
rrna_dict = rrna.to_dict()
rrna_json = rrna.to_json()
print(rrna_dict)
print(rrna_json)

# Create a new rRNA object from a dictionary
new_rrna = rRNA.from_dict(rrna_dict)
print(new_rrna)
```

---
