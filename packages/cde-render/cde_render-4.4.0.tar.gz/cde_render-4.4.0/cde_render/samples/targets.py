from typing_extensions import Self

from cde_render import data, puzzles, render
from cde_render.default import targets

# Imagine that this is a puzzle from the default targets. (You would then need to refer to it using 'targets.Birthday'.


class Birthday(puzzles.NametagPuzzle):
    display_name = "Birthday"
    description = "Has their birthday during any event part."
    asset_name = "meal_special"

    @classmethod
    def check(cls, target: render.RenderTarget, registration: data.Registration) -> Self | None:
        parts = {
            event_part
            for event_part in registration.parts
            if any(
                (event_part.begin.year, event_part.begin.month, event_part.begin.day)
                <= (year, registration.birthday.month, registration.birthday.day)
                <= (event_part.end.year, event_part.end.month, event_part.end.day)
                for year in range(event_part.begin.year, event_part.end.year + 1)
            )
        }
        if parts:
            return cls(target, registration, parts)
        return None


# You could create your own puzzles like this, by inheriting from 'puzzles.NametagPuzzle':


class BirthdayForAll(puzzles.NametagPuzzle):
    display_name = "Birthday for All"
    description = "Now everyone gets a birthday."
    asset_name = "meal_special"

    @classmethod
    def check(cls, target: render.RenderTarget, registration: data.Registration) -> Self | None:
        return cls(target, registration, set(registration.parts))


# You could derive your own puzzle from an existing one like this by inheriting from that puzzle:
#  Use 'super().check(target, registration)' to get the result of the original implementation.
#  You can modify the result by e.g. a) skipping the registration by returning before that
#  b) checking additional conditions afterward.
#  c) modifying the 'ret.parts' (if it is not None) to adjust the event parts where the puzzle should apply.
#     Return None rather than a puzzle with an empty 'parts' if your event has more than one part.


class PresentBirthday(Birthday):
    display_name = "Present Birthday"
    description = "Has their birthday during any event part and is present."

    @classmethod
    def check(cls, target: render.RenderTarget, registration: data.Registration) -> Self | None:
        if ret := super().check(target, registration):
            ret.parts = {event_part for event_part in ret.parts if registration.parts[event_part].status.is_present}
            if not ret.parts:
                return None
        return ret


# You can create your own targets like this, by inheriting from 'render.RenderTarget':


class MyTarget(render.RenderTarget):
    display_name = "My Target"
    description = "My target"

    def create_tasks(self) -> list[render.RenderTask]:
        return [
            render.PDFTask(
                target=self,
                display_name=self.display_name,
                description="",
                base_filename="my_target",
                template_name="lists_attendees.tex",
                template_args={},
                double_tex=False,
            )
        ]


# You can disable default targets like this. Subclasses will also be disabled, but can be manually reenabled.

targets.ListParticipants.disabled = True


# You can modify a defaut target by inheriting from it like this:
#  Use 'super().create_tasks()' to get the tasks of the original target.
#  You cannot directly modify the original tasks, except for 'RenderTask.template_args', but you can create new ones,
#  or you can leave some of them out.


class MyListParticipants(targets.ListParticipants):
    description = "My participant list"

    disabled = False  # Only necessary if you disabled the parent.

    def create_tasks(self) -> list[render.RenderTask]:
        ret = super().create_tasks()
        if len(ret) > 1:
            return ret[1:]
        return ret


# Defining a target with the same name as the default target will disable the default target due to name ambiguity.
#  (This is an implementation detail and could change.)


class ParticipationLetters(render.RenderTarget):
    display_name = "PLetters"
    description = ""

    def create_tasks(self) -> list[render.RenderTask]:
        return []


# Just like targets, you can create new or adjust existing target groups like this:
#  The 'target_classes' can be a list of either default or custom targets.
#
#  Note that target groups can contain disabled targets and that the default target groups will not
#  care if you override targets contained in them. (Both of these things may change in the future).


class MyGroup(render.RenderTargetGroup):
    display_name = "Blubb"
    description = "Bla"
    target_classes = [
        "MyTarget",
        "ListsRooms",
        "ListParticipants",
    ]


class ReallyAllTargets(targets.AllTargets):
    description = "Really render all targets."
    target_classes = list(render.RenderTarget.get_target_classes_by_name())


targets.MinorTools.target_classes.append("MyListParticipants")
