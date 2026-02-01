# GenbankParser Class

---

## Overview
The `GenbankParser` class is designed to parse GenBank files containing biological sequences and annotations. It extracts DNA, RNA, and Protein sequences from the GenBank records and converts them into corresponding Python objects (`DNA`, `RNA`, or `Protein`). It uses the `Biopython` library to read and process GenBank files.

---

## Class Definition

```python
class GenbankParser:
    def __init__(self, file_path):
        """
        Initialize a new GenbankParser object.
        :param file_path: Path to the GenBank file containing biological sequence data
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the GenBank file. |
| `records` | `List[Bio.SeqRecord.SeqRecord]` | List of sequence records parsed from the GenBank file. |

---

## Methods

### Initialization
- **`__init__(self, file_path)`**
  Initializes a new `GenbankParser` instance with the specified GenBank file path. The GenBank file is parsed into a list of `SeqRecord` objects.

---

### Parsing Records
- **`parse_records(self) -> List[Union[DNA, RNA, Protein]]`**
  Parses the GenBank records and converts each record into the appropriate biological objects (`DNA`, `RNA`, or `Protein`).

  - **Returns**: A list of parsed biological objects (`DNA`, `RNA`, or `Protein`).

  - **Details**:
    - Iterates over each `SeqRecord` in the GenBank file.
    - For each Coding Sequence (CDS) feature, it extracts the protein sequence, DNA sequence, and RNA sequence.
    - Creates the corresponding objects and appends them to the result list.
    - If no features are present, it creates a `DNA` object for the entire sequence.

---

### Element Creation
- **`create_protein(self, feature, protein_seq) -> Protein`**
  Creates a `Protein` object from a CDS feature and its translated protein sequence.

  - **Parameters**:
    - `feature`: The CDS feature from the GenBank record.
    - `protein_seq`: The translated protein sequence.

  - **Returns**: A `Protein` object.

  - **Details**:
    - Extracts the protein name and ID from the feature qualifiers.
    - Creates a `Protein` object with the extracted information.

---

- **`create_dna(self, feature, full_sequence) -> DNA`**
  Creates a `DNA` object from a CDS feature and the full sequence.

  - **Parameters**:
    - `feature`: The CDS feature from the GenBank record.
    - `full_sequence`: The full DNA sequence from the record.

  - **Returns**: A `DNA` object.

  - **Details**:
    - Extracts the DNA sequence corresponding to the feature location.
    - Adds the gene name to the `DNA` object.

---

- **`create_rna(self, feature, full_sequence) -> RNA`**
  Creates an `RNA` object from a CDS feature and the full sequence.

  - **Parameters**:
    - `feature`: The CDS feature from the GenBank record.
    - `full_sequence`: The full DNA sequence from the record.

  - **Returns**: An `RNA` object.

  - **Details**:
    - Extracts the RNA sequence corresponding to the feature location.
    - Converts `T` to `U` for RNA sequences.

---

### Metadata Retrieval
- **`get_metadata(self) -> List[Dict[str, Any]]`**
  Retrieves metadata (identifier, name, description, and annotations) for each sequence record in the GenBank file.

  - **Returns**: A list of dictionaries containing metadata for each sequence record.

---

## Example Usage

### GenBank File Example (`sequences.gb`)
```
LOCUS       Example               100 bp    DNA     linear   UNK 01-JAN-1980
DEFINITION  Example GenBank record.
ACCESSION   EXAMPLE1
VERSION     EXAMPLE1.1
SOURCE      Synthetic sequence
  ORGANISM  Synthetic organism
            Other: Synthetic
FEATURES             Location/Qualifiers
     source          1..100
                     /organism="Synthetic organism"
     CDS             10..90
                     /gene="example_gene"
                     /product="Example Protein"
                     /protein_id="EXP1"
                     /translation="MAGIC"
ORIGIN
        1 atgcgatcga tgcgatcgat cgatcgatcg atgcgatcga tgcgatcgat cgatcgatcg
//
```

### Python Code Example
```python
# Initialize the GenbankParser with the path to the GenBank file
parser = GenbankParser(file_path="sequences.gb")

# Parse the records
parsed_elements = parser.parse_records()

# Print the parsed elements
for element in parsed_elements:
    print(element)

# Retrieve metadata
metadata = parser.get_metadata()
for meta in metadata:
    print(meta)
```

### Expected Output
```
Protein: Example Protein, Sequence: MAGIC
DNA Sequence: ATGCGATCGA
RNA Sequence: AUGGCGAUCG

{'id': 'EXAMPLE1', 'name': 'Example', 'description': 'Example GenBank record.', 'annotations': {...}}
```

---

## Dependencies
- **`Biopython`**: Used for reading and processing GenBank files.
- **`DNA`**: Class representing DNA sequences.
- **`RNA`**: Class representing RNA sequences.
- **`Protein`**: Class representing protein sequences.

---

## Error Handling
- If the GenBank file does not exist or cannot be read, `SeqIO.parse` will raise an error.
- If a CDS feature does not have a translation qualifier, it will be skipped.

---

## Notes
- The `GenbankParser` class is designed to handle GenBank files containing annotated sequences.
- The `parse_records` method processes each CDS feature to extract DNA, RNA, and Protein sequences.
- The `get_metadata` method retrieves metadata such as identifier, name, description, and annotations for each sequence record.
