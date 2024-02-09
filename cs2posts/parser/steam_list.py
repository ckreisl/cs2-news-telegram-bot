from __future__ import annotations

from cs2posts.parser.parser import Parser


class SteamListParser(Parser):

    LIST_START_TAG = "<ul>"
    LIST_END_TAG = "</ul>"
    LIST_ITEM_START_TAG = "<li>"
    LIST_ITEM_END_TAG = "</li>"
    LIST_ITEM_ICON = "•"
    LIST_ITEM_ICON_NESTED = "◦"

    def __init__(self, text: str):
        super().__init__(text)

    def is_tag(self, tag: str, i: int) -> bool:
        return self.text[i:i + len(tag)] == tag

    def is_start_tag_list(self, i: int) -> bool:
        return self.is_tag(self.LIST_START_TAG, i)

    def is_end_tag_list(self, i: int) -> bool:
        return self.is_tag(self.LIST_END_TAG, i)

    def is_start_tag_list_item(self, i: int) -> bool:
        return self.is_tag(self.LIST_ITEM_START_TAG, i)

    def is_end_tag_list_item(self, i: int) -> bool:
        return self.is_tag(self.LIST_ITEM_END_TAG, i)

    def parse(self) -> str:
        i = 0
        nested_lvl = 0
        modified_str = ""

        while i < len(self.text):
            if self.is_start_tag_list(i):
                modified_str += "" if nested_lvl > 0 else "\n"
                i += len(self.LIST_START_TAG)
                nested_lvl += 1
                continue

            if self.is_start_tag_list_item(i):
                space = " " * (nested_lvl - 1) * 4 if nested_lvl > 1 else ""
                if nested_lvl > 1:
                    tag = self.LIST_ITEM_ICON_NESTED
                else:
                    tag = self.LIST_ITEM_ICON
                modified_str += f"{space}{tag} "
                i += len(self.LIST_ITEM_START_TAG)
                continue

            if self.is_end_tag_list_item(i):
                modified_str += "\n"
                i += len(self.LIST_ITEM_END_TAG)
                continue

            if self.is_end_tag_list(i):
                modified_str += "" if nested_lvl > 1 else "\n"
                nested_lvl -= 1
                i += len(self.LIST_END_TAG)
                continue

            modified_str += self.text[i]
            i += 1

        self.text = modified_str

        return self.text
