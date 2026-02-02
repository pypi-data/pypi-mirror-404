"""
Patch processing module for DBGear.

Handles YAML patch file parsing and SQL generation for custom data restoration.
"""

import yaml
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PatchConfig:
    """Represents a patch configuration loaded from YAML."""

    def __init__(self, name: str, columns: Dict[str, str], where: Optional[str] = None):
        self.name = name
        self.columns = columns
        self.where = where

    @classmethod
    def from_dict(cls, data: Dict) -> 'PatchConfig':
        """Create PatchConfig from dictionary."""
        if 'name' not in data:
            raise ValueError("Patch config must have 'name' field")
        if 'columns' not in data:
            raise ValueError("Patch config must have 'columns' field")
        if not isinstance(data['columns'], dict):
            raise ValueError("'columns' must be a dictionary mapping insert columns to select expressions")

        return cls(
            name=data['name'],
            columns=data['columns'],
            where=data.get('where')
        )

    @classmethod
    def load_from_file(cls, file_path: str) -> 'PatchConfig':
        """Load patch configuration from YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            return cls.from_dict(data)
        except FileNotFoundError:
            raise ValueError(f"Patch file not found: {file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in patch file: {e}")


def generate_patch_sql(env: str, patch_config: PatchConfig, backup_key: str) -> str:
    """
    Generate INSERT SQL from patch configuration.

    Args:
        env: Database environment name
        patch_config: Patch configuration
        backup_key: Backup table timestamp key (YYYYMMDDHHMMSS)

    Returns:
        Generated INSERT SQL string
    """
    table_name = patch_config.name
    backup_table = f"bak_{table_name}_{backup_key}"

    # Build INSERT column names
    insert_columns = ",\n  ".join(patch_config.columns.keys())

    # Build SELECT expressions
    select_expressions = ",\n  ".join(patch_config.columns.values())

    # Build WHERE clause if specified
    where_clause = ""
    if patch_config.where:
        where_clause = f"\nWHERE {patch_config.where}"

    # Generate final SQL
    sql = f"""INSERT INTO {env}.{table_name} (
  {insert_columns}
)
SELECT
  {select_expressions}
FROM {env}.{backup_table}{where_clause}"""

    return sql


def validate_patch_config(patch_config: PatchConfig) -> List[str]:
    """
    Validate patch configuration and return list of warnings/errors.

    Returns:
        List of validation messages (empty if valid)
    """
    errors = []

    if not patch_config.name:
        errors.append("Table name cannot be empty")

    if not patch_config.columns:
        errors.append("Columns mapping cannot be empty")

    # Check for common SQL injection patterns in WHERE clause
    if patch_config.where:
        # Check for comment and statement separator patterns
        simple_patterns = [';', '--', '/*', '*/']
        where_upper = patch_config.where.upper()
        for pattern in simple_patterns:
            if pattern in where_upper:
                errors.append(f"Potentially dangerous pattern '{pattern}' found in WHERE clause")
                break

        # Check for destructive SQL keywords (word boundaries required)
        import re
        destructive_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER']
        for keyword in destructive_keywords:
            # Use word boundary to avoid false positives like "update_user"
            if re.search(rf'\b{keyword}\b', where_upper):
                errors.append(f"Potentially dangerous SQL keyword '{keyword}' found in WHERE clause")
                break

    # Check for dangerous patterns in column expressions
    for insert_col, select_expr in patch_config.columns.items():
        if not insert_col or not isinstance(insert_col, str):
            errors.append(f"Invalid column name: {insert_col}")
            continue
        if not select_expr or not isinstance(select_expr, str):
            errors.append(f"Invalid select expression for column '{insert_col}'")
            continue

        # Check for dangerous patterns in select expressions
        expr_upper = select_expr.upper()
        for pattern in [';', '--', '/*', '*/']:
            if pattern in expr_upper:
                errors.append(
                    f"Potentially dangerous pattern '{pattern}' found in expression for column '{insert_col}'"
                )
                break

    return errors
