"""
ER diagram generation module using in4viz library.

Provides SVG and draw.io format output for database schema visualization.
"""

from pathlib import Path

from in4viz import Table as In4vizTable, Column as In4vizColumn, LineType, Cardinality
from in4viz.backends.svg import SVGERDiagram
from in4viz.backends.drawio import DrawioERDiagram
from dbgear.models.schema import SchemaManager
from dbgear.models.table import Table
from dbgear.models.column import Column

from .diagram import DiagramConfig, load_diagram_config


def collect_related_tables(
    all_tables: dict[str, Table],
    start_table_name: str,
    direction: str,
    level: int,
    visited: set[str] | None = None
) -> set[str]:
    """
    Recursively collect related tables.

    Args:
        all_tables: Dictionary of all tables in the schema
        start_table_name: Name of the starting table
        direction: 'referenced_by' (tables that reference this) or 'references' (tables this references)
        level: How many levels deep to search
        visited: Set of already visited table names

    Returns:
        Set of table names including the start table
    """
    if visited is None:
        visited = set()

    if level < 0 or start_table_name in visited:
        return visited

    visited.add(start_table_name)

    if level == 0:
        return visited

    start_table = all_tables.get(start_table_name)
    if not start_table:
        return visited

    if direction == 'references':
        # Collect tables that this table references (via foreign keys)
        for relation in start_table.relations:
            target_table_name = relation.target.table_name
            if target_table_name in all_tables:
                collect_related_tables(
                    all_tables, target_table_name, direction, level - 1, visited
                )

    elif direction == 'referenced_by':
        # Collect tables that reference this table
        for table_name, table in all_tables.items():
            if table_name in visited:
                continue
            for relation in table.relations:
                if relation.target.table_name == start_table_name:
                    collect_related_tables(
                        all_tables, table_name, direction, level - 1, visited
                    )
                    break

    return visited


def dbgear_to_in4viz_column(column: Column) -> In4vizColumn:
    """
    Convert DBGear Column to in4viz Column.

    Args:
        column: DBGear Column object

    Returns:
        in4viz Column object
    """
    # Get column type display string
    col_type = column.column_type
    type_str = col_type.base_type if col_type else "UNKNOWN"

    if col_type and col_type.length:
        type_str += f"({col_type.length}"
        if col_type.precision:
            type_str += f",{col_type.precision}"
        type_str += ")"

    return In4vizColumn(
        name=column.column_name,
        logical_name=column.display_name or column.column_name,
        type=type_str,
        primary_key=(column.primary_key is not None),
        nullable=column.nullable,
        foreign_key=False,  # Will be set when processing relations
        index=False  # Will be set when processing indexes
    )


def dbgear_to_in4viz_table(
    table: Table,
    table_name: str,
    bgcolor: str = '#ffffff',
    use_gradient: bool = False
) -> In4vizTable:
    """
    Convert DBGear Table to in4viz Table.

    Args:
        table: DBGear Table object
        table_name: Name of the table
        bgcolor: Background color for the table in hex format (default: white)
        use_gradient: Whether to use gradient for background (default: False)

    Returns:
        in4viz Table object
    """
    columns = [dbgear_to_in4viz_column(col) for col in table.columns]

    # Mark foreign key columns
    for relation in table.relations:
        for bind in relation.bind_columns:
            for col in columns:
                if col.name == bind.source_column:
                    col.foreign_key = True

    # Mark indexed columns
    for index in table.indexes:
        for index_col in index.columns:
            for col in columns:
                if col.name == index_col:
                    col.index = True

    return In4vizTable(
        name=table_name,
        logical_name=table.display_name or table_name,
        columns=columns,
        bgcolor=bgcolor,
        use_gradient=use_gradient
    )


