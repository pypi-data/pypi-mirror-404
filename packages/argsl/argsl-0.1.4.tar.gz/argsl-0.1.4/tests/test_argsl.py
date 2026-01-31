from argsl import argsl
import sys

def test_simple_flags(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ["prog", "input.txt", "--name", "Alice", "--level", "high", "--debug"])
    args = argsl("""
    filename <path!>                # Positional required
    --name|-n <str=env:USER>        # Optional with env fallback
    --level|-l <choice:low,med,high=med>  # Choice with default
    --debug|-d <flag>               # Boolean flag
    """)
    assert args.filename.name == "input.txt"
    assert args.name == "Alice"
    assert args.level == "high"
    assert args.debug is True
