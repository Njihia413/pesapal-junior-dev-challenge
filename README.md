# PesapalDB - A Simple RDBMS Implementation

A custom relational database management system built from scratch for the **Pesapal Junior Developer Challenge 2026**.

## Features

### Core RDBMS Engine

- **SQL Parser**: Full lexer and recursive descent parser supporting SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE
- **Query Executor**: Handles JOINs, WHERE conditions, ORDER BY, LIMIT, GROUP BY, aggregates
- **Data Types**: INTEGER, FLOAT, VARCHAR, BOOLEAN, DATE, TIMESTAMP
- **Constraints**: PRIMARY KEY, UNIQUE, NOT NULL, FOREIGN KEY references
- **B-Tree Indexing**: Efficient lookups with automatic primary key indexing
- **File-Based Storage**: JSON persistence with schema management

### REST API

- FastAPI-powered REST endpoints
- CRUD operations for all tables
- Raw SQL query execution
- CORS enabled for frontend integration

### Frontend Demo App

- Next.js 15 with TypeScript
- shadcn/ui components with dark glassmorphism theme
- Responsive mobile navigation
- Pages: Dashboard, Products, Categories, Suppliers, SQL Console

---

## Project Structure

```
pesapal-junior-dev-challenge/
├── backend/
│   ├── rdbms/
│   │   ├── __init__.py          # Package init
│   │   ├── types.py             # Data types & validation
│   │   ├── schema.py            # Column, Table, Schema classes
│   │   ├── constraints.py       # PK, Unique, NotNull, FK
│   │   ├── storage.py           # JSON file persistence
│   │   ├── indexing.py          # B-tree index implementation
│   │   ├── engine.py            # Main Database class
│   │   ├── repl.py              # Interactive REPL
│   │   ├── parser/
│   │   │   ├── lexer.py         # SQL tokenizer
│   │   │   ├── ast.py           # AST node definitions
│   │   │   └── parser.py        # Recursive descent parser
│   │   └── executor/
│   │       └── executor.py      # Query execution
│   ├── api/
│   │   ├── main.py              # FastAPI endpoints
│   │   └── models.py            # Pydantic models
│   └── requirements.txt
└── frontend/
    ├── app/
    │   ├── page.tsx             # Dashboard
    │   ├── products/page.tsx    # Products CRUD
    │   ├── categories/page.tsx  # Categories CRUD
    │   ├── suppliers/page.tsx   # Suppliers CRUD
    │   └── sql-console/page.tsx # SQL Console
    ├── components/
    │   ├── Sidebar.tsx          # Desktop navigation
    │   └── MobileNav.tsx        # Mobile navigation
    └── lib/
        └── api.ts               # API client
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the interactive REPL
python -m rdbms.repl

# Or start the API server
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

---

## Usage

### Interactive REPL

```sql
sql> CREATE TABLE products (
...>   id INTEGER PRIMARY KEY AUTO_INCREMENT,
...>   name VARCHAR(100) NOT NULL,
...>   price FLOAT
...> );
✓ Table 'products' created

sql> INSERT INTO products (name, price) VALUES ('Widget', 29.99);
✓ Inserted 1 row(s)

sql> SELECT * FROM products;
  id  name     price
----  ------  ------
   1  Widget   29.99

1 row(s) returned

sql> .tables
Tables:
  products (1 rows)

sql> .exit
Goodbye!
```

### API Endpoints

| Method | Endpoint                   | Description         |
| ------ | -------------------------- | ------------------- |
| GET    | `/health`                  | Health check        |
| GET    | `/stats`                   | Database statistics |
| POST   | `/query`                   | Execute SQL query   |
| GET    | `/tables`                  | List all tables     |
| GET    | `/tables/{name}`           | Get table info      |
| GET    | `/tables/{name}/rows`      | Get table rows      |
| POST   | `/tables/{name}/rows`      | Insert row          |
| PUT    | `/tables/{name}/rows/{id}` | Update row          |
| DELETE | `/tables/{name}/rows/{id}` | Delete row          |

---

## Supported SQL

### DDL (Data Definition Language)

```sql
CREATE TABLE table_name (
  column_name TYPE [constraints],
  ...
);

DROP TABLE table_name;

CREATE INDEX index_name ON table_name (column_name);
```

### DML (Data Manipulation Language)

```sql
INSERT INTO table_name (col1, col2) VALUES (val1, val2);

UPDATE table_name SET col1 = val1 WHERE condition;

DELETE FROM table_name WHERE condition;

SELECT columns FROM table
  [JOIN other_table ON condition]
  [WHERE condition]
  [GROUP BY columns [HAVING condition]]
  [ORDER BY column [ASC|DESC]]
  [LIMIT n [OFFSET m]];
```

---

## Tech Stack

**Backend:**

- Python 3.9+
- FastAPI
- Pydantic
- Custom SQL Parser
- B-Tree Index

**Frontend:**

- Next.js 15
- TypeScript
- Tailwind CSS 4
- shadcn/ui
- Lucide Icons

---

## Author

Built for the Pesapal Junior Developer Challenge 2026.
