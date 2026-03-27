#!/usr/bin/env python3
"""Find unused functions, methods, and classes in the codebase."""

import ast
import os
from collections import defaultdict
from pathlib import Path
from typing import List, Set, Tuple


class CodeAnalyzer(ast.NodeVisitor):
    """Analyze Python code to find definitions and usages."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.module_name = self._get_module_name(filepath)
        self.definitions = set()  # (type, name, lineno)
        self.usages = set()  # names used
        self.imports = set()  # imported names
        self.current_class = None

    def _get_module_name(self, filepath: str) -> str:
        """Convert filepath to module name."""
        path = Path(filepath).absolute()
        try:
            parts = path.relative_to(Path.cwd().absolute()).with_suffix("").parts
        except ValueError:
            # If not relative to cwd, just use the filename
            parts = (path.stem,)
        
        if parts and parts[0] == "src":
            parts = parts[1:]
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else path.stem

    def visit_ClassDef(self, node: ast.ClassDef):
        """Record class definitions."""
        full_name = f"{self.module_name}.{node.name}"
        self.definitions.add(("class", full_name, node.lineno))

        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Record function/method definitions."""
        if node.name.startswith("__") and node.name.endswith("__"):
            # Skip magic methods
            self.generic_visit(node)
            return

        if self.current_class:
            full_name = f"{self.module_name}.{self.current_class}.{node.name}"
            self.definitions.add(("method", full_name, node.lineno))
        else:
            full_name = f"{self.module_name}.{node.name}"
            self.definitions.add(("function", full_name, node.lineno))

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Record async function/method definitions."""
        self.visit_FunctionDef(node)

    def visit_Name(self, node: ast.Name):
        """Record name usages."""
        self.usages.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Record attribute access."""
        self.usages.add(node.attr)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Record imports."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Record from imports."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)


def analyze_file(filepath: str) -> Tuple[Set, Set]:
    """Analyze a single Python file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filepath)

        analyzer = CodeAnalyzer(filepath)
        analyzer.visit(tree)
        return analyzer.definitions, analyzer.usages
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return set(), set()


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual env, cache, etc.
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                "venv",
                "__pycache__",
                ".git",
                "htmlcov",
                ".pytest_cache",
                ".mypy_cache",
            }
        ]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """Main analysis function."""
    print("Analyzing codebase for unused code...")

    # Find all Python files
    files = find_python_files("src")
    files.append("main.py")

    # Analyze all files
    all_definitions = {}  # full_name -> (type, filepath, lineno)
    all_usages = set()

    for filepath in files:
        definitions, usages = analyze_file(filepath)

        for def_type, name, lineno in definitions:
            all_definitions[name] = (def_type, filepath, lineno)

        # Extract simple names from usages
        for usage in usages:
            all_usages.add(usage)

    # Find unused definitions
    unused = []
    for full_name, (def_type, filepath, lineno) in all_definitions.items():
        # Extract the simple name (last part)
        simple_name = full_name.split(".")[-1]

        # Special cases to always keep
        if simple_name in {"main", "run", "MainApplication"}:
            continue
        if simple_name.startswith("test_"):
            continue

        # Check if used
        if simple_name not in all_usages:
            unused.append((def_type, full_name, filepath, lineno))

    # Sort by type and name
    unused.sort(key=lambda x: (x[0], x[1]))

    # Print results
    if unused:
        print(f"\nFound {len(unused)} potentially unused definitions:\n")

        by_type = defaultdict(list)
        for def_type, name, filepath, lineno in unused:
            by_type[def_type].append((name, filepath, lineno))

        for def_type in ["class", "function", "method"]:
            if def_type in by_type:
                print(f"\n{def_type.upper()}S ({len(by_type[def_type])}):")
                for name, filepath, lineno in by_type[def_type]:
                    print(f"  {filepath}:{lineno} - {name}")
    else:
        print("\nNo unused code found!")

    return unused


if __name__ == "__main__":
    main()
