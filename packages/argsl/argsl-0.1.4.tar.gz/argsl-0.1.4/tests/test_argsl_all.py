import sys
from argsl import argsl

# Define test cases
test_cases = [
    {
        "argv": ["prog", "file.txt"],
        "dsl": "filename <path!>  # Required positional path",
        "check": lambda args: args.filename.name == "file.txt"
    },
    {
        "argv": ["prog", "--verbose"],
        "dsl": "--verbose|-v <flag>  # Optional flag",
        "check": lambda args: args.verbose is True
    },
    {
        "argv": ["prog", "--count", "42"],
        "dsl": "--count|-c <int=0>  # Integer with default",
        "check": lambda args: args.count == 42
    },
    {
        "argv": ["prog"],
        "dsl": "--count|-c <int=3>  # Integer with default",
        "check": lambda args: args.count == 3
    },
    {
        "argv": ["prog", "--choice", "b"],
        "dsl": "--choice <choice:a,b,c=\"a\">  # Choice with default",
        "check": lambda args: args.choice == "b"
    },
    {
        "argv": ["prog"],
        "dsl": "--choice <choice:a,b,c=\"c\">  # Choice with default",
        "check": lambda args: args.choice == "c"
    },
    {
        "argv": ["prog", "--name", "Alice"],
        "dsl": "--name <str!>  # Required string",
        "check": lambda args: args.name == "Alice"
    },
    {
        "argv": ["prog", "--list", "a", "b"],
        "dsl": "--list <str*>  # Multiple string values",
        "check": lambda args: args.list == ["a", "b"]
    },
    {
        "argv": ["prog"],
        "dsl": "--default <str=\"hello world\">  # Quoted default string",
        "check": lambda args: args.default == "hello world"
    },
    {
        "argv": ["prog", "--no-cache"],
        "dsl": "--no-cache <flag>  # disables cache if passed",
        "check": lambda args: args.no_cache is True
    },
    {
        "argv": ["prog"],
        "dsl": "--no-cache <flag>  # disables cache if passed",
        "check": lambda args: args.no_cache is False
    }
]

# Pytest-compatible test
def test_all_edge_cases(monkeypatch):
    for case in test_cases:
        monkeypatch.setattr(sys, "argv", case["argv"])
        args = argsl(case["dsl"])
        assert case["check"](args), f"Failed: {case['argv']} with DSL {case['dsl']}"
