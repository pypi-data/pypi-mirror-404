import re
from typing import Any

# =============================================================================
# Template Validation
# =============================================================================

SAFE_BUILTINS: dict[str, Any] = {
    "len": len,
    "str": str,
    "int": int,
    "bool": bool,
    "float": float,
    "tuple": tuple,
    "list": list,
    "dict": dict,
    "set": set,
    "all": all,
    "any": any,
    "isinstance": isinstance,
    "type": type,
    "True": True,
    "False": False,
    "None": None,
}

# fmt: off
EMPTY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(re.compile(p) for p in [
    r'=\s*""',                  # empty string: = ""
    r"=\s*''",                  # empty string: = ''
    r'"\s*"',                   # empty string literal: ""
    r"'\s*'",                   # empty string literal: ''
    r"=\s*\(\s*,",              # tuple starting with comma: = (,
    r",\s*,",                   # consecutive commas: , ,
    r",\s*\)",                  # trailing comma before close: ,)
    r"\(\s*\)",                 # empty parens: ()
    r"\{\{.*\}\}",              # unrendered jinja: {{ var }}
])
# fmt: on
