import argparse
import os
import re
import pathlib
import ast

_type_map = {
    "str": str,
    "int": int,
    "float": float,
    "path": pathlib.Path,
    "bool": lambda x: x.lower() in ("1", "true", "yes"),
}

def _safe_literal(value):
    try:
        return ast.literal_eval(value)
    except Exception:
        return value  # treat as raw string if not evaluable

def argsl(dsl: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    for line in dsl.strip().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue

        if "#" in line:
            line, help_text = line.split("#", 1)
        else:
            help_text = ""

        m = re.match(r'(?P<flags>[\-\w| ]+)\s*<(?P<type_expr>[^>]+)>', line.strip())
        if not m:
            raise ValueError(f"Invalid argsl line: {line}")

        flag_part = m.group("flags").strip()
        flags = flag_part.split("|") if flag_part.startswith("-") else []
        positional = not flags
        argname = flag_part if positional else None

        type_expr = m.group("type_expr").strip()
        kwargs = {"help": help_text.strip()} if help_text.strip() else {}

        if type_expr == "flag":
            kwargs["action"] = "store_true"
        else:
            required = "!" in type_expr
            multiple = "*" in type_expr
            type_expr = type_expr.replace("!", "").replace("*", "")

            default = None
            env_fallback = None
            if "=env:" in type_expr:
                type_expr, env_fallback = type_expr.split("=env:")
                env_fallback = env_fallback.strip()
            elif "=" in type_expr:
                type_expr, default = type_expr.split("=", 1)
                default = _safe_literal(default.strip())

            if type_expr.startswith("choice:"):
                kwargs["choices"] = type_expr.split(":", 1)[1].split(",")
                kwargs["type"] = str
            else:
                kwargs["type"] = _type_map.get(type_expr, str)

            if default is not None:
                kwargs["default"] = default
            elif env_fallback:
                kwargs["default"] = os.getenv(env_fallback)

            if required and "default" not in kwargs and not positional:
                kwargs["required"] = True

            if multiple:
                kwargs["nargs"] = "+"

        if positional:
            parser.add_argument(argname, **kwargs)
        else:
            parser.add_argument(*flags, **kwargs)

    return parser.parse_args()

if __name__ == "__main__":
    print("ARGS:", argsl("""
    --name|-n <str!>     # Your name
    --debug|-d <flag>    # Debug mode
    """))

