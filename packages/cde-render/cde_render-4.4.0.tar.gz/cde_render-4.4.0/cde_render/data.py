import abc
import dataclasses
import datetime
import decimal
import functools
import itertools
import re
import sys
from collections.abc import Iterable
from typing import Any, Union

from typing_extensions import Self

from cde_render.common import (
    AgeClasses,
    CourseTrackStati,
    FieldDatatypes,
    Genders,
    Meal,
    MealDefinition,
    RegistrationPartStati,
    calculate_age,
    collate,
    compute_checkdigit,
    generate_filesafe_shortnames,
    parse_date,
    parse_datetime,
    replace_year,
)

MINIMUM_EXPORT_VERSION = [19, 0]
MAXIMUM_EXPORT_VERSION = [19, 2**62]

Sortkey = tuple[Union[str, int, datetime.datetime, datetime.date], ...]

# Base class for all following entities. Forces them to be frozen and sortable by implementing 'get_sortkey'.


@dataclasses.dataclass(kw_only=True, frozen=True)
class Entity(abc.ABC):
    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return collate(self.get_sortkey()) < collate(other.get_sortkey())

    @abc.abstractmethod
    def get_sortkey(self) -> Sortkey: ...


# The entities below (almost) all correspond to entities in the CdEDB.


@dataclasses.dataclass(kw_only=True, frozen=True)
class Event(Entity):
    id: int
    title: str
    shortname: str
    timestamp: datetime.datetime | None

    parts: list["EventPart"] = dataclasses.field(default_factory=list)
    tracks: list["EventTrack"] = dataclasses.field(default_factory=list)
    registrations: list["Registration"] = dataclasses.field(default_factory=list)
    courses: list["Course"] = dataclasses.field(default_factory=list)
    lodgement_groups: list["LodgementGroup"] = dataclasses.field(default_factory=list)
    lodgements: list["Lodgement"] = dataclasses.field(default_factory=list)

    fields: list["Field"] = dataclasses.field(default_factory=list)
    meal_definitions: list[MealDefinition] = dataclasses.field(default_factory=list)

    # Store the config here for easy access.
    config: dict[str, Any]

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.shortname})"

    def get_sortkey(self) -> Sortkey:
        return (self.id,)

    @property
    def begin(self) -> datetime.date:
        return self.parts[0].begin

    @property
    def end(self) -> datetime.date:
        return max(p.end for p in self.parts)

    @property
    def days(self) -> list[datetime.date]:
        return sorted(set().union(*(p.days for p in self.parts)))

    @functools.cached_property
    def fields_by_name(self) -> dict[str, "Field"]:
        return {f.field_name: f for f in self.fields}

    @functools.cached_property
    def parts_by_shortname(self) -> dict[str, "EventPart"]:
        return {ep.shortname: ep for ep in self.parts}

    @functools.cached_property
    def tracks_by_shortname(self) -> dict[str, "EventTrack"]:
        return {et.shortname: et for et in self.tracks}

    @functools.cached_property
    def filesafe_part_shortnames(self) -> dict["EventPart", str]:
        """Generate a filesafe suffix for each event part."""
        filesafe_shortnames = generate_filesafe_shortnames({part.id: part.shortname for part in self.parts})
        return {part: filesafe_shortnames[part.id] for part in self.parts}

    @functools.cached_property
    def filesafe_track_shortnames(self) -> dict["EventTrack", str]:
        """Generate a filesafe suffix for each event track."""
        filesafe_shortnames = generate_filesafe_shortnames({track.id: track.shortname for track in self.tracks})
        return {track: filesafe_shortnames[track.id] for track in self.tracks}

    @functools.cached_property
    def matching_registrations(self) -> list["Registration"]:
        """Read a list of patterns to match against registrations from the CLI (via a temporary config entry)."""
        ret = self.registrations
        if include_patterns := self.config.get("cli", {}).get("match_registrations", []):
            patterns = list(map(functools.partial(re.compile, flags=re.I), include_patterns))
            ret = [
                reg
                for reg in ret
                if any(
                    pattern.search(reg.name.pattern_matching_name) or pattern.search(reg.cdedbid)
                    for pattern in patterns
                )
            ]
        if exclude_patterns := self.config.get("cli", {}).get("exclude_registrations", []):
            patterns = list(map(functools.partial(re.compile, flags=re.I), exclude_patterns))
            ret = [
                reg
                for reg in ret
                if all(
                    not pattern.search(reg.name.pattern_matching_name) and not pattern.search(reg.cdedbid)
                    for pattern in patterns
                )
            ]
        return ret

    def get_active_registrations(
        self,
        parts: Iterable["EventPart"] | None = None,
        *,
        include_guests: bool = False,
        list_consent_only: bool = False,
        minors_only: bool = False,
        matching_registrations_only: bool = False,
    ) -> list["Registration"]:
        """
        Retrieve active participants of an event, possibly filtered by active parts, list_consent and age.

        :param parts:
            The event parts to check the registration for activity. If not given, all event parts are considered.
        :param include_guests:
            If true, `RegistrationPartStati.guest` is considered as acitve. Otherwise only `participant`.
        :param list_consent_only:
            If true, only registrations with list_consent == True are returned.
        :param minors_only:
            If true, only minors as defined by 'common.AgeClasses' are returned.
        :param matching_registrations_only:
            If true, only consider matching registrations (as in `Event.matching_registrations`).
        """
        if parts is None:
            parts = self.parts
        active_stati = [RegistrationPartStati.participant]
        if include_guests:
            active_stati.append(RegistrationPartStati.guest)

        return [
            r
            for r in (self.matching_registrations if matching_registrations_only else self.registrations)
            if (
                any(r.parts[part].status in active_stati for part in parts)
                and (not list_consent_only or r.list_consent)
                and (not minors_only or r.age_class.is_minor)
            )
        ]

    @classmethod
    def from_json(cls, data: dict[str, Any], config: dict[str, Any]) -> Self:
        if "kind" not in data or data["kind"] != "partial":
            raise ValueError("This script requires a 'Partial Export' from the CdEDB!")
        try:
            # Compatibility with export schema version 12 (with old version field)
            version = data.get("EVENT_SCHEMA_VERSION")
            if not version:
                version = [data["CDEDB_EXPORT_EVENT_VERSION"], 0]
        except KeyError as e:
            raise ValueError(
                "No CdEDB export version tag found. This script requires a 'Partial Export' from the CdEDB!"
            ) from e
        if not MINIMUM_EXPORT_VERSION <= version <= MAXIMUM_EXPORT_VERSION:
            raise ValueError(
                "This script requires a 'Partial Export' with version number in [{}.{},{}.{}]!".format(
                    *MINIMUM_EXPORT_VERSION, *MAXIMUM_EXPORT_VERSION
                )
            )

        event_data = data["event"]
        # TODO: Offer replacements for event data from event.fields
        #  (https://tracker.cde-ev.de/gitea/cdedb/cdedb2/issues/3992)
        event_timestamp = datetime.datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None

        event = cls(
            id=data["id"],
            title=event_data["title"],
            shortname=event_data["shortname"],
            config=config,
            timestamp=event_timestamp,
        )

        # Parse parts and tracks
        # Due to the entities being frozen we need to extend the empty default value, instead of assigning here.
        event.parts.extend(
            sorted(
                EventPart.from_json(event, part_id, part_data) for part_id, part_data in data["event"]["parts"].items()
            )
        )
        parts_by_id = {p.id: p for p in event.parts}
        event.tracks.extend(sorted(itertools.chain.from_iterable(p.tracks for p in event.parts)))
        tracks_by_id = {t.id: t for t in event.tracks}

        # Get field definitions
        event.fields.extend(
            sorted(
                Field.from_json(event, field_name, field_data)
                for field_name, field_data in data["event"]["fields"].items()
            )
        )

        # Parse meal definitions
        for meal_spec in config.get("data", {}).get("meals", []):
            if not meal_spec.get("field_name"):
                print("Meal definition is missing field name.")
                continue
            if value_map := meal_spec.get("value_map"):
                meal_spec["value_map"] = {val: key for key, val in value_map.items()}
            meal_def = MealDefinition(**meal_spec)
            if meal_def.field_name not in event.fields_by_name:
                print(f"Unknown meal field name {meal_def.field_name!r} for meal definition.")
            if meal_def.halfmeat_group_field_name and meal_def.halfmeat_group_field_name not in event.fields_by_name:
                print(f"Unknown halfmeat group field name {meal_def.halfmeat_group_field_name!r} for meal definition.")
            event.meal_definitions.append(meal_def)

        # Parse courses and course_segments
        event.courses.extend(
            sorted(
                Course.from_json(event, course_id, course_data, tracks_by_id)
                for course_id, course_data in data["courses"].items()
            )
        )
        courses_by_id = {c.id: c for c in event.courses}

        # Parse lodgement_groups
        event.lodgement_groups.extend(
            sorted(
                LodgementGroup.from_json(event, lg_id, lg_data) for lg_id, lg_data in data["lodgement_groups"].items()
            )
        )
        lodgement_groups_by_id = {lg.id: lg for lg in event.lodgement_groups}

        # Parse lodgements
        event.lodgements.extend(
            sorted(
                Lodgement.from_json(event, lodgement_id, lodgement_data, event.parts, lodgement_groups_by_id)
                for lodgement_id, lodgement_data in data["lodgements"].items()
            )
        )
        lodgements_by_id = {lodge.id: lodge for lodge in event.lodgements}
        # Add lodgements to lodgement groups
        for lodgement in event.lodgements:
            if lodgement.group:
                lodgement.group.lodgements.append(lodgement)

        # Parse registrations
        event.registrations.extend(
            sorted(
                Registration.from_json(
                    event, reg_id, reg_data, event.begin, parts_by_id, tracks_by_id, courses_by_id, lodgements_by_id
                )
                for reg_id, reg_data in data["registrations"].items()
            )
        )

        # Add registrations to the relevant lodgements and courses
        # This done after sorting of Registrations
        for registration in event.registrations:
            for part, registration_part in registration.parts.items():
                if not registration_part.status.is_present:
                    continue
                if registration_part.lodgement:
                    registration_part.lodgement.parts[part].inhabitants.append(
                        (registration, registration_part.campingmat)
                    )
            for track, registration_track in registration.tracks.items():
                if not registration_track.registration_part.status.is_present:
                    continue
                if registration_track.course and track in registration_track.course.tracks:
                    registration_track.course.tracks[track].attendees.append(
                        (registration, registration_track.instructor)
                    )

        return event


