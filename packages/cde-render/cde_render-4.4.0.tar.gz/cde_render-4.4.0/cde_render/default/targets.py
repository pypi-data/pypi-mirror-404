"""
This module defines the default targets. Each target is a function, that is called with the parsed event data and the
combined configuration (default + custom config.ini) and returns any number of PDFTasks. Each PDFTask will
be rendered with Jinja2 and compiled with LuaLaTeX, to result in a single PDF document. If multiple Tasks are present
-- either from different targets, specified by the user, or from a single target -- some of them are compiled in
parallel.

To add a function to the list of targets, the `@target_function` decorator from the `globals` module should be used.
A render task function must take exactly four positional parameters:
* The data.Event object with the CdE event's data
* A configparser object with the combined configuration data
* The path of the output directory. This may be used to add some auxiliary files to the directory
* A string taken from the `--match` command line argument. It may be used to filter the render tasks.

It must return an iterable of render.RenderTask objects. There are multiple kinds of RenderTasks, such as PDFTask
for rendering a jinja2 template into a .tex file which is then compiled using lualatex, or CSVTask which uses
 a DictWriter to write a list of dicts into a .csv file. The iterable may be empty, if there is nothing to be done.
Additionally it should contain a docstring according to PEP 257. It will be displayed as description of the
target to the user.
"""

import collections
import decimal
from collections.abc import Iterable

from cde_render.aux_data import (
    NametagRegistration,
    ParticipantArrivalInfo,
    ParticipantDepartureInfo,
    Room,
)
from cde_render.common import generate_filesafe_shortnames
from cde_render.data import (
    CourseTrackStati,
    Event,
    EventPart,
    Lodgement,
    LodgementGroup,
    Registration,
    RegistrationPartStati,
)
from cde_render.puzzles import NametagPuzzle
from cde_render.render import CSVTask, PDFTask, RenderTarget, RenderTargetGroup, RenderTask


class CourseInstructorsMailmerge(RenderTarget):
    description = (
        "Creates a CSV file for use with mailmerge, that will notify all potential course instructors about"
        " the status of their course."
    )
    display_name = "Course Instructor Notifications"

    def create_tasks(self) -> list[RenderTask]:
        ret: list[RenderTask] = []

        if not self.event.courses:
            return ret

        for track in self.event.tracks:
            display_name = self.display_name
            description = ""
            if len(self.event.tracks) > 1:
                display_name += f" ({track.shortname})"
                description = f"Only includes instructors of courses in Track {track.shortname}."
                if track.part.shortname_if_needed:
                    description = description.removesuffix(".") + f" (of Part {track.part.shortname})"

            # Create course_instructors_mailmerge_*.csv for generating a mail to KLs
            max_num_kls = max(len(course.instructors) for course in self.event.courses)
            headings = ["title", "nr", "part", "tn_list", "tn_num"]
            if track.course_room_field:
                headings.append("room")
            headings.append("receivers")
            headings.extend([f"kl{i}.given_names" for i in range(1, max_num_kls + 1)])
            csv_rows = []
            for c in self.event.courses:
                if not c.tracks[track].status == CourseTrackStati.active:
                    continue
                if not c.instructors:
                    continue
                attendees = [
                    p for p in c.tracks[track].regular_attendees if p.tracks[track].registration_part.status.is_present
                ]
                tnlist = "\n".join(f"{p.name.given_names} {p.name.family_name} &lt;{p.email}&gt;" for p in attendees)
                data = {
                    "title": c.title,
                    "nr": c.nr,
                    "part": track.part.shortname,
                    "tn_list": tnlist,
                    "tn_num": str(len(attendees)),
                    "receivers": ",".join(
                        f"{kl.name.given_names} {kl.name.family_name} <{kl.email}>" for kl in c.instructors
                    ),
                }
                if track.course_room_field:
                    data["room"] = str(c.fields.get(track.course_room_field) or "")
                data.update({f"kl{i + 1}.given_names": kl.name.salutation for i, kl in enumerate(c.instructors)})
                csv_rows.append(data)

            ret.append(
                CSVTask(
                    target=self,
                    display_name=display_name,
                    description=description,
                    base_filename=f"course_instructors_mailmerge_{track.filesafe_shortname}",
                    rows=csv_rows,
                    fields=headings,
                )
            )

            # Count choices per course
            course_choices = {
                course: [
                    sum(
                        1
                        for r in self.event.registrations
                        if r.tracks[track].registration_part.status.is_present
                        and len(r.tracks[track].choices) > i
                        and r.tracks[track].choices[i] == course
                    )
                    for i in range(track.num_choices)
                ]
                for course in self.event.courses
            }

            # Calculate and print avarage choices of non-cancelled courses
            choice_sum = [
                sum(cc[i] for course, cc in course_choices.items() if course.tracks[track].status.is_active)
                for i in range(track.num_choices)
            ]
            choice_average = [
                x / sum(1 for c in self.event.courses if c.tracks[track].status.is_active) for x in choice_sum
            ]
            print("Average choice number of non-cancelled courses:\n" + " - ".join(f"{x:.2f}" for x in choice_average))

            # Find theoretic KLs
            theoretic_kls = {
                course: [r for r in self.event.registrations if r.tracks[track].offered_course is course]
                for course in self.event.courses
            }
            max_num_theoretic_kls = max(len(x) for x in theoretic_kls.values())

            # Create nonkl_mailmerge.csv for generating a mail to non KLs with info about choices
            headings = (
                ["title", "nr", "part"]
                + [f"{i}-choices" for i in range(1, track.num_choices + 1)]
                + ["receivers"]
                + [f"kl{i}.given_names" for i in range(1, max_num_theoretic_kls + 1)]
            )
            csv_rows = []
            for c in self.event.courses:
                if c.tracks[track].status != CourseTrackStati.cancelled:
                    continue
                if not theoretic_kls[c]:
                    continue
                data = {
                    "title": c.title,
                    "nr": c.nr,
                    "part": track.part.shortname,
                    "receivers": ",".join(
                        f"{kl.name.given_names} {kl.name.family_name} <{kl.email}>" for kl in theoretic_kls[c]
                    ),
                }
                data.update({f"{i + 1}-choices": str(num_choices) for i, num_choices in enumerate(course_choices[c])})
                data.update({f"kl{i + 1}.given_names": kl.name.salutation for i, kl in enumerate(theoretic_kls[c])})
                csv_rows.append(data)
            ret.append(
                CSVTask(
                    target=self,
                    display_name=f"{display_name} (cancelled)",
                    description=description,
                    base_filename=f"course_instructors_mailmerge_cancelled_{track.filesafe_shortname}",
                    rows=csv_rows,
                    fields=headings,
                )
            )

        return ret


