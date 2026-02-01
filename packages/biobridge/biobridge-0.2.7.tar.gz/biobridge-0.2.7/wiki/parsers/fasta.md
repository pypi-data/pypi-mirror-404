# FastaParser Class

---

## Overview
The `FastaParser` class is designed to parse FASTA files containing biological sequences (DNA, RNA, or Protein) and convert them into corresponding Python objects (`DNA`, `RNA`, or `Protein`). It uses the `Biopython` library to read and process FASTA files.

---

## Class Definition

```python
class FastaParser:
    def __init__(self, file_path):
        """
        Initialize a new FastaParser object.
        :param file_path: Path to the FASTA file containing biological sequence data
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the FASTA file. |
| `records` | `List[Bio.SeqRecord.SeqRecord]` | List of sequence records parsed from the FASTA file. |

---

## Methods

### Initialization
- **`__init__(self, file_path)`**
  Initializes a new `FastaParser` instance with the specified FASTA file path. The FASTA file is parsed into a list of `SeqRecord` objects.

---

### Parsing Records
- **`parse_records(self) -> List[Union[DNA, RNA, Protein]]`**
  Parses the FASTA records and converts each record into the appropriate biological object (`DNA`, `RNA`, or `Protein`).

  - **Returns**: A list of parsed biological objects (`DNA`, `RNA`, or `Protein`).

  - **Details**:
    - Iterates over each `SeqRecord` in the FASTA file.
    - Determines the type of sequence (`DNA`, `RNA`, or `Protein`) based on the sequence characters.
    - Creates the corresponding object and appends it to the result list.

---

### Element Creation
- **`create_element(self, identifier, sequence) -> Union[DNA, RNA, Protein]`**
  Creates a biological object (`DNA`, `RNA`, or `Protein`) based on the sequence type.

  - **Parameters**:
    - `identifier`: Unique identifier for the sequence.
    - `sequence`: Biological sequence string.

  - **Returns**: A `DNA`, `RNA`, or `Protein` object.

  - **Details**:
    - If the sequence contains only `A`, `C`, `G`, `T`, it is identified as `DNA`.
    - If the sequence contains only `A`, `C`, `G`, `U`, it is identified as `RNA`.
    - Otherwise, it is identified as a `Protein`.

---

### Metadata Retrieval
- **`get_metadata(self) -> List[Dict[str, str]]`**
  Retrieves metadata (identifier and description) for each sequence record in the FASTA file.

  - **Returns**: A list of dictionaries containing metadata for each sequence record.

---

## Example Usage

### FASTA File Example (`sequences.fasta`)
```
>seq1
ATGCGATCG
>seq2
AUGCCGUA
>seq3
ACDEFGHIKLMNPQRSTVWY
```

### Python Code Example
```python
# Initialize the FastaParser with the path to the FASTA file
parser = FastaParser(file_path="sequences.fasta")

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
DNA Sequence: ATGCGATCG
RNA Sequence: AUGCCGUA
Protein: seq3, Sequence: ACDEFGHIKLMNPQRSTVWY

{'id': 'seq1', 'description': ''}
{'id': 'seq2', 'description': ''}
{'id': 'seq3', 'description': ''}
```

---

## Dependencies
- **`Biopython`**: Used for reading and processing FASTA files.
- **`DNA`**: Class representing DNA sequences.
- **`RNA`**: Class representing RNA sequences.
- **`Protein`**: Class representing protein sequences.

---

## Error Handling
- If the FASTA file does not exist or cannot be read, `SeqIO.parse` will raise an error.
- If the sequence type cannot be determined, it defaults to creating a `Protein` object.

---

## Notes
- The `FastaParser` class is designed to handle FASTA files containing DNA, RNA, or Protein sequences.
- The `create_element` method uses the presence of specific nucleotides to determine the sequence type.
- The `get_metadata` method retrieves the identifier and description for each sequence record.
