# DNALite API Documentation

---

## Overview
The **DNALite API** is a Flask-based web service for storing, retrieving, listing, and deleting biological data (e.g., DNA, RNA, Protein sequences) using an `SQLDNAEncoder`. It provides RESTful endpoints for managing data in a structured manner.

---

## Endpoints

### **1. Store Data**
- **Endpoint**: `/store`
- **Method**: `POST`
- **Description**: Stores biological data in the database.
- **Request Body**:
  ```json
  {
    "data_name": "string",
    "data": "object"
  }
  ```
- **Responses**:
  - **Success (201 Created)**:
    ```json
    {
      "message": "Data stored successfully"
    }
    ```
  - **Error (400 Bad Request)**:
    ```json
    {
      "error": "Missing required fields: data_name and data"
    }
    ```
  - **Error (500 Internal Server Error)**:
    ```json
    {
      "error": "Error message"
    }
    ```

---

### **2. Retrieve Data**
- **Endpoint**: `/retrieve/<data_name>`
- **Method**: `GET`
- **Description**: Retrieves stored biological data by its name.
- **Path Parameter**:
  - `data_name`: Name of the data to retrieve.
- **Responses**:
  - **Success (200 OK)**:
    ```json
    {
      "data": "object"
    }
    ```
  - **Error (404 Not Found)**:
    ```json
    {
      "message": "Data not found"
    }
    ```
  - **Error (500 Internal Server Error)**:
    ```json
    {
      "error": "Error message"
    }
    ```

---

### **3. List Stored Data**
- **Endpoint**: `/list`
- **Method**: `GET`
- **Description**: Lists all stored data names.
- **Responses**:
  - **Success (200 OK)**:
    ```json
    [
      "data_name_1",
      "data_name_2",
      ...
    ]
    ```
  - **Error (500 Internal Server Error)**:
    ```json
    {
      "error": "Error message"
    }
    ```

---

### **4. Delete Data**
- **Endpoint**: `/delete/<data_name>`
- **Method**: `DELETE`
- **Description**: Deletes stored biological data by its name.
- **Path Parameter**:
  - `data_name`: Name of the data to delete.
- **Responses**:
  - **Success (200 OK)**:
    ```json
    {
      "message": "Data deleted successfully"
    }
    ```
  - **Error (500 Internal Server Error)**:
    ```json
    {
      "error": "Error message"
    }
    ```

---

### **5. Copy Database**
- **Endpoint**: `/copy`
- **Method**: `POST`
- **Description**: Copies the current database to a new database.
- **Request Body**:
  ```json
  {
    "db_name": "string"
  }
  ```
- **Responses**:
  - **Success (200 OK)**:
    ```json
    {
      "message": "Database copied to {db_name}"
    }
    ```
  - **Error (400 Bad Request)**:
    ```json
    {
      "error": "Missing required field: db_name"
    }
    ```
  - **Error (500 Internal Server Error)**:
    ```json
    {
      "error": "Error message"
    }
    ```

---

## Example Usage

### **1. Initialize the Flask App**
```python
from dnalite_api import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```

### **2. Store Data**
```bash
curl -X POST http://localhost:5000/store \
  -H "Content-Type: application/json" \
  -d '{"data_name": "example_dna", "data": {"sequence": "ATGC"}}'
```

### **3. Retrieve Data**
```bash
curl -X GET http://localhost:5000/retrieve/example_dna
```

### **4. List Stored Data**
```bash
curl -X GET http://localhost:5000/list
```

### **5. Delete Data**
```bash
curl -X DELETE http://localhost:5000/delete/example_dna
```

### **6. Copy Database**
```bash
curl -X POST http://localhost:5000/copy \
  -H "Content-Type: application/json" \
  -d '{"db_name": "new_database"}'
```

---

## Dependencies
- **Flask**: Web framework for building the API.
- **SQLDNAEncoder**: Custom class for encoding and managing biological data in a database.

---

## Error Handling
- **400 Bad Request**: Missing required fields in the request.
- **404 Not Found**: Data not found in the database.
- **500 Internal Server Error**: Unexpected errors during data operations.

---

## Notes
- The API is designed to be extensible for additional biological data types and operations.
- Ensure the `SQLDNAEncoder` is properly initialized with a database connection.
