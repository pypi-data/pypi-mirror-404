# CSVParser Class

---

## **Overview**
The `CSVParser` class is designed to parse CSV files containing biological sequence data (DNA, RNA, or Protein) and convert them into corresponding Python objects (`DNA`, `RNA`, or `Protein`). It leverages the `pandas` library to read and process CSV files, making it easy to handle large datasets efficiently.

---

## **Class Definition**

```python
class CSVParser:
    def __init__(self, file_path):
        """
        Initialize a new CSVParser object.
        :param file_path: Path to the CSV file containing biological sequence data
        """
        ...
```

---

## **Attributes**

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the CSV file. |
| `data` | `pandas.DataFrame` | DataFrame containing the parsed CSV data. |

---

## **Methods**

### **Initialization**
- **`__init__(self, file_path)`**
  Initializes a new `CSVParser` instance with the specified CSV file path. The CSV file is read into a `pandas.DataFrame` for further processing.

---

### **Parsing Records**
- **`parse_records(self) -> List[Union[DNA, RNA, Protein]]`**
  Parses the CSV data and converts each row into the appropriate biological object (`DNA`, `RNA`, or `Protein`).

  - **Returns**: A list of parsed biological objects (`DNA`, `RNA`, or `Protein`).

  - **Details**:
    - Iterates over each row in the CSV file.
    - Determines the type of sequence (`DNA`, `RNA`, or `Protein`) based on the `type` column.
    - Creates the corresponding object and appends it to the result list.

---

## **CSV File Format**
The CSV file should have the following columns:

| Column Name | Description |
|-------------|-------------|
| `sequence`  | The biological sequence (e.g., "ATGC" for DNA, "AUG" for RNA, "ACDEF" for Protein). |
| `type`      | The type of sequence (`DNA`, `RNA`, or `Protein`). |
| `id`        | (Optional) Unique identifier for the sequence (required for `Protein` objects). |

---

## **Example Usage**

### **CSV File Example (`sequences.csv`)**
```csv
sequence,type,id
ATGCGATCG,DNA,
AUGCCGUA,RNA,
ACDEFGHIKLMNPQRSTVWY,Protein,Protein1
```

### **Python Code Example**
```python
# Initialize the CSVParser with the path to the CSV file
parser = CSVParser(file_path="sequences.csv")

# Parse the records
parsed_elements = parser.parse_records()

# Print the parsed elements
for element in parsed_elements:
    print(element)
```

### **Expected Output**
```
DNA Sequence: ATGCGATCG
RNA Sequence: AUGCCGUA
Protein: Protein1, Sequence: ACDEFGHIKLMNPQRSTVWY
```

---

## **Dependencies**
- **`pandas`**: Used for reading and processing CSV files.
- **`DNA`**: Class representing DNA sequences.
- **`RNA`**: Class representing RNA sequences.
- **`Protein`**: Class representing protein sequences.

---

## **Error Handling**
- If the CSV file does not contain the required columns (`sequence`, `type`), the `CSVParser` will raise a `KeyError`.
- If the `type` column contains an invalid value (not `DNA`, `RNA`, or `Protein`), the corresponding row will be skipped.

---

## **Notes**
- The `CSVParser` class is designed to be flexible and can be extended to support additional biological sequence types or custom parsing logic.
- The `id` column is optional and only required for `Protein` objects. If not provided, the `Protein` constructor should handle it appropriately.

---