def _create_diagram(
    backend: str,
    schema_manager: SchemaManager,
    schema_name: str,
    center_table: str | None = None,
    referenced_by_level: int = 1,
    references_level: int = 1,
    category: str | None = None,
    diagram_config: DiagramConfig | None = None
):
    """
    Create ER diagram with specified backend.

    Args:
        backend: 'svg' or 'drawio'
        schema_manager: SchemaManager instance
        schema_name: Name of the schema
        center_table: Name of the table to center the diagram on (None for all tables)
        referenced_by_level: How many levels of tables that reference this table to include
        references_level: How many levels of tables this table references to include
        category: Filter tables by category (None for all tables)
        diagram_config: DiagramConfig for background colors (None uses defaults)

    Returns:
        Diagram instance (SVGERDiagram or DrawioERDiagram)

    Raises:
        ValueError: If schema or table not found
    """
    if diagram_config is None:
        diagram_config = DiagramConfig()

    # Get all tables in the schema
    schemas = schema_manager.schemas
    schema = schemas.get(schema_name)
    if not schema:
        raise ValueError(f"Schema '{schema_name}' not found")

    all_tables = {table.table_name: table for table in schema.tables}

    # Filter by category if specified
    if category:
        all_tables = {
            name: table for name, table in all_tables.items()
            if category in table.categories
        }

    # Determine which tables to include
    if center_table:
        if center_table not in all_tables:
            raise ValueError(f"Table '{center_table}' not found in schema '{schema_name}'")

        tables_to_include = {center_table}

        # Add tables that reference the center table
        if referenced_by_level > 0:
            ref_tables = collect_related_tables(
                all_tables, center_table, 'referenced_by', referenced_by_level, set()
            )
            tables_to_include.update(ref_tables)

        # Add tables that the center table references
        if references_level > 0:
            fk_tables = collect_related_tables(
                all_tables, center_table, 'references', references_level, set()
            )
            tables_to_include.update(fk_tables)
    else:
        # Include all tables
        tables_to_include = set(all_tables.keys())

    # Create ER diagram with appropriate backend
    if backend == 'svg':
        diagram = SVGERDiagram(
            default_line_type=LineType.STRAIGHT,
            min_width=1200,
            min_height=800
        )
    else:  # drawio
        diagram = DrawioERDiagram(
            default_line_type=LineType.STRAIGHT,
            min_width=1200,
            min_height=800
        )

    # Add tables to diagram
    in4viz_tables = {}
    for table_name in tables_to_include:
        table = all_tables[table_name]
        style = diagram_config.get_style(table.categories)
        in4viz_table = dbgear_to_in4viz_table(
            table, table_name, style.background_color, style.use_gradient
        )
        diagram.add_table(in4viz_table)
        in4viz_tables[table_name] = in4viz_table

    # Add edges (relationships)
    for table_name in tables_to_include:
        table = all_tables[table_name]
        for relation in table.relations:
            target_name = relation.target.table_name
            if target_name in tables_to_include:
                # Convert cardinality from DBGear format to in4viz format
                cardinality = Cardinality(
                    relation.cardinarity_source,
                    relation.cardinarity_target
                )

                diagram.add_edge(
                    table_name,
                    target_name,
                    LineType.STRAIGHT,
                    cardinality
                )

    return diagram


def generate_er_diagram_svg(
    schema_manager: SchemaManager,
    schema_name: str,
    center_table: str | None = None,
    referenced_by_level: int = 1,
    references_level: int = 1,
    category: str | None = None,
    diagram_config: DiagramConfig | None = None
) -> str:
    """
    Generate ER diagram in SVG format.

    Args:
        schema_manager: SchemaManager instance
        schema_name: Name of the schema
        center_table: Name of the table to center the diagram on (None for all tables)
        referenced_by_level: How many levels of tables that reference this table to include
        references_level: How many levels of tables this table references to include
        category: Filter tables by category (None for all tables)
        diagram_config: DiagramConfig for background colors (None uses defaults)

    Returns:
        SVG string of the ER diagram
    """
    diagram = _create_diagram(
        'svg', schema_manager, schema_name, center_table, referenced_by_level, references_level,
        category, diagram_config
    )
    return diagram.render_svg()


