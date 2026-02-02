"""
This module contains filters and other helper functions and classes meant to be used from the templates.

These may rely on the 'data' module.

This entire module is made available to the templates as 'UTIL'.
"""

import collections
from collections.abc import Iterable

from .common import RegistrationPartStati
from .data import Course, CourseTrackStati, EventTrack, Lodgement, Registration


def get_nametag_courses(
    registration: Registration, tracks: Iterable[EventTrack], merge: bool = True, second_always_right: bool = False
) -> tuple[list[Course | None], bool, bool]:
    """Get the courses to be printed on the nametag from a list of the event tracks and the registration

    :param registration: The registration to get its courses
    :param tracks: The list of event tracks to get the courses (e.g. only the tracks of one EventPart)
    :param merge: Merge equal courses of the first and second track
    :param second_always_right: Return a None value to push the second course to the right, if the participant is
        not present in the first track's part
    :returns The reduced list of courses, a flag to indicate if the courses have been merged and a flag to indicate
        if the persona attends at at least one course.
    """
    courses: list[Course | None] = []
    for t in tracks:
        reg_track = registration.tracks[t]
        if reg_track.registration_part.status.is_present:
            courses.append(reg_track.course)
        elif second_always_right:
            courses.append(None)

    attends_any_course = any(course is not None for course in courses)

    if merge:
        if len(courses) > 1 and courses[0] is courses[1] and courses[0] is not None:
            return [courses[0]], True, attends_any_course
        else:
            return courses, False, attends_any_course
    else:
        return courses, False, attends_any_course


def get_course_rooms(reg: Registration, tracks: Iterable[EventTrack], merge: bool = True) -> tuple[list[str], bool]:
    """Get the course rooms to be printed on the nametag from a list of the event tracks and the registration

    :param reg: The registration whose course rooms to get
    :param tracks: The list of event tracks to get the courses for (e.g. only the tracks of one EventPart)
    :param merge: Merge equal courses of the first and second track
    :returns The reduced list of course rooms and a flag to indicate if the courses have been merged.
    """
    rooms = []
    for track in tracks:
        reg_track = reg.tracks[track]
        if reg_track.registration_part.status.is_present and reg_track.course:
            room = str(reg_track.course.fields.get(track.course_room_field or "") or "")
            if room:
                rooms.append(room)

    if merge:
        if len(rooms) > 1 and rooms[0] == rooms[1]:
            return [rooms[0]], True
        else:
            return rooms, False
    else:
        return rooms, False


def gather_course_attendees(course: Course, include_guests: bool) -> list[tuple[Registration, list[EventTrack]]]:
    """Get a single list of all regular attendees (not instructors or guests) of a course (in all active tracks of the
    course)

    :param course: The course to gather its atttendees
    :return: A list of tuples, each representing a unique attendee of the course:
        (Registration: list of EventTracks, in which they attend the course)
    """
    regs = collections.defaultdict(list)
    for event_track, course_track in course.tracks.items():
        for reg, instr in course_track.attendees:
            if not instr and course_track.status == CourseTrackStati.active:
                if not include_guests and reg.parts[event_track.part].status == RegistrationPartStati.guest:
                    continue
                regs[reg].append(event_track)

    return sorted(regs.items())


def get_font_size(size_spec: list[tuple[int, int, int]], s: str) -> tuple[int, int]:
    """
    Helper function to determine the appropriate font size and line height for a string from a given spec.

    Select the first entry where the given string is shorter than the max length or the max length is -1.

    :param size_spec: An ordered list of string lengths and font and line height for strings of that length.
    """
    for max_len, font_size, line_height in size_spec:
        if len(s) <= max_len or max_len == -1:
            return font_size, line_height
    return 0, 0


def _override_filter(value: str | None, entity: Course | Lodgement | Registration, override_field: str) -> str | None:
    if value is None:
        return None
    replacement_value = entity.fields.get(override_field)
    if replacement_value is not None:
        return str(replacement_value)
    return value


# The functions below are copied almost verbatim from the CdEDB.


def _small_int_to_words(num: int) -> str:
    """Convert a small integer into a written representation.

    Helper for the general function.
    """
    if num < 0 or num > 999:
        raise ValueError("Out of supported scope.")
    digits = tuple((num // 10**i) % 10 for i in range(3))
    atoms = ("null", "ein", "zwei", "drei", "vier", "fünf", "sechs",
                "sieben", "acht", "neun", "zehn", "elf", "zwölf", "dreizehn",
                "vierzehn", "fünfzehn", "sechzehn", "siebzehn", "achtzehn",
                "neunzehn")  # fmt: skip
    tens = ("", "", "zwanzig", "dreißig", "vierzig", "fünfzig", "sechzig",
            "siebzig", "achtzig", "neunzig")  # fmt: skip
    ret = ""
    if digits[2]:
        ret += atoms[digits[2]] + "hundert"
    if num % 100 < 20:
        if num % 100:
            ret += atoms[num % 100]
        return ret
    if digits[0]:
        ret += atoms[digits[0]]
    if digits[0] and digits[1]:
        ret += "und"
    if digits[1]:
        ret += tens[digits[1]]
    return ret


def _int_to_words_filter(num: int) -> str:
    """Convert an integer into a written representation.

    This is for the usage such as '2 apples' -> 'two apples'.
    """
    if num < 0 or num > 999999:
        raise ValueError("Out of supported scope.")
    if num == 0:
        return "null"
    multipliers = ("", "tausend")
    number_words = []
    tmp = num
    while tmp > 0:
        number_words.append(_small_int_to_words(tmp % 1000))
        tmp = tmp // 1000
    ret = ""
    for number_word, multiplier in reversed(tuple(zip(number_words, multipliers))):
        if number_word != "null":
            ret += number_word + multiplier
    return ret
