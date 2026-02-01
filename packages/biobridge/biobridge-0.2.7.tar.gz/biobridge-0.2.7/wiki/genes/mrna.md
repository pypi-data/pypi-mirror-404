# mRNA Class

## Overview
The `mRNA` class represents a messenger RNA molecule, including its sequence, cap, poly-A tail, untranslated regions (UTRs), coding sequence, and ribosome binding sites. It provides methods for simulating transcription, translation, degradation, alternative splicing, and motif finding.

---

## Class Definition

```python
class mRNA:
    def __init__(self, sequence):
        """
        Initialize a new mRNA object.
        :param sequence: The nucleotide sequence of the mRNA strand
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sequence` | `str` | Nucleotide sequence of the mRNA. |
| `cap` | `str` | 7-methylguanosine cap at the 5' end. |
| `poly_a_tail` | `str` | Poly-A tail at the 3' end. |
| `utr_5` | `str` | 5' untranslated region. |
| `utr_3` | `str` | 3' untranslated region. |
| `coding_sequence` | `str` | Coding sequence of the mRNA. |
| `ribosome_binding_sites` | `List[int]` | Positions of ribosome binding sites. |

---

## Methods

### Initialization and Modification
- **`__init__(self, sequence)`**
  Initializes a new `mRNA` instance with the specified sequence.

- **`add_cap(self)`**
  Adds a 7-methylguanosine cap to the 5' end of the mRNA.

- **`add_poly_a_tail(self, length=200)`**
  Adds a poly-A tail to the 3' end of the mRNA.

- **`set_utrs(self, utr_5, utr_3)`**
  Sets the 5' and 3' untranslated regions.

---

### Sequence Analysis
- **`find_start_codon(self)`**
  Finds the start codon (AUG) in the mRNA sequence.

- **`find_stop_codons(self)`**
  Finds all stop codons (UAA, UAG, UGA) in the mRNA sequence.

- **`set_coding_sequence(self)`**
  Sets the coding sequence based on start and stop codons.

- **`find_kozak_sequence(self)`**
  Finds the Kozak consensus sequence near the start codon.

- **`find_motifs(self, motif)`**
  Finds all occurrences of a specific motif in the mRNA sequence.

- **`get_gc_content(self)`**
  Calculates the GC content of the mRNA sequence.

---

### Transcription and Translation
- **`transcribe_to_mrna(self)`**
  Simulates transcription of DNA to mRNA.

- **`reverse_transcribe(self)`**
  Reverse transcribes the mRNA sequence into DNA.

- **`translate(self)`**
  Translates the coding sequence into a protein sequence.

---

### Ribosome Binding and Degradation
- **`add_ribosome_binding_site(self, position)`**
  Adds a ribosome binding site at the specified position.

- **`simulate_degradation(self, rate=0.01)`**
  Simulates mRNA degradation by shortening the poly-A tail.

---

### Alternative Splicing
- **`simulate_alternative_splicing(self, exon_ranges, base_inclusion_prob=0.7)`**
  Simulates alternative splicing using a probabilistic algorithm.

---

### Utility Methods
- **`__str__(self)`**
  Returns a string representation of the mRNA.

- **`__len__(self)`**
  Returns the total length of the mRNA, including cap and poly-A tail.

---

## Example Usage

```python
# Create an mRNA object
mrna = mRNA(sequence="AUGCCGUAUAGCGCUAUCGA")

# Add cap and poly-A tail
mrna.add_cap()
mrna.add_poly_a_tail()

# Set UTRs
mrna.set_utrs(utr_5="AAAAA", utr_3="CCCCC")

# Set coding sequence
mrna.set_coding_sequence()

# Translate the mRNA
protein_sequence = mrna.translate()
print(f"Protein sequence: {protein_sequence}")

# Simulate degradation
mrna.simulate_degradation(rate=0.1)

# Find Kozak sequence
kozak_sequence = mrna.find_kozak_sequence()
print(f"Kozak sequence: {kozak_sequence}")

# Simulate alternative splicing
exon_ranges = [(0, 5), (5, 10), (10, 15)]
included_exons = mrna.simulate_alternative_splicing(exon_ranges)
print(f"Included exons: {included_exons}")

# Print mRNA information
print(mrna)
```

---
