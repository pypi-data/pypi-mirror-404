# SwissProtParser Class

---

## Overview
The `SwissProtParser` class is designed to parse Swiss-Prot or UniProt XML files containing protein sequences and annotations. It extracts protein sequences and their metadata, converting them into `Protein` objects. The class uses the `Biopython` library to read and process these files.

---

## Class Definition

```python
class SwissProtParser:
    def __init__(self, file_path):
        """
        Initialize a new SwissProtParser object.
        :param file_path: Path to the Swiss-Prot or UniProt XML file containing protein data
        """
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the Swiss-Prot or UniProt XML file. |
| `records` | `List[Bio.SeqRecord.SeqRecord]` | List of sequence records parsed from the file. |

---

## Methods

### Initialization
- **`__init__(self, file_path)`**
  Initializes a new `SwissProtParser` instance with the specified file path. It attempts to parse the file as Swiss-Prot format first, and if that fails, it tries to parse it as UniProt XML format.

---

### Parsing Records
- **`parse_records(self) -> List[Protein]`**
  Parses the records and converts each record into a `Protein` object.

  - **Returns**: A list of `Protein` objects.

  - **Details**:
    - Iterates over each `SeqRecord` in the file.
    - Creates a `Protein` object for each record and appends it to the result list.

---

### Element Creation
- **`create_protein(self, record) -> Protein`**
  Creates a `Protein` object from a sequence record.

  - **Parameters**:
    - `record`: The sequence record from the Swiss-Prot or UniProt XML file.

  - **Returns**: A `Protein` object.

  - **Details**:
    - Extracts the protein's ID, name, description, organism, gene name, and function from the record.
    - Adds features such as domains and binding sites to the `Protein` object.

---

### Metadata Retrieval
- **`get_metadata(self) -> List[Dict[str, Any]]`**
  Retrieves metadata (identifier, name, description, and annotations) for each sequence record in the file.

  - **Returns**: A list of dictionaries containing metadata for each sequence record.

---

## Example Usage

### Swiss-Prot File Example (`proteins.dat`)
```
ID   PROTEIN1_STANDARD            Reviewed;         123 AA.
AC   P12345;
DT   01-JAN-1980, integrated into UniProtKB/Swiss-Prot.
DT   01-JAN-1980, sequence version 1.
DE   Example protein 1 (Example).
GN   Name=EX1; Synonyms=EXP1;
OS   Synthetic organism.
OC   Synthetic.
OX   NCBI_TaxID=123456;
RN   [1]
RP   NUCLEOTIDE SEQUENCE.
RC   TISSUE=Liver;
RX   PubMed=123456789;
RA   Author;
RT   "Example protein.";
RL   J. Biol. Chem. 123:456-4567(1980).
CC   -!- FUNCTION: Example function.
CC   -!- SUBCELLULAR LOCATION: Cytoplasm.
DR   EMBL; EXAMPLE1; EXAMPLE1.1; -.
DR   PIR; EXAMPLE1; EXAMPLE1.
DR   RefSeq; NP_123456.1; NC_123456.1.
DR   UniProtKB/Swiss-Prot; P12345; -.
KW   Example.
FT   CHAIN           1..123
FT                   /note="Example protein 1"
FT                   /id="PRO_123456"
FT   DOMAIN          10..50
FT                   /note="Example domain"
FT   BINDING         20..25
FT                   /note="Example binding site"
SQ   SEQUENCE   123 AA;  12345 MW;  ABCDEF12345 CRC64;
     MAGICSEQUENCE
//
```

### UniProt XML File Example (`proteins.xml`)
```xml
<uniprot xmlns="http://uniprot.org/uniprot" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <entry dataset="Swiss-Prot">
    <accession>P12345</accession>
    <name>PROTEIN1_HUMAN</name>
    <protein>
      <recommendedName>
        <fullName>Example protein 1</fullName>
      </recommendedName>
    </protein>
    <gene>
      <name type="primary">EX1</name>
    </gene>
    <organism>
      <name type="scientific">Homo sapiens</name>
    </organism>
    <sequence>MAGICSEQUENCE</sequence>
    <comment type="function">
      <text>Example function.</text>
    </comment>
    <feature type="domain">
      <location>
        <begin position="10"/>
        <end position="50"/>
      </location>
    </feature>
  </entry>
</uniprot>
```

### Python Code Example
```python
# Initialize the SwissProtParser with the path to the Swiss-Prot or UniProt XML file
parser = SwissProtParser(file_path="proteins.dat")

# Parse the records
proteins = parser.parse_records()

# Print the parsed proteins
for protein in proteins:
    print(protein)

# Retrieve metadata
metadata = parser.get_metadata()
for meta in metadata:
    print(meta)
```

### Expected Output
```
Protein: Example protein 1, Sequence: MAGICSEQUENCE
{'id': 'P12345', 'name': 'PROTEIN1_HUMAN', 'description': 'RecName: Full=Example protein 1;', 'annotations': {...}}
```

---

## Dependencies
- **`Biopython`**: Used for reading and processing Swiss-Prot and UniProt XML files.
- **`Protein`**: Class representing protein sequences.

---

## Error Handling
- If the file does not exist or cannot be read, `SeqIO.parse` will raise an error.
- If the file is neither in Swiss-Prot nor UniProt XML format, a `ValueError` will be raised.

---

## Notes
- The `SwissProtParser` class is designed to handle both Swiss-Prot and UniProt XML files.
- The `create_protein` method extracts comprehensive metadata and features from the records.
- The `get_metadata` method retrieves metadata such as identifier, name, description, and annotations for each sequence record.
