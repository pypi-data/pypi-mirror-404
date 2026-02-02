# dbgear-doc

Documentation generator plugin for [DBGear](https://github.com/tamuto/dbgear).

## Overview

dbgear-doc generates Markdown documentation from DBGear database schema definitions. It provides:

- Automatic documentation generation from `schema.yaml` files
- Table structure documentation with columns, types, and descriptions
- Index and foreign key relationship documentation
- Schema-level overview pages

## Installation

```bash
pip install dbgear-doc
```

Or with Poetry:

```bash
poetry add dbgear-doc
```

## Usage

Once installed, the `doc` subcommand becomes available in the dbgear CLI:

```bash
# Generate documentation (outputs to ./docs by default)
dbgear --project path/to/project doc

# Specify output directory
dbgear --project path/to/project doc -o ./documentation
```

### Programmatic Usage

```python
from dbgear_doc import DocumentGenerator, generate_docs
from dbgear.models.schema import SchemaManager
from pathlib import Path

# Simple usage
generate_docs("schema.yaml", "./docs")

# Advanced usage with SchemaManager
schema_manager = SchemaManager.load("schema.yaml")
generator = DocumentGenerator(schema_manager)
generated_files = generator.generate(Path("./docs"))
```

## Output Structure

```
docs/
├── index.md              # Main index with schema list
└── {schema_name}/
    ├── README.md         # Schema overview with table list
    └── {table_name}.md   # Individual table documentation
```

## Generated Documentation

Each table documentation includes:

- **Description**: Table notes/comments from schema
- **Columns**: Column name, type, nullable, default, and description
- **Primary Key**: Primary key columns
- **Indexes**: Index definitions with columns and uniqueness
- **Foreign Keys**: Foreign key constraints with references

## License

MIT License