class ParticipationLetters(RenderTarget):
    description = (
        "Creates the 'Teilnahmebrief' for each participant and a mailmerge CSV file for sending them out."
        " Can be filtered using the `-r` CLI argument."
    )
    display_name = "Participation Letters"

    def create_tasks(self) -> list[RenderTask]:
        tasks: list[RenderTask] = []

        per_part = self.config.get("participation_letter", {}).get("per_part", True)
        if len(self.event.parts) == 1:
            per_part = False

        #: Use `event.matching_registrations` to limit registrations via CLI.
        participants = [r for r in self.event.matching_registrations if r.is_participant]

        if not participants:
            print(f"No participants for target {self.__class__.__name__}. Skipping.")
            return tasks

        filesafe_reg_names = generate_filesafe_shortnames({reg.persona_id: reg.name.common for reg in participants})
        filenames = {reg.persona_id: filesafe_reg_names[reg.persona_id] for reg in participants}
        filenames_per_part = {
            (part, reg.persona_id): f"{filesafe_reg_names[reg.persona_id]}_{part.filesafe_shortname}"
            for reg in participants
            for part in reg.parts
        }

        # Create MailMerge CSV file
        csv_rows: list[dict[str, str]] = []

        for reg in participants:
            row = {
                "persona.forename": reg.name.salutation,
                "persona.family_name": reg.name.family_name,
                "persona.username": reg.email,
                **(
                    {
                        f"attachment{part.shortname}": f"{filenames_per_part[(part, reg.persona_id)]}.pdf"
                        for part in reg.parts
                    }
                    if per_part
                    else {"attachment": f"{filenames[reg.persona_id]}.pdf"}
                ),
            }

            for event_track in self.event.tracks:
                ptrack = reg.tracks[event_track]
                row[f"is_instructor_{event_track.shortname}"] = str(ptrack.instructor)
                row[f"is_attendee_{event_track.shortname}"] = str(bool(ptrack.course) and not ptrack.instructor)
                row[f"course_title_{event_track.shortname}"] = ptrack.course.title if ptrack.course else ""
                row[f"course_nr_{event_track.shortname}"] = ptrack.course.nr if ptrack.course else ""

            for event_part in self.event.parts:
                ppart = reg.parts[event_part]
                row[f"is_participant_{event_part.shortname}"] = str(ppart.status == RegistrationPartStati.participant)

            csv_rows.append(row)

        tasks.append(
            CSVTask(
                target=self,
                display_name="Participation Letters MailMerge",
                description="Mailmerge CSV file for sending out participation letters.",
                base_filename="participation_letters_mailmerge",
                subdirectory="participation_letters",
                rows=csv_rows,
                fields=list(csv_rows[0].keys()),
            )
        )

        if per_part:
            for reg in participants:
                tasks.extend(
                    PDFTask(
                        target=self,
                        display_name=f"{reg.name.common} ({part.shortname})",
                        description="",
                        base_filename=filenames_per_part[(part, reg.persona_id)],
                        subdirectory="participation_letters",
                        template_name="participation_letter.tex",
                        template_args={
                            "registration": reg,
                            "event_part": part,
                        },
                    )
                    for part in self.event.parts
                    if reg.parts[part].status.is_present
                )
        else:
            tasks.extend(
                PDFTask(
                    target=self,
                    display_name=f"{reg.name.common}",
                    description="",
                    base_filename=filesafe_reg_names[reg.persona_id],
                    subdirectory="participation_letters",
                    template_name="participation_letter.tex",
                    template_args={
                        "registration": reg,
                        **{f"part.{part.shortname}": part for part in self.event.parts},
                    },
                )
                for reg in participants
                if reg.is_present
            )

        return tasks


