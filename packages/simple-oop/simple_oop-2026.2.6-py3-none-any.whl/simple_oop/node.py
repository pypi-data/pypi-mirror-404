import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional, Any, Iterable

from colorama import Fore

from simple_oop import Config
from simple_oop.config import VariableType

log = logging.getLogger("simple-oop")


class Node:
    def __init__(self, ctx: 'NodeContext', name: str) -> None:
        self.ctx: 'NodeContext' = ctx

        self.file: Optional[Path] = None
        self.declaration: Optional[str] = None

        self.variables: dict[str, Any] = {name: _type.default() for name, _type in ctx.config.variables.items()}
        self.variables["name"] = name

        self.references: dict[str, list['Node']] = defaultdict(list)

    def declare(self, file: Path, declaration: str) -> None:
        assert (self.declaration is None) == (self.file is None)

        if self.declaration is not None:
            print(f"{Fore.YELLOW}Node {Fore.RED}{self.variables["name"]}{Fore.YELLOW} was declared twice.{Fore.RESET}\n"
                  f"Once in {self.file}:\n"
                  f"{self.declaration}\n"
                  f"Then in {file}:\n"
                  f"{declaration}")
            raise ValueError

        self.file = file
        self.declaration = declaration

    def set_variable(self, name: str, value: Optional[str], _type: VariableType) -> None:
        actual_value: Any
        match _type:
            case VariableType.BOOL:
                actual_value = value is not None
            case VariableType.NODE if value is not None:
                actual_value = self.ctx.node(value)
                actual_value.references[name].append(self)
            case _:
                actual_value = value

        self.variables[name] = actual_value

    def print(self, skip_types=frozenset()):
        for name, _type in self.ctx.config.variables.items():
            if _type in skip_types: continue
            value = self.variables[name]
            print(_type.format(name, value), end="")

        print()

    def print_tree(self, tree_field, indent=0) -> None:
        print(end=" " * 4 * indent)
        self.print(frozenset([VariableType.NODE]))
        for child in self.references[tree_field]:
            child.print_tree(tree_field, indent + 1)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.variables["name"]

    def __getitem__(self, item: str):
        try:
            return getattr(self, item)
        except AttributeError:
            pass

        invert: bool = False

        if item.startswith("not"):
            invert = True
            item = item.removeprefix("not").lstrip()

        if item not in self.ctx.config.variables:
            log.error(
                f"Variable {item} used in a template declaration or "
                f"template and was not declared in \"variables\"")
            sys.exit(1)

        value = self.variables[item]
        if invert:
            return not value
        else:
            return value

    def children(self, variable: str, indirect: bool = False) -> Iterable['Node']:
        if indirect:
            yield self
            for child in self.references[variable]:
                yield from child.children(variable, indirect=indirect)
        else:
            yield from self.references[variable]


class NodeContext:
    def __init__(self, config: Config):
        self.config: Config = config
        self.nodes: dict[str, Node] = {}
        self.errors: int = 0

    def node(self, name: str) -> Node:
        if name not in self.nodes:
            self.nodes[name] = Node(self, name)
        return self.nodes[name]

    def print_types(self):
        for node in self.nodes.values():
            node.print()
