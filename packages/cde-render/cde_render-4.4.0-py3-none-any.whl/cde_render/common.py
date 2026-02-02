"""
This module contains helper functions uses throughout this package.

In contrast to the 'util' these are not meant to be used from the templates, except for the enums.

Also they are used _by_ the 'data' module, so they _must not_ use the classes defined there.
"""

import dataclasses
import datetime
import enum
import shutil
import textwrap
from collections.abc import Iterable
from typing import TYPE_CHECKING, TypeVar, cast

import phonenumbers

if TYPE_CHECKING:
    from cde_render.data import Registration

NOTO_EMOJI_FONT_URL = "https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji.ttf"


# According to https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words but we allow dots.
FILENAME_SANITIZE_MAP = str.maketrans({x: "_" for x in '/\\?%*:|"<> '})


def sanitize_filename(name: str) -> str:
    """
    Helper function to sanitize filenames (strip forbidden and problematic characters).

    :param name: The unsafe name
    :return: A sanitized version of the name to be used as filename
    """
    return name.translate(FILENAME_SANITIZE_MAP)


def generate_filesafe_shortnames(data: dict[int, str]) -> dict[int, str]:
    """Generate a filesafe shortname for each element of the given id to shortname mapping.

    It uses sanitize_filename() to transform each shortname into a filesafe suffix.
    Afterwards, it appends the corresponding id to all ambiguous names, if any.

    It returns a mapping of ids to filesafe suffixes.
    """
    result = {id_: sanitize_filename(shortname) for id_, shortname in data.items()}

    # Find ambiguous suffixes
    reverse_result: dict[str, int] = {}
    ambiguous_ids = set()
    for id_, suffix in result.items():
        if suffix in reverse_result:
            ambiguous_ids.add(reverse_result[suffix])
            ambiguous_ids.add(id_)
        reverse_result[suffix] = id_

    # Add part id to parts with ambiguous suffix
    for id_ in ambiguous_ids:
        result[id_] += f"_{id_}"

    return result


def format_target_description(
    name: str, description: str, *, subtargets: list[str] | None = None, max_name_length: int
) -> str:
    """Format a description for the given name to nicely fit the terminals width."""
    terminal_width = shutil.get_terminal_size().columns - 2
    indent = " " * (max_name_length + 3)
    ret = textwrap.fill(
        f"{name:<{max_name_length}} : {description}",
        subsequent_indent=indent + " " * 2,
        width=terminal_width,
    )
    if subtargets:
        ret += (
            "\n"
            + textwrap.fill(
                f"[{', '.join(subtargets)}]",
                initial_indent=indent + " " * 2,
                subsequent_indent=indent + " " * 3,
                width=terminal_width,
            )
            + "\n"
        )
    return ret


def parse_date(value: str) -> datetime.date:
    return datetime.datetime.strptime(value, "%Y-%m-%d").date()


def parse_datetime(value: str) -> datetime.datetime:
    return datetime.datetime.strptime(value.replace(":", ""), "%Y-%m-%dT%H%M%S%z")


def calculate_age(reference: datetime.date, born: datetime.date) -> int:
    """Calculate age on a reference date based on birthday.

    Source: https://stackoverflow.com/a/9754466
    """
    return reference.year - born.year - ((reference.month, reference.day) < (born.month, born.day))


class MealType(enum.Enum):
    meat = enum.auto()
    vegetarian = enum.auto()
    vegan = enum.auto()
    special = enum.auto()
    halfmeat1 = enum.auto()
    halfmeat2 = enum.auto()


@dataclasses.dataclass(kw_only=True, frozen=True)
class MealDefinition:
    field_name: str
    halfmeat_group_field_name: str | None = None
    value_map: dict[str, str] = dataclasses.field(default_factory=dict)
    asset_suffix: str = ""

    def evaluate(self, registration: "Registration") -> "Meal":
        meal_value = registration.fields.get(self.field_name)
        if meal_value is None:
            return Meal(definition=self, meal_type=None, meal_value=None)
        meal_type = None
        if meal_type_str := self.value_map.get(meal_value):
            if meal_type_str == "halfmeat":
                meal_type = MealType.halfmeat1
                if self.halfmeat_group_field_name and registration.fields.get(self.halfmeat_group_field_name):
                    meal_type = MealType.halfmeat2
            else:
                meal_type = MealType[meal_type_str]
        return Meal(definition=self, meal_type=meal_type, meal_value=meal_value)


@dataclasses.dataclass(kw_only=True, frozen=True)
class Meal:
    definition: MealDefinition
    meal_type: MealType | None
    meal_value: str | None

    @property
    def asset_name(self) -> str | None:
        if self.meal_type or self.meal_value:
            return f"meal_{self.meal_type.name if self.meal_type else self.meal_value}{self.definition.asset_suffix}"
        return None