class ListParticipants(RenderTarget):
    description = (
        "Creates the public participant list of all participants,"
        " containing on event information like course rooms and lodgements."
    )
    display_name = "Participant List"

    def create_tasks(self) -> list[RenderTask]:
        include_guests = bool(self.config.get("participant_lists", {}).get("show_guests"))
        participants = self.event.get_active_registrations(include_guests=include_guests)

        all_parts_suffix = " (all Parts)" if len(self.event.parts) > 1 else ""
        description = f"Includes participants{' and guests' if include_guests else ''} of any event part."
        tasks: list[RenderTask] = [
            PDFTask(
                target=self,
                display_name=self.display_name + all_parts_suffix,
                description=description,
                base_filename="list_participants",
                template_name="list_participants.tex",
                template_args={
                    "registrations": participants,
                    "parts": self.event.parts,
                    "tracks": self.event.tracks,
                },
            )
        ]

        if len(self.event.parts) > 1:
            for part in self.event.parts:
                part_participants = self.event.get_active_registrations(parts=(part,), include_guests=include_guests)
                tasks.append(
                    PDFTask(
                        target=self,
                        display_name=f"{self.display_name} ({part.shortname})",
                        description=(
                            f"Only includes participants{' and guests' if include_guests else ''}"
                            f" of part {part.shortname}."
                        ),
                        base_filename=f"list_participants_{part.filesafe_shortname}",
                        template_name="list_participants.tex",
                        template_args={
                            "registrations": part_participants,
                            "parts": [part],
                            "tracks": part.tracks,
                            "title_suffix": f" ({part.title})",
                        },
                    )
                )

        return tasks


class OrgaListParticipants(RenderTarget):
    description = (
        "Creates the participant list for orga use. Includes all participants and personal data, like phone numbers,"
        " in addition to on event information like course rooms and lodgements."
    )
    display_name = "Participant List (for Orgas)"

    def create_tasks(self) -> list[RenderTask]:
        include_guests = bool(self.config.get("participant_lists", {}).get("show_guests_orga"))
        participants_orga = self.event.get_active_registrations(include_guests=include_guests)

        all_parts_suffix = " (all Parts)" if len(self.event.parts) > 1 else ""
        tasks: list[RenderTask] = [
            PDFTask(
                target=self,
                display_name=self.display_name + all_parts_suffix,
                description=f"Includes participants{' and guests' if include_guests else ''} of any event part.",
                base_filename="orga_list_participants",
                template_name="orga_list_participants.tex",
                template_args={
                    "registrations": participants_orga,
                    "parts": self.event.parts,
                    "tracks": self.event.tracks,
                },
            ),
        ]

        if len(self.event.parts) > 1:
            for part in self.event.parts:
                part_participants_orga = self.event.get_active_registrations(
                    parts=(part,), include_guests=include_guests
                )
                tasks.append(
                    PDFTask(
                        target=self,
                        display_name=f"{self.display_name} ({part.shortname})",
                        description=(
                            f"Only includes participants{' and guests' if include_guests else ''}"
                            f" of part {part.shortname}."
                        ),
                        base_filename=f"orga_list_participants_{part.filesafe_shortname}",
                        template_name="orga_list_participants.tex",
                        template_args={
                            "registrations": part_participants_orga,
                            "parts": [part],
                            "tracks": part.tracks,
                            "title_suffix": f" ({part.title})",
                        },
                    )
                )

        return tasks


class ChecklistMinors(RenderTarget):
    description = (
        "Creates lists of all minors with columns to check their presence once per day for every event part."
        " Includes guests."
    )
    display_name = "Minor Checklist"

    def create_tasks(self) -> list[RenderTask]:
        return [
            PDFTask(
                target=self,
                display_name=f"{self.display_name}{f' ({part.shortname})' if part.shortname_if_needed else ''}",
                description=f"Checklist for part {part.shortname}" if part.shortname_if_needed else "",
                base_filename=(f"checklist_minors{f'_{part.filesafe_shortname}' if part.shortname_if_needed else ''}"),
                template_name="checklist_minors.tex",
                template_args={
                    "registrations": self.event.get_active_registrations(
                        parts=(part,), include_guests=True, minors_only=True
                    ),
                    "part": part,
                },
            )
            for part in self.event.parts
        ]


