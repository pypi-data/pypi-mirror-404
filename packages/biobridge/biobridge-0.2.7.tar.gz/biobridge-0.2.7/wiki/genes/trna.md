# tRNA Class

## Overview
The `tRNA` class represents a transfer RNA molecule, inheriting from the `RNA` class. It includes functionality for managing anticodons, amino acids, and binding to mRNA sequences, as well as serialization and deserialization methods.

---

## Class Definition

```python
class tRNA(RNA):
    def __init__(self, sequence, anticodon, amino_acid):
        """
        Initialize a new tRNA object.
        :param sequence: The nucleotide sequence of the tRNA strand
        :param anticodon: The anticodon sequence of the tRNA
        :param amino_acid: The amino acid carried by the tRNA
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sequence` | `str` | Nucleotide sequence of the tRNA. |
| `anticodon` | `str` | Anticodon sequence of the tRNA. |
| `amino_acid` | `str` | Amino acid carried by the tRNA. |

---

## Methods

### Initialization
- **`__init__(self, sequence, anticodon, amino_acid)`**
  Initializes a new `tRNA` instance with the specified sequence, anticodon, and amino acid.

---

### Anticodon and Amino Acid Management
- **`get_anticodon(self)`**
  Returns the anticodon sequence of the tRNA.

- **`get_amino_acid(self)`**
  Returns the amino acid carried by the tRNA.

---

### Binding and Matching
- **`matches_codon(self, codon)`**
  Checks if the tRNA anticodon matches the given codon, considering wobble base pairing.

- **`bind_to_mrna(self, mrna_sequence, start_index)`**
  Simulates the binding of the tRNA to an mRNA sequence at a specific start index.

---

### Serialization and Deserialization
- **`to_dict(self)`**
  Converts the `tRNA` object to a dictionary.

- **`from_dict(cls, data)`**
  Creates a `tRNA` object from a dictionary.

- **`to_json(self)`**
  Converts the `tRNA` object to a JSON string.

- **`from_json(cls, json_str)`**
  Creates a `tRNA` object from a JSON string.

---

### String Representation
- **`__str__(self)`**
  Returns a string representation of the `tRNA` object.

---

## Example Usage

```python
# Create a tRNA object
trna = tRNA(sequence="GGCUCGAAUCAGCUCA", anticodon="CAG", amino_acid="Valine")

# Print tRNA information
print(trna)

# Check if the tRNA matches a codon
codon = "GUC"
print(f"Does the tRNA match the codon {codon}? {trna.matches_codon(codon)}")

# Simulate binding to an mRNA sequence
mrna_sequence = "AUGGUCAGUCGAAUCAGCUCA"
start_index = 3
trna.bind_to_mrna(mrna_sequence, start_index)

# Convert tRNA to a dictionary and JSON
trna_dict = trna.to_dict()
trna_json = trna.to_json()
print(trna_dict)
print(trna_json)

# Create a new tRNA object from a dictionary
new_trna = tRNA.from_dict(trna_dict)
print(new_trna)
```

---

## Notes
- The `tRNA` class inherits from the `RNA` class, allowing it to utilize all the methods and attributes of the `RNA` class.
- The `matches_codon` method considers wobble base pairing rules for the third base of the codon.
- The `bind_to_mrna` method simulates the binding process of tRNA to mRNA during translation.
- Serialization and deserialization methods (`to_dict`, `from_dict`, `to_json`, `from_json`) facilitate easy storage and retrieval of tRNA data.# tRNA Class

## Overview
The `tRNA` class represents a transfer RNA molecule, inheriting from the `RNA` class. It includes functionality for managing anticodons, amino acids, and binding to mRNA sequences, as well as serialization and deserialization methods.

---

## Class Definition

```python
class tRNA(RNA):
    def __init__(self, sequence, anticodon, amino_acid):
        """
        Initialize a new tRNA object.
        :param sequence: The nucleotide sequence of the tRNA strand
        :param anticodon: The anticodon sequence of the tRNA
        :param amino_acid: The amino acid carried by the tRNA
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sequence` | `str` | Nucleotide sequence of the tRNA. |
| `anticodon` | `str` | Anticodon sequence of the tRNA. |
| `amino_acid` | `str` | Amino acid carried by the tRNA. |

---

## Methods

### Initialization
- **`__init__(self, sequence, anticodon, amino_acid)`**
  Initializes a new `tRNA` instance with the specified sequence, anticodon, and amino acid.

---

### Anticodon and Amino Acid Management
- **`get_anticodon(self)`**
  Returns the anticodon sequence of the tRNA.

- **`get_amino_acid(self)`**
  Returns the amino acid carried by the tRNA.

---

### Binding and Matching
- **`matches_codon(self, codon)`**
  Checks if the tRNA anticodon matches the given codon, considering wobble base pairing.

- **`bind_to_mrna(self, mrna_sequence, start_index)`**
  Simulates the binding of the tRNA to an mRNA sequence at a specific start index.

---

### Serialization and Deserialization
- **`to_dict(self)`**
  Converts the `tRNA` object to a dictionary.

- **`from_dict(cls, data)`**
  Creates a `tRNA` object from a dictionary.

- **`to_json(self)`**
  Converts the `tRNA` object to a JSON string.

- **`from_json(cls, json_str)`**
  Creates a `tRNA` object from a JSON string.

---

### String Representation
- **`__str__(self)`**
  Returns a string representation of the `tRNA` object.

---

## Example Usage

```python
# Create a tRNA object
trna = tRNA(sequence="GGCUCGAAUCAGCUCA", anticodon="CAG", amino_acid="Valine")

# Print tRNA information
print(trna)

# Check if the tRNA matches a codon
codon = "GUC"
print(f"Does the tRNA match the codon {codon}? {trna.matches_codon(codon)}")

# Simulate binding to an mRNA sequence
mrna_sequence = "AUGGUCAGUCGAAUCAGCUCA"
start_index = 3
trna.bind_to_mrna(mrna_sequence, start_index)

# Convert tRNA to a dictionary and JSON
trna_dict = trna.to_dict()
trna_json = trna.to_json()
print(trna_dict)
print(trna_json)

# Create a new tRNA object from a dictionary
new_trna = tRNA.from_dict(trna_dict)
print(new_trna)
```

---

## Notes
- The `tRNA` class inherits from the `RNA` class, allowing it to utilize all the methods and attributes of the `RNA` class.
- The `matches_codon` method considers wobble base pairing rules for the third base of the codon.
- The `bind_to_mrna` method simulates the binding process of tRNA to mRNA during translation.
- Serialization and deserialization methods (`to_dict`, `from_dict`, `to_json`, `from_json`) facilitate easy storage and retrieval of tRNA data.
