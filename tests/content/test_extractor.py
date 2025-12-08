from __future__ import annotations

import pytest

from cs2posts.content.content import Content
from cs2posts.content.extractor import Extractor


class ConcreteExtractor(Extractor):
    """Concrete implementation for testing the abstract Extractor class."""

    def extract(self) -> list[Content]:
        return []


def test_extractor_init():
    text = "sample text"
    extractor = ConcreteExtractor(text)
    assert extractor.text == text


def test_extractor_text_property():
    text = "another sample text"
    extractor = ConcreteExtractor(text)
    assert extractor.text == "another sample text"


def test_extractor_empty_text():
    extractor = ConcreteExtractor("")
    assert extractor.text == ""


def test_extractor_text_with_special_characters():
    text = "text with [special] characters <html> & symbols"
    extractor = ConcreteExtractor(text)
    assert extractor.text == text


def test_extractor_text_is_private():
    extractor = ConcreteExtractor("test")
    # The text should be accessible through the property but stored privately
    assert extractor.text == "test"
    # Verify that the private attribute exists
    assert hasattr(extractor, '_Extractor__text')


def test_extractor_abstract_method():
    """Test that extract method can be called on concrete implementation."""
    extractor = ConcreteExtractor("test")
    result = extractor.extract()
    assert result == []


def test_extractor_cannot_instantiate_abstract():
    """Test that the abstract Extractor class cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Extractor("test")