class MinorNightlog(RenderTarget):
    description = (
        'Creates a "nightlog" (aka "Logbuch", "Ausleihliste") for minors in form of a booklet.'
        " One for every evening of every event part. Includes guests."
    )
    display_name = "Minor Nightlog"

    def create_tasks(self) -> list[RenderTask]:
        tasks: list[RenderTask] = []
        for part in self.event.parts:
            minors = self.event.get_active_registrations(parts=(part,), include_guests=True, minors_only=True)

            filename_suffix = f"_{part.filesafe_shortname}" if part.shortname_if_needed else ""

            tasks.extend(
                PDFTask(
                    target=self,
                    display_name=(
                        f"{self.display_name} {day.strftime('%d.%m.%Y')}"
                        f"{f' ({part.shortname})' if part.shortname_if_needed else ''}"
                    ),
                    description=(
                        f"Nightlog for {day:%d.%m.%y}{f' of {part.shortname}' if part.shortname_if_needed else ''}"
                    ),
                    base_filename=f"minor_nightlog{filename_suffix}_{day:%Y-%m-%d}",
                    subdirectory="minor_nightlogs",
                    template_name="minor_nightlog.tex",
                    template_args={
                        "participants": minors,
                        "day": day,
                    },
                )
                for day in list(part.days)[:-1]
            )
        return tasks


class ListsRooms(RenderTarget):
    description = (
        "Creates lists for all rooms listing all inhabitants of the room and courses and their attendees in the room."
        " Course rooms and lodgements are combined by their name."
    )
    display_name = "Room Lists"

    def create_tasks(self) -> list[RenderTask]:
        tasks: list[RenderTask] = []
        rooms = Room.from_event(self.event, self.config)

        include_empty_lodgements = self.config.get("room_lists", {}).get("include_empty_lodgements", "group")
        include_empty_course_rooms = self.config.get("room_lists", {}).get("include_empty_course_rooms", False)

        lodgements_by_group: dict[LodgementGroup, list[Lodgement]] = {}
        for lodgement in self.event.lodgements:
            lodgements_by_group.setdefault(lodgement.group, []).append(lodgement)

        rooms_by_part = {
            part: [
                room
                for room in rooms
                if (
                    room.lodgement
                    and (
                        room.lodgement.parts[part].inhabitants
                        or include_empty_lodgements == "all"
                        or include_empty_lodgements == "group"
                        and any(
                            lodgement.parts[part].inhabitants for lodgement in lodgements_by_group[room.lodgement.group]
                        )
                    )
                    or room.course_tracks
                    and (
                        any(ct.track.part == part for ct in room.course_tracks)
                        or not room.lodgement
                        and include_empty_course_rooms
                    )
                )
            ]
            for part in self.event.parts
        }

        for part in self.event.parts:
            tasks.append(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name}{f' ({part.shortname})' if part.shortname_if_needed else ''}",
                    description=f"Room Lists for {part.shortname}" if part.shortname_if_needed else "",
                    base_filename=(f"lists_rooms{f'_{part.filesafe_shortname}' if part.shortname_if_needed else ''}"),
                    template_name="lists_rooms.tex",
                    template_args={
                        "part": part,
                        "rooms": rooms_by_part[part],
                    },
                )
            )

        return tasks


class ListsAttendees(RenderTarget):
    description = "Creates list of attendees for all courses for instructors."
    display_name = "Attendee Lists (for instructors)"

    def create_tasks(self) -> list[RenderTask]:
        return [
            PDFTask(
                target=self,
                display_name=self.display_name,
                description="",
                base_filename="lists_attendees",
                template_name="lists_attendees.tex",
                template_args={},
            ),
        ]


class OrgaListVertrauenspersonen(RenderTarget):
    description = "Creates a list of Vertrauenspersonen per event part."
    display_name = "Vertrauenspersonen List (for Orgas)"

    def create_tasks(self) -> list[RenderTask]:
        registrations: dict[EventPart, list[Registration]] = {ep: [] for ep in self.event.parts}

        for reg in self.event.registrations:
            for reg_part in reg.parts.values():
                vp_field = self.config.get("data", {}).get("vertrauenspersonen", {}).get(reg_part.part.shortname)
                if not vp_field:
                    continue
                if reg_part.status.is_present and reg.fields.get(vp_field, False):
                    registrations[reg_part.part].append(reg)

        return [
            PDFTask(
                target=self,
                display_name=f"{self.display_name}{f' {part.shortname}' if part.shortname_if_needed else ''}",
                description="",
                base_filename=(
                    f"orga_list_vertrauenspersonen{f'_{part.filesafe_shortname}' if part.shortname_if_needed else ''}"
                ),
                template_name="orga_list_vertrauenspersonen.tex",
                template_args={
                    "registrations": registrations[part],
                    "part": part,
                },
            )
            for part in self.event.parts
        ]


class ListCourses(RenderTarget):
    description = "Creates a list of all courses for every event part."
    display_name = "Course List"

    def create_tasks(self) -> list[RenderTask]:
        all_parts_suffix = " (all Parts)" if len(self.event.parts) > 1 else ""
        tasks: list[RenderTask] = [
            PDFTask(
                target=self,
                display_name=self.display_name + all_parts_suffix,
                description="",
                base_filename="list_courses",
                template_name="list_courses.tex",
                template_args={
                    "tracks": self.event.tracks,
                    "courses": self.event.courses,
                },
            )
        ]

        if len(self.event.parts) > 1:
            for part in self.event.parts:
                tasks.append(
                    PDFTask(
                        target=self,
                        display_name=f"{self.display_name} ({part.shortname})",
                        description=f"Course List for part {part.shortname}",
                        base_filename=f"list_courses_{part.filesafe_shortname}",
                        template_name="list_courses.tex",
                        template_args={
                            "parts": part,
                            "tracks": part.tracks,
                            "courses": [
                                course
                                for course in self.event.courses
                                if any(course.tracks[track].status.is_active for track in part.tracks)
                            ],
                        },
                    )
                )

        return tasks


