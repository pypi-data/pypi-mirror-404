# Gene Class

## Overview
The `Gene` class represents a gene within a DNA sequence, including its name, start and end positions, and inheritance pattern. It provides methods for serialization, deserialization, and string representation.

---

## Class Definition

```python
class Gene:
    def __init__(self, name, start, end, inheritance='mixed'):
        """
        Initialize a new Gene object.
        :param name: Name of the gene
        :param start: Start position of the gene in the DNA sequence
        :param end: End position of the gene in the DNA sequence
        :param inheritance: Inheritance pattern of the gene (default: 'mixed')
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the gene. |
| `start` | `int` | Start position of the gene in the DNA sequence. |
| `end` | `int` | End position of the gene in the DNA sequence. |
| `inheritance` | `str` | Inheritance pattern of the gene (recessive, dominant, mixed). |

---

## Methods

### Initialization
- **`__init__(self, name, start, end, inheritance='mixed')`**
  Initializes a new `Gene` instance with the specified name, start position, end position, and inheritance pattern.

---

### Inheritance Management
- **`set_inheritance(self, inheritance)`**
  Sets the inheritance pattern of the gene. Valid patterns are 'recessive', 'dominant', and 'mixed'.

---

### Serialization and Deserialization
- **`to_dict(self)`**
  Converts the `Gene` object to a dictionary.

- **`from_dict(self, gene_dict)`**
  Populates the `Gene` object from a dictionary.

---

### String Representation
- **`__str__(self)`**
  Returns a human-readable string representation of the `Gene` object.

- **`__repr__(self)`**
  Returns a formal string representation of the `Gene` object, used for debugging.

---

## Example Usage

```python
# Create a Gene object
gene = Gene(name="BRCA1", start=100, end=500, inheritance="dominant")

# Print the gene information
print(gene)

# Convert the gene to a dictionary
gene_dict = gene.to_dict()
print(gene_dict)

# Create a new Gene object from a dictionary
new_gene = Gene(name="", start=0, end=0)
new_gene.from_dict(gene_dict)
print(new_gene)
```

---

## Notes
- The `Gene` class is designed to be used as part of a larger genetic simulation or analysis system.
- The `inheritance` attribute must be one of the valid values: 'recessive', 'dominant', or 'mixed'.
- The `to_dict` and `from_dict` methods facilitate serialization and deserialization, making it easy to save and load gene data.
