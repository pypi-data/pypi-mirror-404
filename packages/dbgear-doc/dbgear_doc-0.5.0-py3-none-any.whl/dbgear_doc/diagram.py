"""
Diagram configuration module.

Provides models for diagram.yaml configuration file that defines
category-based background colors for ER diagrams.
"""

from pathlib import Path
import pydantic
import yaml


class CategoryStyle(pydantic.BaseModel):
    """Style configuration for a category."""
    background_color: str = "#FFFFFF"
    use_gradient: bool = False


class DiagramConfig(pydantic.BaseModel):
    """
    Diagram configuration loaded from diagram.yaml.

    Example diagram.yaml:
        categories:
          master:
            background_color: "#E3F2FD"
            use_gradient: true
          transaction:
            background_color: "#FFF3E0"
          log:
            background_color: "#E8F5E9"
        default:
          background_color: "#FFFFFF"
    """
    categories: dict[str, CategoryStyle] = pydantic.Field(default_factory=dict)
    default: CategoryStyle = pydantic.Field(default_factory=CategoryStyle)

    def get_style(self, table_categories: list[str] | None) -> CategoryStyle:
        """
        Get style for a table based on its categories.

        Args:
            table_categories: List of category names assigned to the table.
                            If multiple categories, uses the first one defined in diagram.yaml.
                            If None or empty, uses default style.

        Returns:
            CategoryStyle with background_color and use_gradient
        """
        if not table_categories:
            return self.default

        # Find the first category that has a style defined
        for category in table_categories:
            if category in self.categories:
                return self.categories[category]

        return self.default

    def get_background_color(self, table_categories: list[str] | None) -> str:
        """
        Get background color for a table based on its categories.

        Args:
            table_categories: List of category names assigned to the table.
                            If multiple categories, uses the first one defined in diagram.yaml.
                            If None or empty, uses default color.

        Returns:
            Background color hex string (e.g., "#E3F2FD")
        """
        return self.get_style(table_categories).background_color


def load_diagram_config(project_path: str | Path) -> DiagramConfig:
    """
    Load diagram configuration from diagram.yaml.

    Args:
        project_path: Path to the project directory (where project.yaml is located)

    Returns:
        DiagramConfig instance (with defaults if file doesn't exist)
    """
    config_path = Path(project_path) / "diagram.yaml"

    if not config_path.exists():
        return DiagramConfig()

    with open(config_path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    return DiagramConfig.model_validate(data)
