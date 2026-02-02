"""
This module contains classes and helpers that are commonly used by the template renderer but do not directly correspond
to anything represented in the CdEDB.

Some of these entities directly depend on some entries of the config.
"""

import abc
import dataclasses
import datetime
import json
import pathlib
import warnings
from collections.abc import Iterable
from typing import Any, ClassVar

import requests
from typing_extensions import Self

from cde_render.data import CourseTrack, Entity, Event, EventPart, Lodgement, Registration, RegistrationPart, Sortkey

OFFLINE_APITOKEN = "CdEDB-static/quick_partial_export/y1f2i3d4x5b6/"


def get_event_data(config: dict[str, Any], input_file: pathlib.Path | None, custom_dir: pathlib.Path) -> "Event | None":
    if input_file is None:
        if not config.get("api", {}).get("token_file") and not config.get("api", {}).get("offline_host"):
            print("Incorrect API-configuration. Please adjust config file.")
            return None

        url = "https://{host}/db/event/event/droid/export"
        host = "db.cde-ev.de"
        verify_ssl: bool | str = True
        apitoken = None

        if token_path := config["api"].get("token_file"):
            token_path = (custom_dir / config["api"]["token_file"]).resolve()
            try:
                apitoken = token_path.read_text("utf-8").strip()
            except FileNotFoundError:
                print(f"API-Token file '{token_path!s}' not found. Consider running this script with '--setup'.")
                return None
            if not apitoken:
                print(f"Empty API-Token file '{token_path!s}'.")
                return None

        if offline_host := config["api"].get("offline_host"):
            verify_ssl = (pathlib.Path(__file__).parent.parent / "misc" / "cdedb-self-signed.pem").as_posix()
            host = offline_host
            if apitoken is None:
                url = "https://{host}/db/event/offline/partial"
                apitoken = OFFLINE_APITOKEN

        if apitoken is None:
            print("Incorrect API configuration. Please adjust config file.")
            return None

        print("Reading data from Orga-API. This might take a second or two…")
        try:
            response = requests.get(url.format(host=host), headers={"X-CdEDB-API-Token": apitoken}, verify=verify_ssl)
            response.raise_for_status()
        except requests.HTTPError as e:
            print(f"HTTPError during API-Request: {e}.")
            return None

        event_data = response.json()
    else:
        try:
            event_data = json.loads(input_file.read_text("utf-8"))
        except (FileNotFoundError, IsADirectoryError):
            print(f"Input file {input_file!r} not found.")
            return None

    event = Event.from_json(event_data, config)
    print(
        f"Parsed event data with {len(event.registrations)} registrations, {len(event.courses)} courses and"
        f" {len(event.lodgements)} lodgements in {len(event.parts)} event parts and {len(event.tracks)}"
        f" course tracks."
    )
    return event


@dataclasses.dataclass(kw_only=True, frozen=True)
class Room(Entity):
    name: str

    lodgement: Lodgement | None
    course_tracks: list[CourseTrack] = dataclasses.field(default_factory=list, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.name!r})"

    def get_sortkey(self) -> Sortkey:
        return (self.name,)

    @classmethod
    def from_event(cls, event: Event, config: dict[str, Any]) -> list["Room"]:
        rooms = []

        course_room_delimiter = str(config.get("room_lists", {}).get("course_room_delimiter", ""))

        for lodgement in event.lodgements:
            rooms.append(Room(name=lodgement.title, lodgement=lodgement))

        rooms_by_name = {room.name: room for room in rooms}

        if len(rooms_by_name) != len(rooms):
            print("Warning: Duplicate lodgement name. Course rooms will match a random matching lodgement.")

        def add_course_to_room(course_track: CourseTrack, room_name: str) -> None:
            if room_name not in rooms_by_name:
                rooms_by_name[room_name] = room = Room(name=room_name, lodgement=None)
                rooms.append(room)
            rooms_by_name[room_name].course_tracks.append(course_track)

        for course in event.courses:
            for active_track in course.active_tracks.values():
                if course_room := str(course.fields.get(active_track.track.course_room_field or "", "")):
                    if course_room_delimiter:
                        # noinspection PyUnboundLocalVariable
                        for single_room in course_room.split(course_room_delimiter):
                            if not single_room.strip():
                                continue
                            add_course_to_room(active_track, single_room)
                    else:
                        add_course_to_room(active_track, course_room)

        for room in rooms:
            room.course_tracks.sort()
        return sorted(rooms)


