# EnsemblParser Class

---

## Overview
The `EnsemblParser` class is designed to parse EMBL (European Molecular Biology Laboratory) files containing biological sequences and annotations. It extracts DNA, RNA, and Protein sequences from the EMBL records and converts them into corresponding Python objects (`DNA`, `RNA`, or `Protein`). It uses the `Biopython` library to read and process EMBL files.

---

## Class Definition

```python
class EnsemblParser:
    def __init__(self, file_path):
        """
        Initialize a new EnsemblParser object.
        :param file_path: Path to the EMBL file containing biological sequence data
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the EMBL file. |
| `records` | `List[Bio.SeqRecord.SeqRecord]` | List of sequence records parsed from the EMBL file. |

---

## Methods

### Initialization
- **`__init__(self, file_path)`**
  Initializes a new `EnsemblParser` instance with the specified EMBL file path. The EMBL file is parsed into a list of `SeqRecord` objects.

---

### Parsing Records
- **`parse_records(self) -> List[Union[DNA, RNA, Protein]]`**
  Parses the EMBL records and converts each record into the appropriate biological objects (`DNA`, `RNA`, or `Protein`).

  - **Returns**: A list of parsed biological objects (`DNA`, `RNA`, or `Protein`).

  - **Details**:
    - Iterates over each `SeqRecord` in the EMBL file.
    - For each Coding Sequence (CDS) feature, it extracts the protein sequence, DNA sequence, and RNA sequence.
    - Creates the corresponding objects and appends them to the result list.

---

### Element Creation
- **`create_protein(self, feature, protein_seq) -> Protein`**
  Creates a `Protein` object from a CDS feature and its translated protein sequence.

  - **Parameters**:
    - `feature`: The CDS feature from the EMBL record.
    - `protein_seq`: The translated protein sequence.

  - **Returns**: A `Protein` object.

  - **Details**:
    - Extracts the protein ID and name from the feature qualifiers.
    - Adds additional information such as product and notes if available.

---

- **`create_dna(self, feature, full_sequence) -> DNA`**
  Creates a `DNA` object from a CDS feature and the full sequence.

  - **Parameters**:
    - `feature`: The CDS feature from the EMBL record.
    - `full_sequence`: The full DNA sequence from the record.

  - **Returns**: A `DNA` object.

  - **Details**:
    - Extracts the DNA sequence corresponding to the feature location.
    - Adds the gene name to the `DNA` object.

---

- **`create_rna(self, feature, full_sequence) -> RNA`**
  Creates an `RNA` object from a CDS feature and the full sequence.

  - **Parameters**:
    - `feature`: The CDS feature from the EMBL record.
    - `full_sequence`: The full DNA sequence from the record.

  - **Returns**: An `RNA` object.

  - **Details**:
    - Extracts the RNA sequence corresponding to the feature location.
    - Converts `T` to `U` for RNA sequences.
    - Adds the gene name to the `RNA` object.

---

### Metadata Retrieval
- **`get_metadata(self) -> List[Dict[str, Any]]`**
  Retrieves metadata (identifier, name, description, and annotations) for each sequence record in the EMBL file.

  - **Returns**: A list of dictionaries containing metadata for each sequence record.

---

## Example Usage

### EMBL File Example (`sequences.embl`)
```
ID   EXAMPLE1 standard; genomic; DNA; UNK; 100 BP.
XX
AC   EXAMPLE1;
XX
DE   Example EMBL record.
XX
SV   EXAMPLE1.1
XX
KW   .
XX
OS   Synthetic organism
XX
RN   [1]
XX
RA   Author;
RT   ;
RL   Unpublished.
XX
RN   [2]
XX
RA   Author2;
RT   ;
RL   Unpublished.
XX
DR   MD5; 123456789abcdef123456789abcdef12.
XX
CC   Example record.
XX
FH   Key             Location/Qualifiers
FH
FT   source          1..100
FT                   /organism="Synthetic organism"
FT   CDS             10..90
FT                   /gene="example_gene"
FT                   /protein_id="EXP1"
FT                   /product="Example Protein"
FT                   /translation="MAGIC"
XX
SQ   Sequence 100 BP; 25 A; 25 C; 25 G; 25 T; 0 other;
     atgcgatcga tgcgatcgat cgatcgatcg atgcgatcga tgcgatcgat cgatcgatcg
//
```

### Python Code Example
```python
# Initialize the EnsemblParser with the path to the EMBL file
parser = EnsemblParser(file_path="sequences.embl")

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

{'id': 'EXAMPLE1', 'name': 'EXAMPLE1', 'description': 'Example EMBL record.', 'annotations': {...}}
```

---

## Dependencies
- **`Biopython`**: Used for reading and processing EMBL files.
- **`DNA`**: Class representing DNA sequences.
- **`RNA`**: Class representing RNA sequences.
- **`Protein`**: Class representing protein sequences.

---

## Error Handling
- If the EMBL file does not exist or cannot be read, `SeqIO.parse` will raise an error.
- If a CDS feature does not have a translation qualifier, it will be skipped.

---

## Notes
- The `EnsemblParser` class is designed to handle EMBL files containing annotated sequences.
- The `parse_records` method processes each CDS feature to extract DNA, RNA, and Protein sequences.
- The `get_metadata` method retrieves metadata such as identifier, name, description, and annotations for each sequence record.