@dataclasses.dataclass(kw_only=True, frozen=True)
class EventPart(Entity):
    event: Event = dataclasses.field(compare=False)
    id: int
    title: str
    shortname: str
    begin: datetime.date
    end: datetime.date

    tracks: list["EventTrack"] = dataclasses.field(default_factory=list, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.shortname})"

    def get_sortkey(self) -> Sortkey:
        return (self.begin, self.end, self.title, self.id)

    @property
    def days(self) -> Iterable[datetime.date]:
        d = self.begin
        while d <= self.end:
            yield d
            d += datetime.timedelta(days=1)

    @classmethod
    def from_json(cls, event: Event, part_id: str, data: dict[str, Any]) -> Self:
        part = cls(
            event=event,
            id=int(part_id),
            title=data["title"],
            shortname=data["shortname"],
            begin=parse_date(data["part_begin"]),
            end=parse_date(data["part_end"]),
        )
        part.tracks.extend(sorted(EventTrack.from_json(ti, td, part) for ti, td in data["tracks"].items()))
        return part

    @property
    def filesafe_shortname(self) -> str:
        return self.event.filesafe_part_shortnames[self]

    @property
    def shortname_if_needed(self) -> str:
        return self.shortname if len(self.event.parts) > 1 else ""


@dataclasses.dataclass(kw_only=True, frozen=True)
class EventTrack(Entity):
    id: int
    part: EventPart = dataclasses.field(compare=False)
    title: str
    shortname: str
    sortkey: int
    num_choices: int
    course_room_field: str | None

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.shortname})"

    def get_sortkey(self) -> Sortkey:
        return self.part.get_sortkey() + (self.sortkey, self.shortname, self.id)

    @classmethod
    def from_json(cls, track_id: str, data: dict[str, Any], part: EventPart) -> Self:
        return cls(
            id=int(track_id),
            part=part,
            title=data["title"],
            shortname=data["shortname"],
            sortkey=data["sortkey"],
            num_choices=data["num_choices"],
            course_room_field=data["course_room_field"],
        )

    @property
    def filesafe_shortname(self) -> str:
        return self.part.event.filesafe_track_shortnames[self]


