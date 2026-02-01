"""Contains useful regexes that get used lots of places"""

from __future__ import annotations

import re

NEWLINE_RE = re.compile(r"\r?\n")
SPACE_RE = re.compile(r"\s+")
COMMA_SEMI_RE = re.compile(r"\s*[,;]\s*")
NON_LETTER_LIKE_RE = re.compile(r"\W+")
NON_DIGIT_RE = re.compile(r"\D")
LEADING_UNDER_RE = re.compile(r"^_")