def generate_er_diagram_drawio(
    schema_manager: SchemaManager,
    schema_name: str,
    center_table: str | None = None,
    referenced_by_level: int = 1,
    references_level: int = 1,
    category: str | None = None,
    diagram_config: DiagramConfig | None = None
) -> str:
    """
    Generate ER diagram in draw.io XML format.

    Args:
        schema_manager: SchemaManager instance
        schema_name: Name of the schema
        center_table: Name of the table to center the diagram on (None for all tables)
        referenced_by_level: How many levels of tables that reference this table to include
        references_level: How many levels of tables this table references to include
        category: Filter tables by category (None for all tables)
        diagram_config: DiagramConfig for background colors (None uses defaults)

    Returns:
        draw.io XML string of the ER diagram
    """
    diagram = _create_diagram(
        'drawio', schema_manager, schema_name, center_table, referenced_by_level, references_level,
        category, diagram_config
    )
    return diagram.render_drawio()


def generate_svg(
    schema_path: str,
    output_path: str,
    schema_name: str | None = None,
    center_table: str | None = None,
    referenced_by_level: int = 1,
    references_level: int = 1,
    category: str | None = None,
    project_path: str | None = None
) -> str:
    """
    Generate SVG ER diagram from a schema file.

    This function serves as the entry point for the dbgear svg plugin.

    Args:
        schema_path: Path to the schema.yaml file.
        output_path: Path to write the SVG file.
        schema_name: Name of the schema (uses first schema if None).
        center_table: Table to center diagram on (all tables if None).
        referenced_by_level: Levels of tables that reference this table to include.
        references_level: Levels of tables this table references to include.
        category: Filter tables by category (None for all tables).
        project_path: Path to project directory for diagram.yaml (uses schema_path parent if None).

    Returns:
        Path to the generated SVG file.
    """
    schema_manager = SchemaManager.load(schema_path)

    # Use first schema if not specified
    if schema_name is None:
        schema_name = next(iter(schema_manager.schemas.keys()))

    # Load diagram config
    if project_path is None:
        project_path = Path(schema_path).parent
    diagram_config = load_diagram_config(project_path)

    svg_content = generate_er_diagram_svg(
        schema_manager, schema_name, center_table, referenced_by_level, references_level,
        category, diagram_config
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    return output_path


def generate_drawio(
    schema_path: str,
    output_path: str,
    schema_name: str | None = None,
    center_table: str | None = None,
    referenced_by_level: int = 1,
    references_level: int = 1,
    category: str | None = None,
    project_path: str | None = None
) -> str:
    """
    Generate draw.io ER diagram from a schema file.

    This function serves as the entry point for the dbgear drawio plugin.

    Args:
        schema_path: Path to the schema.yaml file.
        output_path: Path to write the draw.io XML file.
        schema_name: Name of the schema (uses first schema if None).
        center_table: Table to center diagram on (all tables if None).
        referenced_by_level: Levels of tables that reference this table to include.
        references_level: Levels of tables this table references to include.
        category: Filter tables by category (None for all tables).
        project_path: Path to project directory for diagram.yaml (uses schema_path parent if None).

    Returns:
        Path to the generated draw.io file.
    """
    schema_manager = SchemaManager.load(schema_path)

    # Use first schema if not specified
    if schema_name is None:
        schema_name = next(iter(schema_manager.schemas.keys()))

    # Load diagram config
    if project_path is None:
        project_path = Path(schema_path).parent
    diagram_config = load_diagram_config(project_path)

    drawio_content = generate_er_diagram_drawio(
        schema_manager, schema_name, center_table, referenced_by_level, references_level,
        category, diagram_config
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(drawio_content)

    return output_path