class Nametags(RenderTarget):
    description = (
        "Creates nametags for all participants and guests (for every event part)."
        " Can be filtered using the `-r` CLI argument."
    )
    display_name = "Nametags"

    def create_tasks(self) -> list["RenderTask"]:
        per_part: bool | None = self.config.get("nametags", {}).get("per_part")
        if per_part is None:
            per_part = len(self.event.parts) > 2 or len(self.event.tracks) > 2
        if len(self.event.parts) == 1:
            per_part = False

        #: Use `event.matching_registrations` to limit registrations via CLI.
        present_registrations = sorted(
            NametagRegistration.from_registration(reg) for reg in self.event.matching_registrations if reg.is_present
        )

        puzzles = NametagPuzzle.check_all(self, present_registrations)

        if per_part:
            ret: list[RenderTask] = [
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name} ({part.shortname})",
                    description="",
                    base_filename=f"nametags_{part.filesafe_shortname}",
                    template_name="nametags.tex",
                    template_args={
                        "registration_groups": group_participants(
                            self.event,
                            _registrations := [p for p in present_registrations if p.parts[part].status.is_present],
                            part,
                        ),
                        "part": part,
                        "puzzles": puzzles.filter(registrations=_registrations, part=part),
                    },
                )
                for part in self.event.parts
            ]
        else:
            ret = [
                PDFTask(
                    target=self,
                    display_name=self.display_name,
                    description="",
                    base_filename="nametags",
                    template_name="nametags.tex",
                    template_args={
                        "registration_groups": group_participants(
                            self.event,
                            present_registrations,
                            # This part only affects the grouping by lodgement, which is not ideal but not
                            #  catastrophic if there is more than one part.
                            self.event.parts[0],
                        ),
                        # This part might affect the puzzles, but this is the users fault for wanting
                        #  non-separate namteags then.
                        "puzzles": puzzles.filter(registrations=present_registrations),
                    },
                ),
            ]

        if NametagPuzzle.get_all_puzzle_classes():
            ret.append(
                PDFTask(
                    target=self,
                    display_name="Puzzle Solutions",
                    description="Creates a list of nametag puzzles and stats for every puzzle.",
                    base_filename="puzzle_solutions",
                    template_name="puzzle_solutions.tex",
                    template_args={
                        "all_puzzles": NametagPuzzle.get_all_puzzle_classes(),
                        "puzzle_stats": puzzles.stats(),
                    },
                )
            )

        return ret


def group_participants(
    event: Event, participants: Iterable[Registration], part: EventPart
) -> list[tuple[str, list[Registration]]]:
    """Helper function for grouping the participants by age and lodgement for different nametag colors.

    First, tries to assign, each participant to one of the config.nametags.age_groups. If not possible, tries to assign
    them to one of the config.nametags.lodgement_groups. If not possible assignes them to the 'others' group.

    :param participants: A list of participants to group
    :param part: The event part to consider for grouping by lodgement
    :return: List of groups as tuple of group name and list of participants
    """
    age_groups: list[tuple[int, list[Registration]]]
    age_groups = [(int(x), []) for x in event.config.get("nametags", {}).get("age_groups", [])]
    lodgement_groups: list[tuple[LodgementGroup, list[Registration]]]
    lodgement_groups = [(lg, []) for lg in event.lodgement_groups]
    others = []

    # Create duplicate nametags for Vertrauenspersonen and Orgas.
    vertrauenspersonen = []
    vp_field_name = event.config.get("data", {}).get("vertrauenspersonen", {}).get(part.shortname)
    orgas = []
    orga_nametags_regular = event.config.get("nametags", {}).get("orga_nametags_regular")
    orga_nametags_separate = event.config.get("nametags", {}).get("orga_nametags_separate")

    for p in participants:
        if vp_field_name and p.fields.get(vp_field_name, False):
            vertrauenspersonen.append(p)

        if p.is_orga:
            if orga_nametags_separate:
                orgas.append(p)
            if not orga_nametags_regular:
                continue

        for max_age, registrations in age_groups:
            if p.age < max_age:
                registrations.append(p)
                break
        else:
            for lodgement_group, registrations in lodgement_groups:
                lodgement = p.parts[part].lodgement
                if lodgement and lodgement.group is lodgement_group:
                    registrations.append(p)
                    break
            else:
                others.append(p)

    ret = [
        *((f"age u{name}", registrations) for name, registrations in age_groups),
        *((lg.title, registrations) for lg, registrations in lodgement_groups),
        ("others", others),
        ("vertrauenspersonen", vertrauenspersonen),
    ]

    if orga_nametags_separate:
        ret.append(("orgas", orgas))

    return ret


