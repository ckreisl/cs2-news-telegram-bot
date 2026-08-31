from __future__ import annotations

import html
import re


class SteamNewsTableParser:
    """Renders ``[table]`` bbcode as a column-aligned ``<pre>`` block."""

    TABLE_PATTERN = re.compile(r"\[table\](.*?)\[/table\]", re.IGNORECASE | re.DOTALL)
    ROW_PATTERN = re.compile(r"\[tr\](.*?)\[/tr\]", re.IGNORECASE | re.DOTALL)
    CELL_PATTERN = re.compile(r"\[t[dh]\](.*?)\[/t[dh]\]", re.IGNORECASE | re.DOTALL)
    WHITESPACE_PATTERN = re.compile(r"\s+")

    def parse(self, text: str) -> str:
        return self.TABLE_PATTERN.sub(self._render_table, text)

    def _render_table(self, match: re.Match[str]) -> str:
        content = self._normalize_line_breaks(match.group(1))
        rows = self._extract_rows(content)

        if not rows:
            return ""

        widths = self._column_widths(rows)
        table_text = "\n".join(self._render_row(row, widths) for row in rows)

        return f"<pre>{html.escape(table_text)}</pre>"

    def _normalize_line_breaks(self, text: str) -> str:
        return text.replace("<br />", "\n").replace("<br/>", "\n")

    def _extract_rows(self, content: str) -> list[list[str]]:
        rows = (
            self._extract_cells(match.group(1))
            for match in self.ROW_PATTERN.finditer(content)
        )
        return [cells for cells in rows if cells]

    def _extract_cells(self, row_text: str) -> list[str]:
        return [
            self._normalize_cell(cell) for cell in self.CELL_PATTERN.findall(row_text)
        ]

    def _normalize_cell(self, value: str) -> str:
        return self.WHITESPACE_PATTERN.sub(" ", value.strip())

    def _column_widths(self, rows: list[list[str]]) -> list[int]:
        max_columns = max(len(row) for row in rows)
        return [
            max((len(row[index]) for row in rows if index < len(row)), default=0)
            for index in range(max_columns)
        ]

    def _render_row(self, row: list[str], widths: list[int]) -> str:
        last = len(row) - 1
        return " | ".join(
            cell if index == last else cell.ljust(widths[index])
            for index, cell in enumerate(row)
        )