@dataclasses.dataclass(kw_only=True, frozen=True)
class Course(Entity):
    event: Event = dataclasses.field(compare=False)

    id: int
    nr: str
    title: str
    shortname: str

    fields: dict[str, Any] = dataclasses.field(default_factory=dict, compare=False)
    tracks: dict[EventTrack, "CourseTrack"] = dataclasses.field(default_factory=dict, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.nr}. {self.shortname})"

    def get_sortkey(self) -> Sortkey:
        return (self.nr, self.shortname, self.id)

    @property
    def instructors(self) -> list["Registration"]:
        return sorted(set().union(*(t.instructors for t in self.tracks.values())))

    @property
    def is_active(self) -> bool:
        return any(t.status.is_active for t in self.tracks.values())

    @property
    def active_tracks(self) -> dict[EventTrack, "CourseTrack"]:
        return {et: ct for et, ct in self.tracks.items() if ct.status.is_active}

    @classmethod
    def from_json(cls, event: Event, course_id: str, data: dict[str, Any], event_tracks: dict[int, EventTrack]) -> Self:
        # Globally replace course data from fields based on the 'data.replacements.courses' config section.
        _replace_from_datafield(
            entity_data=data,
            field_data=data["fields"],
            replacement_config=event.config.get("data", {}).get("replacements", {}).get("courses", {}),
        )
        course = cls(
            event=event, id=int(course_id), nr=data["nr"] or "", title=data["title"], shortname=data["shortname"]
        )
        for field, value in data["fields"].items():
            if field not in event.fields_by_name:
                continue
            if event.fields_by_name[field].kind == FieldDatatypes.datetime and value is not None:
                value = parse_datetime(value)
            elif event.fields_by_name[field].kind == FieldDatatypes.date and value is not None:
                value = parse_date(value)
            course.fields[field] = value
        # Add CourseTracks
        tracks = {
            event_tracks[int(ti)]: CourseTrack.from_json(td, course, event_tracks[int(ti)])
            for ti, td in data["segments"].items()
        }
        tracks.update(
            {
                track: CourseTrack(course=course, track=track, status=CourseTrackStati.not_offered)
                for track in event_tracks.values()
                if track not in tracks
            }
        )
        course.tracks.update(dict(sorted(tracks.items())))
        return course


