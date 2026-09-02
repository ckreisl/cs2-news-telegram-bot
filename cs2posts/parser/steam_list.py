from __future__ import annotations


class SteamListParser:
    """Renders ``<ul>``/``<li>`` markup as indented bullet lines."""

    LIST_START_TAG = "<ul>"
    LIST_END_TAG = "</ul>"
    LIST_ITEM_START_TAG = "<li>"
    LIST_ITEM_END_TAG = "</li>"
    LIST_ITEM_ICON = "•"
    LIST_ITEM_ICON_NESTED = "◦"
    NESTED_INDENT = 4

    def parse(self, text: str) -> str:
        i = 0
        nested_lvl = 0
        out: list[str] = []

        while i < len(text):
            if text.startswith(self.LIST_START_TAG, i):
                out.append("" if nested_lvl > 0 else "\n")
                i += len(self.LIST_START_TAG)
                nested_lvl += 1
                continue

            if text.startswith(self.LIST_ITEM_START_TAG, i):
                is_nested = nested_lvl > 1
                indent = (
                    " " * (nested_lvl - 1) * self.NESTED_INDENT if is_nested else ""
                )
                icon = self.LIST_ITEM_ICON_NESTED if is_nested else self.LIST_ITEM_ICON
                out.append(f"{indent}{icon} ")

                empty_item = self.LIST_ITEM_START_TAG + self.LIST_ITEM_END_TAG
                if text.startswith(empty_item, i):
                    i += len(empty_item)
                else:
                    i += len(self.LIST_ITEM_START_TAG)
                continue

            if text.startswith(self.LIST_ITEM_END_TAG, i):
                out.append("\n")
                i += len(self.LIST_ITEM_END_TAG)
                continue

            if text.startswith(self.LIST_END_TAG, i):
                out.append("" if nested_lvl > 1 else "\n")
                nested_lvl -= 1
                i += len(self.LIST_END_TAG)
                continue

            out.append(text[i])
            i += 1

        return "".join(out)