def _get_arriving_participants(
    event: Event, target: str, registrations: Iterable[Registration] | None = None
) -> dict[EventPart, list[ParticipantArrivalInfo]]:
    transport_values = event.config.get("data", {}).get("transport_values", {})

    # Parse arrival config per part, defaulting to arrival config with no specified part.
    arrival_config = dict(event.config.get("arrival", {}))
    parts = arrival_config.pop("parts", [])
    raw_config_by_part = {part_config.get("part") or "": part_config for part_config in parts}
    arrival_config_by_part = {
        event_part: (raw_config_by_part.get(event_part.shortname) or raw_config_by_part.get("") or {}) | arrival_config
        for event_part in event.parts
    }

    registrations = registrations if registrations is not None else event.registrations
    if target == "nametags":
        registrations = sorted(NametagRegistration.from_registration(reg) for reg in registrations)

    return {
        part: sorted(
            ap
            for registration in registrations
            if (
                ap := ParticipantArrivalInfo.from_registration(registration, part, transport_values, part_config)
            ).check_include(target=target)
        )
        for part, part_config in arrival_config_by_part.items()
    }


def _get_departing_participants(
    event: Event, target: str, registrations: Iterable[Registration] | None = None
) -> dict[EventPart, list[ParticipantDepartureInfo]]:
    transport_values = event.config.get("data", {}).get("transport_values", {})

    # Parse departure config per part, defaulting to departure config with no specified part.
    departure_config = dict(event.config.get("departure", {}))
    parts = departure_config.pop("parts", [])
    raw_config_by_part = {part_config.get("part") or "": part_config for part_config in parts}
    departure_config_by_part = {
        event_part: (raw_config_by_part.get(event_part.shortname) or raw_config_by_part.get("") or {})
        | departure_config
        for event_part in event.parts
    }

    registrations = registrations if registrations is not None else event.registrations
    if target == "nametags":
        registrations = sorted(NametagRegistration.from_registration(reg) for reg in registrations)

    return {
        part: sorted(
            dp
            for registration in registrations
            if (
                dp := ParticipantDepartureInfo.from_registration(registration, part, transport_values, part_config)
            ).check_include(target=target)
        )
        for part, part_config in departure_config_by_part.items()
    }


class ChecklistArrival(RenderTarget):
    description = "Creates checklists of all newly arriving participants for every event part."
    display_name = "Arrival Checklist"

    def create_tasks(self) -> list[RenderTask]:
        tasks: list[RenderTask] = []

        arriving_participants_by_part = _get_arriving_participants(self.event, target="checklist")

        # Allow only rendering one checklist variant via config.
        sort_by_time = sort_by_name = True
        arrival_config = self.config.get("arrival", {})
        if (sort := arrival_config.get("checklist_sort", "both").lower()) == "time":
            sort_by_name = False
        elif sort == "name":
            sort_by_time = False

        for part in self.event.parts:
            participants_sorted_by_arrival = arriving_participants_by_part[part]
            participants_sorted_by_name = sorted(participants_sorted_by_arrival, key=lambda x: x.registration)

            display_name = f"{self.display_name}{f' ({part.shortname})' if part.shortname_if_needed else ''}"
            filesafe_shortname = f"_{part.filesafe_shortname}" if part.shortname_if_needed else ""

            if sort_by_time:
                tasks.append(
                    PDFTask(
                        target=self,
                        display_name=f"{display_name} sorted by Arrival Time",
                        description="",
                        base_filename=f"checklist_arrival_by_time{filesafe_shortname}",
                        template_name="checklist_arrival.tex",
                        template_args={"participants": participants_sorted_by_arrival, "part": part},
                    ),
                )
            if sort_by_name:
                tasks.append(
                    PDFTask(
                        target=self,
                        display_name=f"{display_name} sorted by Name",
                        description="",
                        base_filename=f"checklist_arrival_by_name{filesafe_shortname}",
                        template_name="checklist_arrival.tex",
                        template_args={"participants": participants_sorted_by_name, "part": part},
                    ),
                )

        return tasks


class ChecklistDeparture(RenderTarget):
    description = "Creates checklists of all departing participants assigned to a bus for every event part."
    display_name = "Departure Checklists"

    def create_tasks(self) -> list[RenderTask]:
        tasks: list[RenderTask] = []

        departing_participants_by_part = _get_departing_participants(self.event, target="checklist")

        for part in self.event.parts:
            busses: dict[str, list[ParticipantDepartureInfo]] = collections.defaultdict(list)
            for departing_participant in departing_participants_by_part[part]:
                if departing_participant.bus:
                    busses[departing_participant.bus].append(departing_participant)

            if not busses:
                print(f"No bus field(s), no bus assignments or no registrations for {part!r}.")
                continue
            part_config = departing_participants_by_part[part][0].config

            tasks.append(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name}{f' ({part.shortname})' if part.shortname_if_needed else ''}",
                    description="",
                    base_filename=(
                        f"checklist_departure{f'_{part.filesafe_shortname}' if part.shortname_if_needed else ''}"
                    ),
                    template_name="checklist_departure.tex",
                    template_args={
                        "busses": busses.items(),
                        "part": part,
                        "config": part_config,
                    },
                )
            )
        return tasks