@dataclasses.dataclass(kw_only=True, frozen=True)
class CourseTrack(Entity):
    track: EventTrack
    course: Course
    status: CourseTrackStati

    attendees: list[tuple["Registration", bool]] = dataclasses.field(default_factory=list, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(course={self.course!r}, track={self.track!r}, status={self.status.name})"

    def get_sortkey(self) -> Sortkey:
        return self.track.get_sortkey() + self.course.get_sortkey()

    @functools.cached_property
    def regular_attendees(self) -> list["Registration"]:
        return sorted(p for p, instructor in self.attendees if not instructor)

    @functools.cached_property
    def instructors(self) -> list["Registration"]:
        return sorted(p for p, instructor in self.attendees if instructor)

    @classmethod
    def from_json(cls, data: dict[str, Any], course: Course, track: EventTrack) -> Self:
        course_track = cls(
            track=track, course=course, status=CourseTrackStati.active if data else CourseTrackStati.cancelled
        )
        return course_track


@dataclasses.dataclass(kw_only=True, frozen=True)
class LodgementGroup(Entity):
    event: Event = dataclasses.field(compare=False)

    id: int
    title: str
    lodgements: list["Lodgement"] = dataclasses.field(default_factory=list, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.title})"

    def get_sortkey(self) -> Sortkey:
        return (self.title, self.id)

    @classmethod
    def from_json(cls, event: Event, lodgement_group_id: str, data: dict[str, Any]) -> Self:
        return cls(event=event, id=int(lodgement_group_id), title=data["title"])


