# cli.py
import sys
import inspect
from typing import Callable, Dict


class Command:
    def __init__(self, func: Callable, name: str):
        self.func = func
        self.name = name
        self.help = func.__doc__ or ""
        self.signature = inspect.signature(func)

    def run(self, argv: list[str]):
        params = list(self.signature.parameters.values())
        args = []

        for i, param in enumerate(params):
            if i < len(argv):
                args.append(argv[i])
            elif param.default is not inspect.Parameter.empty:
                args.append(param.default)
            else:
                raise SystemExit(f"Missing argument: {param.name}")

        self.func(*args)


class CLI:
    def __init__(self):
        self.commands: Dict[str, Command] = {}

    def command(self, name: str | None = None):
        def decorator(func: Callable):
            cmd_name = name or func.__name__
            self.commands[cmd_name] = Command(func, cmd_name)
            return func
        return decorator

    def run(self, argv=None):
        argv = argv or sys.argv[1:]

        if not argv or argv[0] in {"-h", "--help"}:
            self.help()
            return

        cmd, *args = argv
        if cmd not in self.commands:
            print(f"Unknown command: {cmd}\n")
            self.help()
            return

        self.commands[cmd].run(args)

    def help(self):
        print("Available commands:\n")
        for name, cmd in self.commands.items():
            print(f"  {name:<12} {cmd.help}")