# The functions and classes below are copied almost verbatim from the CdEDB.
#  The enums are generally from 'cdedb.database.constants'.


class Genders(enum.IntEnum):
    """CdEDB spec for a personas gender."""

    female = 1  #:
    male = 2  #:
    #: this is a catch-all for complicated reality
    other = 10
    not_specified = 20  #:


class RegistrationPartStati(enum.IntEnum):
    """CdEDB spec for a registrations status in a part."""

    not_applied = -1  #:
    applied = 1  #:
    participant = 2  #:
    waitlist = 3  #:
    guest = 4  #:
    cancelled = 5  #:
    rejected = 6  #:

    @property
    def is_involved(self) -> bool:
        """Any status which warrants further attention by the orgas."""
        return self in (
            RegistrationPartStati.applied,
            RegistrationPartStati.participant,
            RegistrationPartStati.waitlist,
            RegistrationPartStati.guest,
        )

    @property
    def is_present(self) -> bool:
        return self in (
            RegistrationPartStati.participant,
            RegistrationPartStati.guest,
        )


class FieldDatatypes(enum.IntEnum):
    """CdEDB spec for the datatypes available for custom data fields."""

    str = 1  #:
    bool = 2  #:
    int = 3  #:
    float = 4  #:
    date = 5  #:
    datetime = 6  #:
    non_negative_int = 10  #:
    non_negative_float = 12  #:
    phone = 20  #:
    iban = 30  #:


@enum.unique
class AgeClasses(enum.IntEnum):
    """CdEDB abstraction for encapsulating properties based on age."""

    full = 1  #: at least 18 years old
    u18 = 2  #: between 16 and 18 years old
    u16 = 3  #: between 14 and 16 years old
    u14 = 4  #: less than 14 years old
    u10 = 5  #: less than 10 years old, accompanied by parents.

    @property
    def is_minor(self) -> bool:
        """Checks whether a legal guardian is required."""
        return self in {AgeClasses.u14, AgeClasses.u16, AgeClasses.u18}

    @property
    def is_full(self) -> bool:
        """Checks whether a person is of age."""
        return self == AgeClasses.full


class CourseTrackStati(enum.IntEnum):
    """Variation of the CdEDB spec for a courses status in a track."""

    not_offered = -1  #: In the CdEDB this is represented by a missing entry in the 'course_segments' table.
    cancelled = 1  #: Corresponds to 'course_segments.is_active == False'.
    active = 2  #: Corresponds to 'course_segments.is_active == True'.

    @property
    def is_active(self) -> bool:
        return self == CourseTrackStati.active


ALL_ENUMS = (Genders, RegistrationPartStati, CourseTrackStati, FieldDatatypes, AgeClasses)


def compute_checkdigit(value: int) -> str:
    """Map an integer to the checksum used for UI purposes.

    This checkdigit allows for error detection if somebody messes up a
    handwritten ID or such.

    Most of the time, the integer will be a persona id.
    """
    digits = []
    tmp = value
    while tmp > 0:
        digits.append(tmp % 10)
        tmp //= 10
    dsum = sum((i + 2) * d for i, d in enumerate(digits))
    return "0123456789X"[-dsum % 11]


def replace_year(date: datetime.date, year: int) -> datetime.date:
    """Convenience function to go back in time.

    Dates are nasty, in theory this should be a simple replacement, but leap years create problems.
    """
    try:
        return date.replace(year=year)
    except ValueError:
        # This can happen in only one situation: we tried to move a leap day into a year without leap.
        if not (date.month == 2 and date.day == 29):
            raise
        return date.replace(year=year, day=28)


def phone_filter(val: str | None) -> str | None:
    """Custom jinja filter to format phone numbers."""
    if val is None:
        return None

    try:
        # default to german if no region is provided
        phone = phonenumbers.parse(val, region="DE")
    except phonenumbers.NumberParseException:
        # default to the raw value if it can not be parsed
        return val

    return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)


try:
    import icu as _icu  # type: ignore[import-untyped, import-not-found, unused-ignore]
except ImportError:

    def _collate(x: str) -> str:
        return x.casefold()

    COLLATING = False
else:
    _collate = _icu.Collator.createInstance(_icu.Locale("de-u-kn-true")).getSortKey
    del _icu
    COLLATING = True


T = TypeVar("T")


def collate(sortkey: T) -> T:
    """Adjust strings to be sorted naturally.

    For details see 'cdedb.common.sorting.collate'.
    """
    if isinstance(sortkey, str):
        return cast(T, _collate(sortkey))
    if isinstance(sortkey, Iterable):
        return cast(T, tuple(map(collate, sortkey)))
    return sortkey
