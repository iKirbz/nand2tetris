from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Symbol:
    type: str
    kind: str
    index: int


@dataclass
class SymbolTable:
    class_symbols: Dict[str, Symbol] = field(default_factory=dict)
    subroutine_symbols: Dict[str, Symbol] = field(default_factory=dict)

    def start_subroutine(self) -> None:
        self.subroutine_symbols.clear()

    def define(self, name: str, type: str, kind: str) -> None:
        var_count = self.var_count(kind)

        if kind in ("static", "field"):
            self.class_symbols[name] = Symbol(type, kind, var_count)
        elif kind in ("argument", "local"):
            self.subroutine_symbols[name] = Symbol(type, kind, var_count)
        else:
            raise ValueError(f"Invalid kind: {kind}")

    def var_count(self, kind: str) -> int:
        if kind in ("static", "field"):
            count = sum(1 for symbol in self.class_symbols.values() if symbol.kind == kind)
        elif kind in ("argument", "local"):
            count = sum(1 for symbol in self.subroutine_symbols.values() if symbol.kind == kind)
        else:
            raise ValueError(f"Invalid kind: {kind}")

        return count

    def get(self, name: str) -> Symbol:
        if name in self.subroutine_symbols:
            return self.subroutine_symbols[name]
        elif name in self.class_symbols:
            return self.class_symbols[name]
        else:
            raise Exception(f"Symbol '{name}' not found")

    def has(self, name: str) -> bool:
        return name in self.subroutine_symbols or name in self.class_symbols
