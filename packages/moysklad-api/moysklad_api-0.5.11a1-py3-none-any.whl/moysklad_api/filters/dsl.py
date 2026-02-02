from .operators import (
    Contains,
    Empty,
    Endswith,
    Eq,
    Gt,
    Gte,
    Lt,
    Lte,
    NotContains,
    Startswith,
)


class Field:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, value):
        return Eq(self.name, value)

    def __gt__(self, value):
        return Gt(self.name, value)

    def __lt__(self, value):
        return Lt(self.name, value)

    def __ge__(self, value):
        return Gte(self.name, value)

    def __le__(self, value):
        return Lte(self.name, value)

    def contains(self, value):
        return Contains(self.name, value)

    def not_contains(self, value):
        return NotContains(self.name, value)

    def startswith(self, value):
        return Startswith(self.name, value)

    def endswith(self, value):
        return Endswith(self.name, value)

    def empty(self):
        return Empty(self.name)


class Filters:
    def __getattr__(self, v: str) -> Field:
        return Field(v)
