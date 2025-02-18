from typing import Iterator, Self

from pymonad.monoid import Monoid  # type: ignore[import-untyped]


class Set[T](Monoid):  # type: ignore[no-any-unimported, misc]
    def __init__(self, val: set[T] | list[T] | tuple[T] | T = set()) -> None:
        self.value: set[T]
        if isinstance(val, set) or isinstance(val, list) or isinstance(val, tuple):
            self.value = set(val)
        else:
            self.value = {val}
        self.__iadd__ = self.__add__

    def issubset(self, other: Self | set[T]) -> bool:
        if isinstance(other, set):
            return self.value.issubset(other)
        return self.value.issubset(other.value)

    def issuperset(self, other: Self | set[T]) -> bool:
        if isinstance(other, set):
            return self.value.issuperset(other)
        return self.value.issuperset(other.value)

    def intersection(self: Self, other: Self) -> "Set[T]":
        return Set(self.value.intersection(other.value))

    def addition_operation(self: Self, other: Self) -> "Set[T]":
        return Set(self.value.union(other.value))

    def union(self: Self, *others: Self) -> "Set[T]":
        result: Set[T] = self
        for other in others:
            result += result + other
        return result

    def identity_element(self) -> "Set[T]":
        return Set()

    def copy(self) -> "Set[T]":
        return Set(self.value.copy())

    def pop(self) -> T:
        return self.value.pop()

    def add(self, x: T) -> None:
        self.value.add(x)

    def difference(self, x: Self) -> Self:
        return Set(self.value - x.value)

    def __sub__(self, x: Self) -> Self:
        return self.difference(x)

    def __iter__(self) -> Iterator[T]:
        return self.value.__iter__()

    def __len__(self) -> int:
        return len(self.value)

    def __format__(self, format_spec: str) -> str:
        return ("{:" + format_spec + "}").format(str(self))

    def __repr__(self) -> str:
        return "{}".format(self.value)

    def __eq__(self: Self, other: object) -> bool:
        if isinstance(other, Set):
            return self.value == other.value
        elif isinstance(other, set):
            return self.value == other
        return False

    def __hash__(self: Self) -> int:
        """
        A DANGEROUS thing to do, if we are using this function
        (which is done implicitly in dict keys) we need to make
        sure that the set itself doesn't change.
        """
        return hash(tuple(self.value))


class Sum(Monoid[int]):  # type: ignore[no-any-unimported, misc]
    def __init__(self, val: int = 0) -> None:
        self.value = val
        self.__iadd__ = self.__add__

    def __format__(self, format_spec: str) -> str:
        return ("{:" + format_spec + "}").format(str(self))

    def addition_operation(self: Self, other: Self | int) -> "Sum":
        if isinstance(other, int):
            return self + Sum(other)
        return Sum(self.value + other.value)

    def identity_element(self) -> "Sum":
        return Sum()

    def __repr__(self) -> str:
        return "{}".format(self.value)

    def __eq__(self: Self, other: object) -> bool:
        if isinstance(other, Sum):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)


class Product(Monoid[int]):  # type: ignore[no-any-unimported, misc]
    def __init__(self, val: int = 1) -> None:
        self.value = val
        self.__iadd__ = self.__add__

    def addition_operation(self: Self, other: Self) -> "Product":
        return Product(self.value * other.value)

    def identity_element(self) -> "Product":
        return Product(1)

    def __repr__(self) -> str:
        return "{}".format(self.value)

    def __eq__(self: Self, other: object) -> bool:
        if isinstance(other, Product):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return False
