from typing_extensions import Self

from cde_render import data, puzzles, render
from cde_render.default import targets

####################################
# Create your custom targets here. #
####################################

# class MyCustomTarget(render.RenderTarget):
#     display_name = "My Custom Target"
#     description = "Create a custom list of stuff or something."
#
#     def create_tasks(self) -> list[render.RenderTask]:
#         return []


# class MyListParticipants(targets.ListParticipants):
#     display_name = "My Custom Participant List"
#     # Leave out description to inherit.
#
#     def create_tasks(self) -> list[render.RenderTask]:
#         ret = super().create_tasks()
#         if len(ret) > 1:
#             return ret[1:]
#         return ret


#####################################
# Create your nametag puzzles here. #
#####################################

# class Birthday(puzzles.NametagPuzzle):
#     display_name = "Birthday"
#     description = "Has their birthday during any event part."
#     asset_name = "some_asset_name"
#
#     @classmethod
#     def check(cls, target: render.RenderTarget, registration: data.Registration) -> Self | None:
#         parts = {
#             event_part
#             for event_part in registration.parts
#             if registration.parts[event_part].status.is_present and any(
#                 (event_part.begin.year, event_part.begin.month, event_part.begin.day)
#                 <= (year, registration.birthday.month, registration.birthday.day)
#                 <= (event_part.end.year, event_part.end.month, event_part.end.day)
#                 for year in range(event_part.begin.year, event_part.end.year + 1)
#             )
#         }
#         if parts:
#             return cls(target, registration, parts)
#         return None