@dataclasses.dataclass(kw_only=True, frozen=True)
class Lodgement(Entity):
    event: Event = dataclasses.field(compare=False)

    id: int
    title: str
    group: LodgementGroup

    fields: dict[str, Any] = dataclasses.field(default_factory=dict, compare=False)
    parts: dict[EventPart, "LodgementPart"] = dataclasses.field(default_factory=dict, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(group={self.group!r}, title={self.title})"

    def get_sortkey(self) -> Sortkey:
        return self.group.get_sortkey() + (self.title, self.id)

    @classmethod
    def from_json(
        cls,
        event: Event,
        lodgement_id: str,
        data: dict[str, Any],
        event_parts: list[EventPart],
        lodgement_groups: dict[int, LodgementGroup],
    ) -> Self:
        # Globally replace lodgement data from fields based on the 'data.replacements.lodgements' config section.
        _replace_from_datafield(
            entity_data=data,
            field_data=data["fields"],
            replacement_config=event.config.get("data", {}).get("replacements", {}).get("lodgements", {}),
        )
        lodgement = cls(
            event=event, id=int(lodgement_id), title=data["title"], group=lodgement_groups[data["group_id"]]
        )
        # Adding lodgements to group's list is done afterwards to fix the order
        for field, value in data["fields"].items():
            if field not in event.fields_by_name:
                continue
            if event.fields_by_name[field].kind == FieldDatatypes.datetime and value is not None:
                value = parse_datetime(value)
            elif event.fields_by_name[field].kind == FieldDatatypes.date and value is not None:
                value = parse_date(value)
            lodgement.fields[field] = value
        for part in event_parts:
            lodgement_part = LodgementPart(lodgement=lodgement, part=part)
            lodgement.parts[part] = lodgement_part
        return lodgement


@dataclasses.dataclass(kw_only=True, frozen=True)
class LodgementPart(Entity):
    part: EventPart
    lodgement: Lodgement
    inhabitants: list[tuple["Registration", bool]] = dataclasses.field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(lodgement={self.lodgement!r}, part={self.part!r})"

    def get_sortkey(self) -> Sortkey:
        return self.lodgement.get_sortkey() + self.part.get_sortkey()

    @functools.cached_property
    def regular_inhabitants(self) -> list["Registration"]:
        return sorted(p for p, campingmat in self.inhabitants if not campingmat)

    @functools.cached_property
    def campingmat_inhabitants(self) -> list["Registration"]:
        return sorted(p for p, campingmat in self.inhabitants if campingmat)


@dataclasses.dataclass(kw_only=True, frozen=True)
class Registration(Entity):
    event: Event = dataclasses.field(compare=False)
    id: int
    persona_id: int
    name: "Name"
    gender: Genders
    birthday: datetime.date
    age: int
    email: str
    telephone: str
    mobile: str
    address: "Address"
    payment: "Payment"
    list_consent: bool
    is_orga: bool
    ctime: datetime.datetime
    tracks: dict[EventTrack, "RegistrationTrack"] = dataclasses.field(default_factory=dict, compare=False)
    parts: dict[EventPart, "RegistrationPart"] = dataclasses.field(default_factory=dict, compare=False)
    fields: dict[str, Any] = dataclasses.field(default_factory=dict, compare=False)
    checkin_periods: list["CheckinPeriod"] = dataclasses.field(default_factory=list, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(name={self.name!r}, id={self.id})"

    def get_sortkey(self) -> Sortkey:
        return (self.name.common, self.id)

    @property
    def is_present(self) -> bool:
        return any(p.status.is_present for p in self.parts.values())

    @property
    def is_participant(self) -> bool:
        return any(p.status == RegistrationPartStati.participant for p in self.parts.values())

    @property
    def present_parts(self) -> list["RegistrationPart"]:
        result = [p for p in self.parts.values() if p.status.is_present]
        result.sort(key=(lambda p: p.part.begin))
        return result

    @property
    def participant_parts(self) -> list["RegistrationPart"]:
        result = [p for p in self.parts.values() if p.status == RegistrationPartStati.participant]
        result.sort(key=(lambda p: p.part.begin))
        return result

    def was_present_at(self, timestamp: datetime.datetime) -> bool:
        return any(timestamp in period for period in self.checkin_periods)

    @property
    def age_class(self) -> AgeClasses:
        if self.age >= 18:
            return AgeClasses.full
        if self.age >= 16:
            return AgeClasses.u18
        if self.age >= 14:
            return AgeClasses.u16
        if self.age >= 10:
            return AgeClasses.u14
        return AgeClasses.u10

    @property
    def cdedbid(self) -> str:
        return f"DB-{self.persona_id}-{compute_checkdigit(self.persona_id)}"

    @property
    def first_checkin(self) -> datetime.datetime | None:
        if self.checkin_periods:
            return self.checkin_periods[0].checkin
        return None

    @property
    def last_checkout(self) -> datetime.datetime | None:
        if self.checkin_periods and self.checkin_periods[-1].checkout:
            return self.checkin_periods[-1].checkout
        return None

    @functools.cached_property
    def event_birthdays(self) -> list[datetime.date]:
        return sorted(set().union(*(rp.event_birthdays for rp in self.parts.values())))

    @functools.cached_property
    def meals(self) -> list[Meal]:
        return [meal_def.evaluate(self) for meal_def in self.event.meal_definitions]

    @classmethod
    def from_json(
        cls,
        event: Event,
        reg_id: str,
        data: dict[str, Any],
        event_begin: datetime.date,
        event_parts: dict[int, EventPart],
        event_tracks: dict[int, EventTrack],
        courses: dict[int, Course],
        lodgements: dict[int, Lodgement],
    ) -> Self:
        persona = data["persona"]
        # Globally replace registration data from fields based on the 'data.replacements.registrations' config section.
        _replace_from_datafield(
            entity_data=data,
            field_data=data["fields"],
            replacement_config=event.config.get("data", {}).get("replacements", {}).get("registrations", {}),
        )
        _replace_from_datafield(
            entity_data=persona,
            field_data=data["fields"],
            replacement_config=event.config.get("data", {}).get("replacements", {}).get("registrations", {}),
        )
        birthday = parse_date(persona["birthday"])
        registration = cls(
            event=event,
            id=int(reg_id),
            persona_id=persona["id"],
            name=Name.from_json_persona(persona),
            address=Address.from_json_persona(persona),
            payment=Payment.from_json(data),
            birthday=birthday,
            age=calculate_age(event_begin, birthday),
            gender=Genders(persona["gender"]),
            email=persona["username"],
            telephone=persona["telephone"],
            mobile=persona["mobile"],
            list_consent=data["list_consent"],
            is_orga=persona["is_orga"],
            ctime=datetime.datetime.fromisoformat(data["ctime"]),
        )

        for field, value in data["fields"].items():
            if field not in event.fields_by_name:
                continue
            if event.fields_by_name[field].kind == FieldDatatypes.datetime and value is not None:
                value = parse_datetime(value)
            elif event.fields_by_name[field].kind == FieldDatatypes.date and value is not None:
                value = parse_date(value)
            registration.fields[field] = value

        registration.parts.update(
            {
                event_parts[int(pi)]: RegistrationPart.from_json(pd, registration, event_parts[int(pi)], lodgements)
                for pi, pd in data["parts"].items()
            }
        )

        registration.tracks.update(
            {
                event_tracks[int(ti)]: RegistrationTrack.from_json(td, registration, event_tracks[int(ti)], courses)
                for ti, td in data["tracks"].items()
            }
        )
        for part in event_parts.values():
            if part not in registration.parts:
                registration.parts[part] = RegistrationPart(registration=registration, part=part)
            for track in part.tracks:
                if track not in registration.tracks:
                    registration.tracks[track] = RegistrationTrack(
                        registration=registration,
                        registration_part=registration.parts[part],
                        track=track,
                        choices=[None] * track.num_choices,
                    )

        registration.checkin_periods.extend(
            sorted(CheckinPeriod.from_json(period, registration) for period in data["checkin_periods"])
        )
        return registration


@dataclasses.dataclass(kw_only=True, frozen=True)
class Name(Entity):
    """This follows the conventions described by https://db.cde-ev.de/doc/Design_UX_Conventions.html"""

    given_names: str
    family_name: str
    nickname: str = ""  # Used in first line of nametag and in parentheses behind given names otherwise. Optional.

    # The following are all only used in legal contexts, via the 'legal' property.
    title: str = ""  # Placed in front of the actual name (like 'Dr.', 'Prof.' etc). Optional.
    legal_given_names: str = ""  # All given names to be used in a legal context. Optional.
    name_supplement: str = ""  # Like title, but behind the actual name. Optional.

    pronouns: str = ""  # Optional.
    pronouns_nametag: bool = False  # Whether to display the pronouns on the nametag.

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.common})"

    def get_sortkey(self) -> Sortkey:
        return (self.common,)

    @property
    def common(self) -> str:
        """This should be the default for the event context, where the nickname should be taken into consideration.

        Corresponds to `util.persona_name(persona, include_nickname=True)` in the CdEDB.
        """
        return f"{self.common_forename} {self.common_surname}"

    @property
    def common_forename(self) -> str:
        """This should be the default for the event context."""
        if self.nickname:
            forename = f"{self.given_names} ({self.nickname})"
        else:
            forename = self.given_names
        return forename

    @property
    def common_surname(self) -> str:
        """This should be the default for the event context."""
        return self.family_name

    @property
    def persona_name(self) -> str:
        """This is the default outside of the event context, where the nickname ist not taken into consideration.

        Corresponds to `util.persona_name(persona)` in the CdEDB.
        """
        return f"{self.persona_forename} {self.persona_surname}"

    @property
    def persona_forename(self) -> str:
        """This is the default outside of the event context."""
        return self.given_names

    @property
    def persona_surname(self) -> str:
        """This is the default outside of the event context."""
        return self.family_name

    @property
    def salutation(self) -> str:
        """This should be used when a user is directly addressed (saluted)."""
        return self.given_names

    @property
    def legal(self) -> str:
        """This should be used whenever the user is addressed in a legal context."""
        return (
            f"{self.title or ''} {self.legal_given_names or self.given_names} {self.family_name}"
            f" {self.name_supplement or ''}"
        ).strip()

    @property
    def nametag_forename(self) -> str:
        """This should be used on nametags only."""
        return self.nickname or self.given_names

    @property
    def nametag_surname(self) -> str:
        """This should be used on nametags only."""
        return f"{self.given_names if self.nickname else ''} {self.family_name}".strip()

    @property
    def nametag_pronouns(self) -> str:
        """This should be used on nametags only."""
        return self.pronouns if self.pronouns_nametag else ""

    @property
    def list_forename(self) -> str:
        """This should be used on lists only."""
        return self.common_forename

    @property
    def list_surname(self) -> str:
        """This should be used on lists only."""
        return self.common_surname

    @property
    def pattern_matching_name(self) -> str:
        """Used to pattern match against."""
        if self.nickname:
            return f"{self.persona_name};{self.common};{self.nickname} {self.common_surname}"
        return self.common

    @classmethod
    def from_json_persona(cls, data: dict[str, Any]) -> Self:
        return cls(
            given_names=data["given_names"],
            family_name=data["family_name"],
            nickname=data["nickname"],
            title=data["title"],
            legal_given_names=data["legal_given_names"],
            name_supplement=data["name_supplement"],
            pronouns=data["pronouns"],
            pronouns_nametag=data["pronouns_nametag"],
        )


