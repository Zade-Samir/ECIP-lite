import os
import re
from typing import List, Dict, Any, Optional
from ecip_core.common.logger import get_logger
from ecip_core.models.sql_metadata import (
    SqlMetadata, TableMetadata, ColumnMetadata, ForeignKeyMetadata,
    ViewMetadata, IndexMetadata, ProcedureMetadata
)

logger = get_logger(__name__)


class SqlParser:
    """
    Parses SQL files (.sql, Flyway migrations, DDL scripts) and extracts rich schema metadata.
    """

    def parse(self, file_path: str) -> SqlMetadata:
        logger.info("SQL parsed")
        metadata = SqlMetadata(file_path=file_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error("Parse failure")
            raise e

        if not content.strip():
            return metadata

        statements = self._get_statements(content)

        for stmt in statements:
            try:
                # 1. CREATE TABLE
                if re.match(r"^CREATE\s+TABLE", stmt, re.IGNORECASE):
                    self._parse_create_table(stmt, metadata)
                # 2. CREATE VIEW
                elif re.match(r"^CREATE\s+(?:OR\s+REPLACE\s+)?VIEW", stmt, re.IGNORECASE):
                    self._parse_create_view(stmt, metadata)
                # 3. CREATE INDEX
                elif re.match(r"^CREATE\s+(?:UNIQUE\s+)?INDEX", stmt, re.IGNORECASE):
                    self._parse_create_index(stmt, metadata)
                # 4. CREATE PROCEDURE
                elif re.match(r"^CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE", stmt, re.IGNORECASE):
                    self._parse_create_procedure(stmt, metadata)
            except Exception as e:
                logger.warning(f"Failed to parse statement: {stmt}. Error: {e}")
                logger.warning("Unsupported SQL dialect")

        return metadata

    def _get_statements(self, sql: str) -> List[str]:
        # Clean multi-line comments
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        # Clean single-line comments
        sql = re.sub(r"--.*", "", sql)
        
        # Split by semicolon and clean whitespace
        statements = []
        for stmt in sql.split(";"):
            cleaned = re.sub(r"\s+", " ", stmt).strip()
            if cleaned:
                statements.append(cleaned)
        return statements

    def _parse_create_table(self, stmt: str, metadata: SqlMetadata) -> None:
        # Match table name and columns block
        match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w\.\`]+)\s*\((.*)\)", stmt, re.IGNORECASE)
        if not match:
            return

        table_name = match.group(1).replace("`", "").replace("\"", "")
        columns_block = match.group(2)

        table_meta = TableMetadata(name=table_name)
        parts = self._split_columns_block(columns_block)

        for part in parts:
            part_upper = part.upper()
            
            # Primary Key constraint: PRIMARY KEY (col1, col2)
            if part_upper.startswith("PRIMARY KEY"):
                pk_match = re.search(r"PRIMARY\s+KEY\s*\((.*?)\)", part, re.IGNORECASE)
                if pk_match:
                    pks = [pk.strip().replace("`", "").replace("\"", "") for pk in pk_match.group(1).split(",")]
                    table_meta.primary_keys.extend(pks)
                    # Update column flags
                    for col in table_meta.columns:
                        if col.name in pks:
                            col.is_primary = True
                continue

            # Foreign Key constraint: FOREIGN KEY (col) REFERENCES other_table(other_col)
            if part_upper.startswith("FOREIGN KEY") or "FOREIGN KEY" in part_upper:
                fk_match = re.search(r"FOREIGN\s+KEY\s*\((.*?)\)\s*REFERENCES\s+([\w\.\`]+)\s*\((.*?)\)", part, re.IGNORECASE)
                if fk_match:
                    col_name = fk_match.group(1).strip().replace("`", "").replace("\"", "")
                    ref_table = fk_match.group(2).strip().replace("`", "").replace("\"", "")
                    ref_col = fk_match.group(3).strip().replace("`", "").replace("\"", "")
                    table_meta.foreign_keys.append(
                        ForeignKeyMetadata(
                            column=col_name,
                            referenced_table=ref_table,
                            referenced_column=ref_col
                        )
                    )
                continue

            # Constraint index fallback (e.g. CONSTRAINT fk_name FOREIGN KEY...)
            if part_upper.startswith("CONSTRAINT"):
                if "FOREIGN KEY" in part_upper:
                    fk_match = re.search(r"FOREIGN\s+KEY\s*\((.*?)\)\s*REFERENCES\s+([\w\.\`]+)\s*\((.*?)\)", part, re.IGNORECASE)
                    if fk_match:
                        col_name = fk_match.group(1).strip().replace("`", "").replace("\"", "")
                        ref_table = fk_match.group(2).strip().replace("`", "").replace("\"", "")
                        ref_col = fk_match.group(3).strip().replace("`", "").replace("\"", "")
                        table_meta.foreign_keys.append(
                            ForeignKeyMetadata(
                                column=col_name,
                                referenced_table=ref_table,
                                referenced_column=ref_col
                            )
                        )
                elif "PRIMARY KEY" in part_upper:
                    pk_match = re.search(r"PRIMARY\s+KEY\s*\((.*?)\)", part, re.IGNORECASE)
                    if pk_match:
                        pks = [pk.strip().replace("`", "").replace("\"", "") for pk in pk_match.group(1).split(",")]
                        table_meta.primary_keys.extend(pks)
                continue

            # Key/Unique Index parameters (MySQL specific key declarations)
            if part_upper.startswith("KEY ") or part_upper.startswith("INDEX "):
                continue

            # Standard Column Definition
            col_parts = part.split()
            if not col_parts:
                continue
            col_name = col_parts[0].replace("`", "").replace("\"", "")
            data_type = col_parts[1] if len(col_parts) > 1 else "VARCHAR"
            
            is_pk = "PRIMARY KEY" in part_upper
            is_nullable = "NOT NULL" not in part_upper and not is_pk

            if is_pk:
                table_meta.primary_keys.append(col_name)

            table_meta.columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=data_type,
                    is_primary=is_pk,
                    is_nullable=is_nullable
                )
            )

        metadata.tables.append(table_meta)

    def _split_columns_block(self, block: str) -> List[str]:
        """Splits columns in parentheses safely without breaking on decimal types like DECIMAL(10,2)."""
        parts = []
        current = []
        depth = 0
        for char in block:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            if char == ',' and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(char)
        if current:
            parts.append("".join(current).strip())
        return parts

    def _parse_create_view(self, stmt: str, metadata: SqlMetadata) -> None:
        match = re.search(r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([\w\.\`]+)\s+AS\s+(.*)", stmt, re.IGNORECASE)
        if match:
            view_name = match.group(1).replace("`", "").replace("\"", "")
            metadata.views.append(ViewMetadata(name=view_name, definition=match.group(2)))

    def _parse_create_index(self, stmt: str, metadata: SqlMetadata) -> None:
        match = re.search(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+([\w\.\`]+)\s+ON\s+([\w\.\`]+)\s*\((.*?)\)", stmt, re.IGNORECASE)
        if match:
            idx_name = match.group(1).replace("`", "").replace("\"", "")
            tbl_name = match.group(2).replace("`", "").replace("\"", "")
            cols = [c.strip().replace("`", "").replace("\"", "") for c in match.group(3).split(",")]
            metadata.indexes.append(
                IndexMetadata(
                    name=idx_name,
                    table_name=tbl_name,
                    columns=cols
                )
            )

    def _parse_create_procedure(self, stmt: str, metadata: SqlMetadata) -> None:
        match = re.search(r"CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+([\w\.\`]+)", stmt, re.IGNORECASE)
        if match:
            proc_name = match.group(1).replace("`", "").replace("\"", "")
            metadata.procedures.append(ProcedureMetadata(name=proc_name))