class ListDepartures(RenderTarget):
    description = "Creates list with departure times for all participants for them to check and confirm."
    display_name = "Departure List"

    def create_tasks(self) -> list[RenderTask]:
        tasks: list[RenderTask] = []

        departing_participants_by_part = _get_departing_participants(self.event, target="list")

        for part in self.event.parts:
            part_participants = departing_participants_by_part[part]
            if not part_participants:
                continue
            part_config = part_participants[0].config

            tasks.append(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name}{f' ({part.shortname})' if part.shortname_if_needed else ''}",
                    description="",
                    base_filename=(
                        f"list_departure{f'_{part.filesafe_shortname}' if part.shortname_if_needed else ''}"
                    ),
                    template_name="list_departure.tex",
                    template_args={
                        "participants": part_participants,
                        "part": part,
                        "config": part_config,
                    },
                )
            )

        return tasks


class NametagsDeparture(RenderTarget):
    description = (
        "Create nametags for printing on sticky nametag sheets to replace the usual nametags on departure day."
    )
    display_name = "Departure Nametags"

    def create_tasks(self) -> list[RenderTask]:
        tasks: list[RenderTask] = []

        departing_participants_by_part = _get_departing_participants(
            self.event, target="nametags", registrations=self.event.matching_registrations
        )

        for part in self.event.parts:
            part_participants = departing_participants_by_part[part]
            if not part_participants:
                continue
            part_config = part_participants[0].config

            tasks.append(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name}{f' ({part.shortname})' if part.shortname_if_needed else ''}",
                    description="",
                    base_filename=(
                        f"nametags_departure{f'_{part.filesafe_shortname}' if part.shortname_if_needed else ''}"
                    ),
                    template_name="nametags_departure.tex",
                    template_args={
                        "participants": part_participants,
                        "part": part,
                        "config": part_config,
                    },
                )
            )

        return tasks


class DonationReceipts(RenderTarget):
    description = (
        "Creates receipts for all donations. For use by Vorstand not Orgas! Orgas are legally not allowed to"
        " issue donation receipts."
        " Can be filtered using the `-r` CLI argument."
    )
    display_name = "Donation Receipts"

    def create_tasks(self) -> list[RenderTask]:
        print(
            "\nWARNING:\nThis shall only be used by the Vorstand!"
            " Orgas are legally not allowed to issue donation receipts!\n"
        )

        wants_receipt_field = self.config.get("donation", {}).get("wants_receipt_field", "")
        donation_fields = self.config.get("donation", {}).get("donation_fields", {})
        receipt_issuer = self.config.get("donation", {}).get("receipt_issuer", "")
        place_of_issue = self.config.get("donation", {}).get("place_of_issue", "")

        tasks: list[RenderTask] = []

        filesafe_reg_names = generate_filesafe_shortnames(
            {reg.persona_id: reg.name.common for reg in self.event.matching_registrations}
        )

        #: Use `event.matching_registrations` to limit registrations via CLI.
        for reg in self.event.matching_registrations:
            if not reg.fields.get(wants_receipt_field):
                continue
            donation = sum(
                (
                    decimal.Decimal(amount)
                    for field_name, amount in donation_fields.items()
                    if reg.fields.get(field_name)
                ),
                start=decimal.Decimal(0),
            )
            # check that the donation is an integer
            if donation.as_integer_ratio()[1] != 1:
                raise ValueError("Donation must be an integer!")
            if donation <= 0:
                continue
            tasks.append(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name} {reg.name.common}",
                    description="",
                    base_filename=filesafe_reg_names[reg.persona_id],
                    subdirectory="donation_receipts",
                    template_name="donation_receipt.tex",
                    template_args={
                        "registration": reg,
                        "donation": donation,
                        "issuer": receipt_issuer,
                        "place_of_issue": place_of_issue,
                        "date_of_donation": reg.payment.date,
                    },
                )
            )
        return tasks


class Envelopes(RenderTarget):
    description = (
        "Creates envelope sized (22cm x 11cm) pages with name, course and attended parts for every"
        " participant and guest, by event part or event part group depending on configuration."
        " Meant for printing on the backside of regular envelopes."
        " Can be filtered using the `-r` CLI argument."
    )
    display_name = "Envelopes"

    def create_tasks(self) -> list[RenderTask]:
        envelope_part_groups = self.config.get("envelopes", {}).get("part_groups", [])

        ungrouped_parts = set(self.event.parts_by_shortname)
        for group in envelope_part_groups:
            for part in group["parts"]:
                ungrouped_parts.remove(part)

        #: Use `event.matching_registrations` to limit registrations via CLI.

        return [
            *(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name} {group['shortname']}",
                    description="",
                    base_filename=f"envelopes_{group['shortname']}",
                    template_name="envelopes.tex",
                    template_args={
                        "registrations": [
                            r
                            for r in self.event.matching_registrations
                            if any(
                                r.parts[self.event.parts_by_shortname[part]].status.is_present
                                for part in group["parts"]
                            )
                        ],
                    },
                )
                for group in envelope_part_groups
            ),
            *(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name} {part.shortname}",
                    description="",
                    base_filename=f"envelopes_{part.filesafe_shortname}",
                    template_name="envelopes.tex",
                    template_args={
                        "registrations": [
                            r for r in self.event.matching_registrations if r.parts[part].status.is_present
                        ],
                    },
                )
                for part in self.event.parts
                if part.shortname in ungrouped_parts
            ),
        ]