@dataclasses.dataclass(kw_only=True, frozen=True)
class Address(Entity):
    address: str
    address_supplement: str
    postal_code: str
    location: str
    country: str

    def __repr__(self) -> str:
        inline_address = self.full_address.replace("\n", ", ")
        return f"{self.__class__.__qualname__}({inline_address})"

    def get_sortkey(self) -> Sortkey:
        return (0,)

    @property
    def full_address(self) -> str:
        res = ""
        if self.address:
            res += self.address + "\n"
        if self.address_supplement:
            res += self.address_supplement + "\n"
        if self.postal_code:
            res += self.postal_code + " "
        if self.location:
            res += self.location
        if self.country and self.country not in ("Germany", "Deutschland", "DE"):
            res += "\n" + self.country
        return res

    @classmethod
    def from_json_persona(cls, data: dict[str, Any]) -> Self:
        return cls(
            address=data["address"],
            address_supplement=data["address_supplement"],
            postal_code=data["postal_code"],
            location=data["location"],
            country=data["country"],
        )


@dataclasses.dataclass(kw_only=True, frozen=True)
class Payment(Entity):
    date: datetime.date | None
    paid: decimal.Decimal
    owed: decimal.Decimal

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(date={self.date}, paid={self.paid}, owed={self.owed})"

    def get_sortkey(self) -> Sortkey:
        return (0,)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        return cls(
            date=parse_date(data["payment"]) if data["payment"] else None,
            paid=decimal.Decimal(data["amount_paid"]),
            owed=decimal.Decimal(data["amount_owed"]),
        )


