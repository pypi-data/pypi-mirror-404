import argparse
import logging
import os
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from typing import Union

import colorama
from colorama import Fore
from pydantic import ValidationError

from .config import Config, VariableType
from .discovery import discover
from .node import NodeContext
from .version import program_version

colorama.init(autoreset=True)

from .code_gen import TemplateEnvironment  # I put this here to stop it from being moved (professional, I know)

PROGRAM_NAME = "simple-oop"

log = logging.getLogger(PROGRAM_NAME)
console = logging.StreamHandler()
log.addHandler(console)
log.setLevel(logging.DEBUG)
console.setFormatter(
    logging.Formatter(
        f"{{asctime}} [{Fore.YELLOW}{{levelname:>5}}{Fore.RESET}] {Fore.BLUE}{{name}}{Fore.RESET}: {{message}}",
        style="{", datefmt="W%W %a %I:%M"))

colorama.init(autoreset=True)


def command_entry_point():
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Program was interrupted by user")


class Mode(ABC):
    modes: list[type['Mode']] = []
    name: Union[None, str] = None
    description: Union[None, str] = None

    @classmethod
    @abstractmethod
    def create_parser(cls, obj) -> ArgumentParser:
        parser = obj.add_parser(cls.name, description=cls.description, help=cls.description)
        parser.set_defaults(mode=cls)
        return parser

    @classmethod
    @abstractmethod
    def call(cls, args):
        pass


@Mode.modes.append
class Generate(Mode):
    name = "generate"
    description = "TODO"  # TODO

    @classmethod
    def create_parser(cls, obj) -> ArgumentParser:
        parser = super().create_parser(obj)
        parser.add_argument("-w", "--working-directory", type=Path, default=Path(os.getcwd()))
        parser.add_argument("--dump-tree", type=str, default=None)
        return parser

    @classmethod
    def call(cls, args: argparse.Namespace) -> None:
        os.chdir(args.working_directory.resolve())

        config_file = Path("simple-oop/config.json")
        assert config_file.exists(), f"File {config_file} does not exist at {os.getcwd()}"
        try:
            c = Config.model_validate_json(config_file.read_text())
        except ValidationError as e:
            print(e)
            return

        if args.verbose:
            log.debug("Using following config:")
            print(c.model_dump_json(indent=4))

        ctx = NodeContext(c)

        discover(ctx, c.input_directories[0])

        if ctx.errors > 0:
            log.error(f"Discovery failed with {ctx.errors} error(s)")
            return

        if args.verbose:
            log.debug("Found the following type structure:")
            ctx.print_types()

        if args.dump_tree is not None:
            assert args.dump_tree in c.variables
            assert c.variables[args.dump_tree] == VariableType.NODE

            roots = [n for n in ctx.nodes.values() if n.variables[args.dump_tree] is None]
            for r in roots:
                r.print_tree(args.dump_tree)

        gen = TemplateEnvironment(ctx)

        for template in c.templates:
            gen.generate(template)


def main():
    parser = ArgumentParser(prog=PROGRAM_NAME,
                            description="Placeholder description",
                            allow_abbrev=True, add_help=True, exit_on_error=True)

    parser.add_argument('-v', '--verbose', action='store_true', help="Show more output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {program_version}")

    subparsers = parser.add_subparsers(title="Modes", description="Possible modes of operation", required=True)
    for mode in Mode.modes:
        mode.create_parser(subparsers)

    args = parser.parse_args()

    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    log.debug("Starting program...")

    args.mode.call(args)