class ListRoomChanges(RenderTarget):
    description = (
        "Creates list with room changes for all participants who need to move to a different room for the"
        " configured event parts."
    )
    display_name = "Room Change List"

    def create_tasks(self) -> list["RenderTask"]:
        ret: list[RenderTask] = []

        room_change_config = self.config.get("room_changes", {})
        room_change_parts = room_change_config.get("parts", [])

        for entry in room_change_parts:
            first = self.event.parts_by_shortname[entry["first"]]
            second = self.event.parts_by_shortname[entry["second"]]

            registrations = [
                reg
                for reg in self.event.registrations
                if reg.parts[first].status.is_present
                and reg.parts[second].status.is_present
                and reg.parts[first].lodgement
                and reg.parts[second].lodgement
                and (
                    reg.parts[first].lodgement != reg.parts[second].lodgement
                    or room_change_config.get("include_non_changing")
                )
            ]

            ret.append(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name} {first.shortname} -> {second.shortname}",
                    description="",
                    base_filename=f"list_room_changes_{first.filesafe_shortname}_{second.filesafe_shortname}",
                    template_name="list_room_changes.tex",
                    template_args={
                        "registrations": registrations,
                        "first": first,
                        "second": second,
                        "guest": RegistrationPartStati.guest,
                    },
                )
            )

        return ret


class OrgaListBirthdays(RenderTarget):
    description = "Creates a list of people who celebrate their birthday during the event."
    display_name = "Birthday List"

    def create_tasks(self) -> list[RenderTask]:
        return [
            *(
                PDFTask(
                    target=self,
                    display_name=f"{self.display_name} {part.shortname}",
                    description="",
                    base_filename=f"orga_list_birthdays_{part.filesafe_shortname}",
                    template_name="orga_list_birthdays.tex",
                    template_args={
                        "registrations": sorted(
                            (reg for reg in self.event.matching_registrations if reg.parts[part].event_birthdays),
                            key=lambda reg: reg.parts[part].event_birthdays,
                        ),
                        "part": part,
                    },
                )
                for part in self.event.parts
                if len(self.event.parts) > 1
            ),
            PDFTask(
                target=self,
                display_name=self.display_name,
                description="",
                base_filename="orga_list_birthdays",
                template_name="orga_list_birthdays.tex",
                template_args={
                    "registrations": sorted(
                        (reg for reg in self.event.matching_registrations if reg.event_birthdays),
                        key=lambda reg: reg.event_birthdays,
                    ),
                    "part": None,
                },
            ),
        ]


class OrgaLists(RenderTargetGroup):
    display_name = "All Orgalists"
    description = "Creates all orga specific lists."
    target_classes = [
        "OrgaListParticipants",
        "OrgaListVertrauenspersonen",
        "OrgaListBirthdays",
        "ListCourses",
        "ChecklistMinors",
        "ChecklistArrival",
        "ChecklistDeparture",
    ]


class PublicLists(RenderTargetGroup):
    display_name = "All Public Lists"
    description = "Creates all public lists."
    target_classes = [
        "ListParticipants",
        "ListCourses",
        "ListRoomChanges",
        "ListDepartures",
        "ListsRooms",
        "ListsAttendees",
    ]


class MinorTools(RenderTargetGroup):
    display_name = "Tools for Minors"
    description = "Creates all tools for minors."
    target_classes = [
        "ChecklistMinors",
        "MinorNightlog",
    ]


class ArrivalTools(RenderTargetGroup):
    display_name = "Arrival Tools"
    description = "Creates all targets for arriving participants."
    target_classes = [
        "ChecklistArrival",
        "Nametags",
        "ListParticipants",
        "ListCourses",
        "ListsRooms",
        "ListsAttendees",
    ]


class DepartureTools(RenderTargetGroup):
    display_name = "Departure Tools"
    description = "Creates all targets for departing participants."
    target_classes = [
        "ListDepartures",
        "ChecklistDeparture",
        "NametagsDeparture",
        "ListRoomChanges",
    ]


class AllTargets(RenderTargetGroup):
    display_name = "All Targets"
    description = "Creates all targets, except participation letters and donation receipts."
    target_classes = [
        target_class.__name__
        for target_class in RenderTarget.__subclasses__()
        if target_class is not RenderTargetGroup
        and target_class is not ParticipationLetters
        and target_class is not DonationReceipts
    ]