@dataclasses.dataclass(kw_only=True, frozen=True)
class RegistrationPart(Entity):
    registration: Registration
    part: EventPart
    status: RegistrationPartStati = RegistrationPartStati.not_applied
    lodgement: Lodgement | None = None
    campingmat: bool = False

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(registration={self.registration!r}, part={self.part!r})"

    def get_sortkey(self) -> Sortkey:
        return self.registration.get_sortkey() + self.part.get_sortkey()

    @functools.cached_property
    def event_birthdays(self) -> list[datetime.date]:
        return [
            adjusted_birthday
            for year in range(self.part.begin.year, self.part.end.year + 1)
            if self.part.begin <= (adjusted_birthday := replace_year(self.registration.birthday, year)) <= self.part.end
            and self.status.is_present
        ]

    @classmethod
    def from_json(
        cls, data: dict[str, Any], registration: Registration, part: EventPart, lodgements: dict[int, Lodgement]
    ) -> Self:
        # Adding the registration to the lodgement's registration list is done later.
        return cls(
            registration=registration,
            part=part,
            status=RegistrationPartStati(data["status"]),
            lodgement=lodgements.get(data["lodgement_id"]),
            campingmat=data["is_camping_mat"],
        )


@dataclasses.dataclass(kw_only=True, frozen=True)
class RegistrationTrack(Entity):
    registration: Registration
    registration_part: RegistrationPart
    track: EventTrack
    course: Course | None = None
    offered_course: Course | None = None
    choices: list[Course | None] = dataclasses.field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(registration={self.registration!r}, track={self.track!r})"

    def get_sortkey(self) -> Sortkey:
        return self.registration.get_sortkey() + self.track.get_sortkey()

    @property
    def instructor(self) -> bool:
        return self.offered_course is not None and self.offered_course == self.course

    @classmethod
    def from_json(
        cls, data: dict[str, Any], registration: Registration, track: EventTrack, courses: dict[int, Course]
    ) -> Self:
        # Adding the registration to the courses' attendee list is done later.
        return cls(
            registration=registration,
            registration_part=registration.parts[track.part],
            track=track,
            course=courses.get(data["course_id"]),
            offered_course=courses.get(data["course_instructor"]),
            choices=[courses[choice] for choice in data["choices"]],
        )