@dataclasses.dataclass(kw_only=True, frozen=True)
class _ParticipantTransportInfo(Entity, abc.ABC):
    registration: Registration
    event_part: EventPart

    transport_values: dict[str, str]
    config: dict[str, Any]

    time: datetime.datetime | None
    transport: str | None
    comment: str
    bus: str | None

    default_time: ClassVar[datetime.datetime] = datetime.datetime(3000, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    def __repr__(self) -> str:
        time = "-missing-" if not self.time or self.time_is_missing else self.time.isoformat()
        return f"{self.__class__.__qualname__}({self.registration!r}, {time} ({self.transport!r})"

    @property
    def part(self) -> RegistrationPart:
        return self.registration.parts[self.event_part]

    @property
    def is_present(self) -> bool:
        return self.part.status.is_present

    @property
    def is_train(self) -> bool:
        # If transport is None, assume it to be train.
        return self.transport is None or self.transport == self.transport_values.get("train")

    @property
    def is_car(self) -> bool:
        return self.transport is not None and self.transport == self.transport_values.get("car")

    @property
    def is_stay(self) -> bool:
        return self.transport is not None and self.transport == self.transport_values.get("stay")

    @property
    def is_misc(self) -> bool:
        return self.transport is not None and self.transport == self.transport_values.get("misc")

    @property
    def time_is_missing(self) -> bool:
        return self.time is not None and self.time == self.default_time

    def check_include(self, target: str) -> bool:
        if not self.is_present:
            return False

        if self.config.get(f"{target}_exclude_car") and self.is_car:
            return False

        if self.config.get(f"{target}_exclude_stay") and self.is_stay:
            return False

        return True

    @classmethod
    def from_registration(
        cls,
        registration: Registration,
        event_part: EventPart,
        transport_values: dict[str, str],
        part_config: dict[str, Any],
    ) -> Self:
        time_field = part_config.get("time_field")
        time = (registration.fields.get(time_field) or cls.default_time) if time_field else None
        time = time.replace(second=0, microsecond=0) if time else None

        transport_field = part_config.get("transport_field")
        transport = (registration.fields.get(transport_field) or "") if transport_field else None

        comment_field = part_config.get("comment_field")
        comment = registration.fields.get(comment_field or "") or ""

        bus_field = part_config.get("bus_field")
        bus = (registration.fields.get(bus_field) or "") if bus_field else None
        return cls(
            registration=registration,
            event_part=event_part,
            transport_values=transport_values,
            config=part_config,
            time=time,
            transport=transport,
            comment=comment,
            bus=bus,
        )


@dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
class ParticipantArrivalInfo(_ParticipantTransportInfo):
    def get_sortkey(self) -> Sortkey:
        return (self.time or self.default_time,) + self.registration.get_sortkey()

    @property
    def is_present_previous(self) -> bool:
        return any(
            self.registration.parts[self.event_part.event.parts_by_shortname[prev_part]].status.is_present
            for prev_part in self.config.get("previous_parts", [])
        )

    def check_include(self, target: str) -> bool:
        if target == "checklist":
            if self.is_present_previous:
                if not self.config.get("show_previous_part_with_arrival_time") or self.time_is_missing:
                    return False

        return super().check_include(target)


@dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
class ParticipantDepartureInfo(_ParticipantTransportInfo):
    def get_sortkey(self) -> Sortkey:
        return self.registration.get_sortkey()

    @property
    def is_present_next(self) -> bool:
        return any(
            self.registration.parts[self.event_part.event.parts_by_shortname[next_part]].status.is_present
            for next_part in self.config.get("next_parts", [])
        )

    def check_include(self, target: str) -> bool:
        if target == "checklist" or target == "nametags":
            if self.is_present_next:
                if (
                    not self.config.get("show_next_part_with_departure_time")
                    or not self.time
                    or self.time == self.default_time
                ):
                    return False

        return super().check_include(target)


@dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
class NametagRegistration(Registration):
    def get_sortkey(self) -> Sortkey:
        return (f"{self.name.nametag_forename} {self.name.nametag_surname}",) + super().get_sortkey()

    @classmethod
    def from_registration(cls, registration: Registration) -> Self:
        return cls(**vars(registration))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Registration) and not isinstance(other, NametagRegistration):
            return self.id == other.id
        return super().__eq__(other)


def get_active_registrations(
    event: Event,
    parts: Iterable[EventPart] | None = None,
    include_guests: bool = False,
    list_consent_only: bool = False,
    minors_only: bool = False,
    matching_registrations_only: bool = False,
) -> list[Registration]:
    warnings.warn(
        "The `get_active_registrations` function is deprecated and will be removed in a future release."
        " Use the `Event.get_active_registrations` method instead.",
        DeprecationWarning,
    )
    return event.get_active_registrations(
        parts=parts,
        include_guests=include_guests,
        list_consent_only=list_consent_only,
        minors_only=minors_only,
        matching_registrations_only=matching_registrations_only,
    )
