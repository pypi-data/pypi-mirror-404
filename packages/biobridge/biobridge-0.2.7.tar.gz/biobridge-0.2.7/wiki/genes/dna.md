# DNA Class

## Overview
The `DNA` class simulates the structure, behavior, and properties of a DNA molecule, including sequence manipulation, gene management, transcription, translation, mutation, and molecular weight calculation. It supports advanced operations such as finding motifs, palindromes, open reading frames (ORFs), and restriction sites, as well as data encoding/decoding.

---

## Class Definition

```python
class DNA:
    def __init__(self, sequence, genes=None):
        """
        Initialize a new DNA object.
        :param sequence: The nucleotide sequence of the DNA strand
        :param genes: A list of genes (optional), each represented by a tuple (gene_name, start_index, end_index)
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `strand1` | `List[Nucleotide]` | Primary strand of the DNA. |
| `strand2` | `List[Nucleotide]` | Complementary strand of the DNA. |
| `genes` | `List[Gene]` | List of genes encoded in the DNA. |
| `mutation_probabilities` | `Dict[str, float]` | Mutation probabilities for each nucleotide. |
| `sequence` | `str` | Nucleotide sequence of the primary strand. |
| `nucleotide_weights` | `Dict[str, float]` | Molecular weights of nucleotides (in Daltons). |

---

## Methods

### Initialization
- **`__init__(self, sequence, genes=None)`**
  Initializes a new `DNA` instance with the specified sequence and optional genes.

---

### Gene Management
- **`add_gene(self, name, sequence, inheritance)`**
  Adds a gene to the DNA sequence.

- **`remove_gene(self, name)`**
  Removes a gene from the DNA sequence.

- **`_find_insertion_point(self, gene_length)`**
  Finds a suitable insertion point for a new gene.

---

### Mutation Methods
- **`absolute_mutate(self, index, new_nucleotide, probability)`**
  Mutates the DNA sequence at a specific index with an absolute probability.

- **`mutate(self, index, new_base)`**
  Mutates the DNA sequence at a specific index based on nucleotide-specific probabilities.

- **`absolute_random_mutate(self, probability)`**
  Randomly mutates the DNA sequence with an absolute probability.

- **`random_mutate(self)`**
  Randomly mutates the DNA sequence based on nucleotide-specific probabilities.

---

### Sequence Retrieval
- **`get_sequence(self, strand=1)`**
  Retrieves the sequence of a specific strand.

---

### Transcription and Translation
- **`transcribe(self)`**
  Transcribes the DNA sequence into RNA.

- **`advanced_transcribe(self, start=0, end=None)`**
  Performs advanced transcription, incorporating splicing.

- **`construct_mrna(self, start=0, end=None)`**
  Constructs an mRNA object from the DNA sequence.

- **`transcribe_with_regulation(self, start=0, end=None, promoter_strength=1.0, enhancers=None, silencers=None)`**
  Performs transcription with regulatory elements.

- **`advanced_reverse_transcribe(self, rna)`**
  Performs advanced reverse transcription from RNA to DNA.

- **`reverse_transcribe_from_mrna(self, mrna)`**
  Performs reverse transcription from mRNA to DNA.

- **`translate(self, start=0, end=None)`**
  Translates the DNA sequence into an amino acid sequence.

---

### ORF and Motif Analysis
- **`find_orfs(self, min_length=100)`**
  Finds all open reading frames (ORFs) in the DNA sequence.

- **`find_motif(self, motif)`**
  Finds occurrences of a specific motif in the DNA sequence.

- **`find_repeats(self, min_length=2)`**
  Finds repeated sequences in the DNA.

- **`find_palindromes(self, min_length=4)`**
  Finds palindromic sequences in the DNA.

---

### Chemical and Structural Analysis
- **`gc_content(self)`**
  Calculates the GC content of the DNA sequence.

- **`codon_usage(self)`**
  Calculates the codon usage in the DNA sequence.

- **`hamming_distance(self, other_dna)`**
  Calculates the Hamming distance between this DNA sequence and another.

- **`find_restriction_sites(self, enzyme_sites)`**
  Finds restriction enzyme cut sites in the DNA sequence.

---

### Data Encoding and Decoding
- **`encode_8bit(self, input_data)`**
  Encodes general input data into the DNA sequence.

- **`decode_8bit(self, dna_sequence)`**
  Decodes a DNA sequence back into the original string.

- **`encode_binary(self, binary_data)`**
  Encodes binary data into the DNA sequence.

- **`decode_binary(self)`**
  Decodes the DNA sequence back into binary data.

- **`store_binary_data(self, binary_data)`**
  Stores binary data in the DNA sequence.

- **`retrieve_binary_data(self)`**
  Retrieves the stored binary data from the DNA sequence.

---

### Replication and Molecular Weight
- **`replicate(self, mutation_rate=0.001)`**
  Simulates DNA replication, potentially introducing mutations.

- **`calculate_molecular_weight(self)`**
  Calculates the molecular weight of the DNA and its genes.

- **`display_molecular_weights(self)`**
  Displays the molecular weights of the DNA and its genes.

---

### Visualization
- **`create_gene_heatmap(self)`**
  Creates a heatmap visualization of the genes in the DNA.

---

### Serialization and Deserialization
- **`to_dict(self)`**
  Converts the DNA object to a dictionary.

- **`from_dict(cls, data)`**
  Creates a `DNA` object from a dictionary.

- **`to_json(self)`**
  Converts the DNA object to a JSON string.

- **`from_json(cls, json_str)`**
  Creates a `DNA` object from a JSON string.

---

### Utility Methods
- **`describe(self)`**
  Provides a detailed description of the DNA, including its sequence and genes.

- **`has_mutation(self)`**
  Checks if the DNA sequence has any mutations.

- **`__len__(self)`**
  Returns the length of the DNA sequence.

- **`__getitem__(self, index)`**
  Allows indexing of the DNA sequence.

- **`__eq__(self, other)`**
  Checks if two DNA sequences are equal.

- **`__str__(self)`**
  Returns a string representation of the DNA.

---

## Example Usage

```python
# Create a DNA object
dna = DNA(sequence="ATGCGATCGATCGATCG")

# Add a gene
dna.add_gene(name="Gene1", sequence="ATGCGA", inheritance="dominant")

# Transcribe the DNA
rna = dna.transcribe()

# Find ORFs
orfs = dna.find_orfs()

# Calculate molecular weight
total_weight, gene_weights = dna.calculate_molecular_weight()

# Visualize genes
dna.create_gene_heatmap()

# Replicate the DNA
new_dna = dna.replicate(mutation_rate=0.001)
```