@dataclasses.dataclass(kw_only=True, frozen=True)
class Field(Entity):
    event: Event = dataclasses.field(compare=False)
    field_name: str
    title: str
    sort_group: str
    sortkey: int
    kind: FieldDatatypes
    association: int
    entries: dict[Any, str] | None = dataclasses.field(default_factory=dict)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.title}, kind={self.kind.name})"

    def get_sortkey(self) -> Sortkey:
        return (
            self.sort_group or chr(sys.maxunicode),  # Sort empty group last.
            self.sortkey,
            self.title,
            self.field_name,
        )

    @classmethod
    def from_json(cls, event: Event, field_name: str, data: dict[str, Any]) -> Self:
        try:
            datatype = FieldDatatypes(data["kind"])
        except ValueError as e:
            print(f"Warning: Unknown field datatype for field {field_name!r}, defaulting to 'str'.: {e}")
            datatype = FieldDatatypes.str
        field = cls(
            event=event,
            field_name=field_name,
            title=data["title"],
            sort_group=data["sort_group"],
            sortkey=int(data["sortkey"]),
            kind=datatype,
            association=data["association"],
            entries=dict(data["entries"]) if data["entries"] else None,
        )
        return field


@dataclasses.dataclass(kw_only=True, frozen=True)
class CheckinPeriod(Entity):
    registration: Registration
    checkin: datetime.datetime
    checkout: datetime.datetime | None

    def __repr__(self) -> str:
        checkoutstr = self.checkout.isoformat() if self.checkout else "*now*"
        return f"{self.__class__.__qualname__}({self.checkin.isoformat()} – {checkoutstr})"

    def get_sortkey(self) -> Sortkey:
        return (self.checkin, self.checkout or datetime.datetime.max)

    def __contains__(self, timestamp: datetime.datetime) -> bool:
        if not isinstance(timestamp, datetime.datetime):
            return NotImplemented  # type: ignore[unreachable]
        if self.checkout:
            return self.checkin <= timestamp <= self.checkout
        return self.checkin <= timestamp

    @classmethod
    def from_json(cls, data: dict[str, Any], registration: Registration) -> Self:
        return cls(
            registration=registration,
            checkin=datetime.datetime.fromisoformat(data["checkin_time"]),
            checkout=datetime.datetime.fromisoformat(data["checkout_time"]) if data.get("checkout_time") else None,
        )


def _replace_from_datafield(
    entity_data: dict[str, Any], field_data: dict[str, Any], replacement_config: dict[str, str]
) -> None:
    for key, original_value in entity_data.items():
        value = original_value
        if not isinstance(original_value, dict | list):
            if replacement_field_name := replacement_config.get(key):
                replacement_value = field_data.get(replacement_field_name)
                if replacement_value is not None:
                    value = replacement_value
        entity_data[key] = value
