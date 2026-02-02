import abc
import collections
import dataclasses
import random
from collections.abc import Collection, ItemsView
from typing import ClassVar

from typing_extensions import Self

from .data import EventPart, Registration
from .render import RenderTarget


@dataclasses.dataclass
class Puzzles:
    _by_registration_by_part: dict[Registration, list["NametagPuzzle"]]

    def get(self, registration: Registration, part: EventPart | None = None) -> list["NametagPuzzle"]:
        puzzles = self._by_registration_by_part.get(registration, [])
        if part:
            puzzles = [puzzle for puzzle in puzzles if part in puzzle.parts]
        return puzzles

    def filter(self, *, registrations: Collection[Registration] | None = None, part: EventPart | None = None) -> Self:
        registrations = set(registrations or ()) or None
        return self.__class__(
            {
                registration: [puzzle for puzzle in puzzles if part is None or part in puzzle.parts]
                for registration, puzzles in self._by_registration_by_part.items()
                if registrations is None or registration in registrations
            }
        )

    def items(self) -> ItemsView[Registration, list["NametagPuzzle"]]:
        return self._by_registration_by_part.items()

    def stats(self) -> "PuzzleStats":
        return PuzzleStats.from_puzzles(self)


@dataclasses.dataclass
class PuzzleStats:
    frequency: collections.Counter[type["NametagPuzzle"]]
    frequency_by_part: dict[EventPart, collections.Counter[type["NametagPuzzle"]]]
    distribution: collections.Counter[int]
    distribution_by_part: dict[EventPart, collections.Counter[int]]

    @classmethod
    def from_puzzles(cls, puzzles: Puzzles) -> Self:
        frequency_total: collections.Counter[type[NametagPuzzle]] = collections.Counter()
        frequency_by_part: dict[EventPart, collections.Counter[type[NametagPuzzle]]] = {}

        distribution_total: collections.Counter[int] = collections.Counter()
        distribution_by_part: dict[EventPart, collections.Counter[int]] = {}

        for registration, reg_puzzles in puzzles.items():
            frequency_total.update(puzzle.__class__ for puzzle in reg_puzzles)
            distribution_total[len(reg_puzzles)] += 1

            for event_part in registration.parts:
                part_puzzles = puzzles.get(registration, event_part)

                frequency_by_part.setdefault(event_part, collections.Counter()).update(
                    puzzle.__class__ for puzzle in part_puzzles
                )

                distribution_by_part.setdefault(event_part, collections.Counter())[len(part_puzzles)] += 1

        return cls(frequency_total, frequency_by_part, distribution_total, distribution_by_part)


@dataclasses.dataclass
class NametagPuzzle(abc.ABC):
    display_name: ClassVar[str]
    description: ClassVar[str] = ""
    asset_name: ClassVar[str] = ""

    disabled: ClassVar[bool] = False

    _all_puzzle_classes: ClassVar[list[type[Self]]] = []

    target: RenderTarget
    registration: Registration
    parts: set[EventPart]

    @classmethod
    def get_asset_name(cls) -> str:
        return cls.asset_name or cls.display_name

    @classmethod
    def get_all_puzzle_classes(cls) -> list[type[Self]]:
        return cls._all_puzzle_classes

    @classmethod
    def refresh_global_puzzle_classes(cls) -> None:
        all_puzzles = []

        def extend(puzzle_class: type[Self]) -> None:
            for subclass in puzzle_class.__subclasses__():
                if subclass.disabled:
                    continue
                if not subclass.__subclasses__():
                    all_puzzles.append(subclass)
                extend(subclass)

        extend(cls)
        cls._all_puzzle_classes = all_puzzles

    @classmethod
    def check_all(cls, target: RenderTarget, registrations: Collection[Registration]) -> Puzzles:
        puzzle_classes = cls.get_all_puzzle_classes()

        randomize = target.config.get("nametags", {}).get("puzzles", {}).get("randomize")
        if randomize == "once":
            random.shuffle(puzzle_classes)

        puzzle_data: dict[Registration, list[NametagPuzzle]] = {}
        for registration in registrations:
            puzzle_data[registration] = []
            for puzzle_class in puzzle_classes:
                if puzzle := puzzle_class.check(target, registration):
                    puzzle_data[registration].append(puzzle)

            if randomize == "all":
                random.shuffle(puzzle_classes)

        return Puzzles(puzzle_data)

    @classmethod
    @abc.abstractmethod
    def check(cls, target: RenderTarget, registration: Registration) -> Self | None: ...


_ALL_PUZZLE_CLASSES: list[type[NametagPuzzle]] = []


def set_global_puzzle_subclasses() -> None:
    _ALL_PUZZLE_CLASSES.clear()

    def extend(puzzle_class: type[NametagPuzzle]) -> None:
        for subclass in puzzle_class.__subclasses__():
            if subclass.disabled:
                continue
            if not subclass.__subclasses__():
                _ALL_PUZZLE_CLASSES.append(subclass)
            extend(subclass)

    extend(NametagPuzzle)  # type: ignore[type-abstract]
