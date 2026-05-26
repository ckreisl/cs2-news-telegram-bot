from __future__ import annotations

import html
import re

from cs2posts.parser.parser import Parser


class SteamNewsTableParser(Parser):

    TABLE_PATTERN = re.compile(r'\[table\](.*?)\[/table\]', re.IGNORECASE | re.DOTALL)
    ROW_PATTERN = re.compile(r'\[tr\](.*?)\[/tr\]', re.IGNORECASE | re.DOTALL)
    CELL_PATTERN = re.compile(r'\[t[dh]\](.*?)\[/t[dh]\]', re.IGNORECASE | re.DOTALL)

    def parse(self) -> str:
        self.text = self.TABLE_PATTERN.sub(self._render_table, self.text)
        return self.text

    def _render_table(self, match: re.Match[str]) -> str:
        content = self._normalize_line_breaks(match.group(1))
        rows = self._extract_rows(content)

        if not rows:
            return ''

        column_widths = self._column_widths(rows)
        rendered_rows = [self._render_row(row, column_widths) for row in rows]
        table_text = '\n'.join(rendered_rows)

        return f'<pre>{html.escape(table_text)}</pre>'

    def _normalize_line_breaks(self, text: str) -> str:
        return text.replace('<br />', '\n').replace('<br/>', '\n')

    def _extract_rows(self, content: str) -> list[list[str]]:
        rows: list[list[str]] = []

        for row_match in self.ROW_PATTERN.finditer(content):
            row_text = row_match.group(1)
            cells = self._extract_cells(row_text)
            if cells:
                rows.append(cells)

        return rows

    def _extract_cells(self, row_text: str) -> list[str]:
        return [self._normalize_cell(cell) for cell in self.CELL_PATTERN.findall(row_text)]

    def _normalize_cell(self, value: str) -> str:
        return re.sub(r'\s+', ' ', value.strip())

    def _column_widths(self, rows: list[list[str]]) -> list[int]:
        if not rows:
            return []

        max_columns = max(len(row) for row in rows)
        return [
            max((len(row[index]) for row in rows if index < len(row)), default=0)
            for index in range(max_columns)
        ]

    def _render_row(self, row: list[str], widths: list[int]) -> str:
        cells: list[str] = []

        for index, cell in enumerate(row):
            padded_cell = cell if index == len(row) - 1 else cell.ljust(widths[index])
            cells.append(padded_cell)

        return ' | '.join(cells)
