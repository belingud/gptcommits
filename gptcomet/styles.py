import typing as t
from decimal import Decimal
from enum import Enum, StrEnum

from git import safe_decode
from rich.color import Color
from rich.panel import Panel
from rich.text import Text

from gptcomet.utils import defenc


class Styles(StrEnum):
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    STRIKE = "strike"
    STRIKE_ITALIC = "strike italic"
    STRIKE_BOLD = "strike bold"
    STRIKE_BOLD_ITALIC = "strike bold italic"
    ITALIC_BOLD = "italic bold"
    ITALIC_BOLD_UNDERLINE = "italic bold underline"


class Colors(StrEnum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"
    BLACK = "black"

    LIGHT_RED = "rgb(255,100,0)"
    LIGHT_GREEN = "rgb(173,255,47)"
    LIGHT_YELLOW = "rgb(255,255,224)"
    LIGHT_BLUE = "rgb(135,206,235)"
    LIGHT_MAGENTA = "rgb(255,105,180)"
    LIGHT_CYAN = "rgb(224,255,255)"
    LIGHT_WHITE = "rgb(245,245,245)"

    BRIGHT = "bright"

    DEFAULT = "default"


def stylize(text: str, *styles: str) -> Text:
    """
    Format the text with specified styles.

    Args:
        text (str): The text to format.
        *styles (str): The styles to apply to the text.

    Returns:
        str: The formatted text.
    """
    styles = tuple(safe_decode(s) for s in styles)
    if isinstance(text, (int, float, Decimal)):
        text = str(text)
    elif isinstance(text, bytes):
        text = text.decode(defenc)
    return Text(text, style=" ".join(styles))
