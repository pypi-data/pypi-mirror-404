import abc
import csv
import dataclasses
import datetime
import functools
import pathlib
import re
import subprocess
import warnings
from collections.abc import Callable, Iterable
from typing import Any, ClassVar, TypeVar, Union

import jinja2
from typing_extensions import Self

from .data import Course, Event, Lodgement, Registration, Sortkey

T = TypeVar("T")

TEX_ESCAPE_LOOKUP = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    # Escaping tilde and circumflex with a simple backslash
    # would instead result in applying them as diacritics.
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    # Escaping a single backslash with a backslash
    # would cause a newline instead of escaping it.
    "\\": r"\textbackslash{}",
    # Replace double quotes with double single quotes
    # as the former is a shorthand for umlaute when using babel for german.
    # Prefer using ``Foobar'' instead.
    '"': "''",
    # Using a square bracket can cause unintended behaviour
    # when they are the first non-whitespace character after some commands
    # which take optional arguments like `\item`.
    "[": "{[}",
}


def escape_tex(value: str | None, linebreaks: bool = False) -> str:
    """
    Escaping filter for the LaTeX Jinja2 environment.

    :param value: The raw string to be escaped for usage in TeX files
    :param linebreaks: If true, linebreaks are converted to TeX linebreaks ("\\")
    :return: The escaped string
    """
    if value is None:
        return ""

    res = re.sub(
        "|".join(f"({re.escape(c)})" for c in TEX_ESCAPE_LOOKUP),
        # Lookup content of match (group 0) in escape table.
        lambda match: TEX_ESCAPE_LOOKUP[match[0]],
        value,
    )

    if linebreaks:
        return res.replace("\n", r"\\")
    return res


def filter_inverse_chunks(value: Iterable[T], n: int = 2) -> Iterable[T]:
    """
    A generator to be used as jinja filter that reverses chunks of n elements from the given iterator.
    The last element will be repeated to fill the last chunk if neccessary.

    :param value: Input iterator
    :param n: Chunk size
    """
    end = False
    iterator = iter(value)
    while not end:
        chunk = []
        for i in range(n):
            try:
                chunk.append(next(iterator))
            except StopIteration:
                end = True
                if not chunk:
                    break
                for _ in range(i, n):
                    chunk.append(chunk[-1])
                break
        yield from reversed(chunk)


def filter_date(value: datetime.date | None, format: str = "%d.%m.%Y") -> str:
    """
    A filter to format date values.

    :param format: a format string for the strftime function
    """
    if value is None:
        return ""
    return value.strftime(format)


def filter_datetime(
    value: datetime.datetime | None,
    format: str = "%d.%m.%Y~%H:%M",
    timezone: datetime.timezone = datetime.timezone.utc,
) -> str:
    """
    A filter to format date values.

    :param format: a format string for the strftime function
    :param timezone: A timezone to convert the datetime object to before formatting
    """
    if value is None:
        return ""
    return value.astimezone(timezone).strftime(format)


def override_from_datafield(
    value: object, obj: Union[Registration, Course, Lodgement], field_name: str | None
) -> object:
    """
    Jinja filter to replace a given value with a data field from the given object if that field has been filled with a
    true-ish value.

    Usage example::

        registration.name.common_forename|override_from_datafield(registration, "forename_replacement")|e
    """
    if field_name and obj.fields.get(field_name):
        return obj.fields[field_name]
    return value


def find_asset(
    file_names: Union[None, str, Iterable[str]],
    asset_dirs: Iterable[pathlib.Path],
    *,
    format_data: dict[str, Any] | None = None,
) -> str | None:
    """
    Search the given asset directories for an asset matching one of the file names and return its full path with '/'
    delimiters (to be used in TeX).

    The first asset directory is searched for all alternative file names before moving on to the second directory.

    :param file_names: List of filename to search for. May contain format placeholders. May contain '/' to search
        in subdirectories. May be a single string.
    :param format_data: If given, format into given file names.
    :param asset_dirs: List of asset directories to search for the given asset name
    """
    if file_names is None:
        return None
    if isinstance(file_names, str):
        file_names = [file_names]
    for d in asset_dirs:
        for name in file_names:
            if format_data:
                name = name.format(**format_data)
            fullname = d / name
            if fullname.exists():
                # make an explict conversion to posix paths, since this is expected by TeX
                return fullname.as_posix()
            asset_files = [f for f in d.glob(f"{name}.*") if f.suffix != ".svg"]
            if asset_files:
                return asset_files[0].as_posix()
    return None


def get_latex_jinja_env(
    template_paths: list[pathlib.Path], asset_paths: list[pathlib.Path], timezone: datetime.timezone
) -> jinja2.Environment:
    """
    Factory function to construct the Jinja2 Environment object. It sets the template loader, the Jinja variable-,
    block- and comment delimiters, some additional options and the required filters and globals.

    :param template_paths: A list of directories to be passed to the jinja2.FileSystemLoader to search for templates
    :param asset_paths: A list of directories to be searched for assets, using the `find_asset` template function
    :param timezone: The timezone to show timestamps in
    :return: The configured Jinja2 Environment
    """
    latex_jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_paths),
        block_start_string="<<%",
        block_end_string="%>>",
        variable_start_string="<<<",
        variable_end_string=">>>",
        comment_start_string="<<#",
        comment_end_string="#>>",
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=False,
        extensions=["jinja2.ext.do"],
    )
    latex_jinja2_env.filters["e"] = escape_tex
    latex_jinja2_env.filters["inverse_chunks"] = filter_inverse_chunks
    latex_jinja2_env.filters["date"] = filter_date
    latex_jinja2_env.filters["datetime"] = functools.partial(filter_datetime, timezone=timezone)
    latex_jinja2_env.filters["override_from_datafield"] = override_from_datafield
    latex_jinja2_env.globals["now"] = datetime.datetime.now()
    latex_jinja2_env.globals["find_asset"] = functools.partial(find_asset, asset_dirs=asset_paths)

    return latex_jinja2_env


Fn = TypeVar("Fn", bound=Callable[..., Any])


class ScheduleShutter:
    """
    A small helper class to cancel scheduled function executions by wrapping the functions.
    """

    def __init__(self) -> None:
        self.shutdown = False

    def wrap(self, fun: Fn) -> Fn:
        @functools.wraps(fun)
        def wrapped(*args, **kwargs):  # type: ignore
            if self.shutdown:
                return
            return fun(*args, **kwargs)

        return wrapped  # type: ignore


class CdEDialect(csv.Dialect):
    delimiter = ";"
    quoting = csv.QUOTE_MINIMAL
    quotechar = '"'
    doublequote = True
    lineterminator = "\n"
    escapechar = None


@dataclasses.dataclass(frozen=True)
class RenderTarget(abc.ABC):
    display_name: ClassVar[str]
    description: ClassVar[str]

    disabled: ClassVar[bool] = False

    _all_target_classes: ClassVar[list[type[Self]]] = []

    event: Event = dataclasses.field(compare=False)
    config: dict[str, Any] = dataclasses.field(compare=False)

    tasks: list["RenderTask"] = dataclasses.field(compare=False, init=False, default_factory=list)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} tasks=[{', '.join(repr(task) for task in self.tasks)}]>"

    @functools.cached_property
    def matching_registrations(self) -> list[Registration]:
        warnings.warn(
            "The `RenderTarget.matching_registrations` property is deprecated and will be removed in a future release."
            " Use the `Event.matching_registrations` property instead, via `self.event.matching_registrations`.",
            DeprecationWarning,
        )
        return self.event.matching_registrations

    @abc.abstractmethod
    def create_tasks(self) -> list["RenderTask"]: ...

    @classmethod
    def get_all_target_classes(cls) -> list[type[Self]]:
        return cls._all_target_classes

    @classmethod
    def refresh_global_target_classes(cls) -> None:
        all_targets = []

        def extend(target_class: type[Self]) -> None:
            for subclass in target_class.__subclasses__():
                # Do not include target groups here.
                if subclass is RenderTargetGroup:
                    continue
                # Do not offer disabled classes but still offer their subclasses.
                if not subclass.disabled:
                    all_targets.append(subclass)
                extend(subclass)

        extend(cls)
        cls._all_target_classes = all_targets

    @classmethod
    def get_target_classes_by_name(cls) -> dict[str, type[Self]]:
        return {target_class.__name__: target_class for target_class in cls.get_all_target_classes()}


@dataclasses.dataclass(frozen=True, kw_only=True)
class RenderTask(abc.ABC):
    target: RenderTarget

    display_name: str
    description: str
    base_filename: str
    subdirectory: str = ""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.base_filename}>"

    def __post_init__(self) -> None:
        self.target.tasks.append(self)

    @property
    def job_name(self) -> str:
        return self.base_filename

    @property
    @abc.abstractmethod
    def output_filename(self) -> str: ...

    @property
    def output_filepath(self) -> str:
        if self.subdirectory:
            return f"{self.subdirectory}/{self.output_filename}"
        return self.output_filename

    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, RenderTask):
            return NotImplemented  # type: ignore[unreachable]
        return self._get_sortkey() < other._get_sortkey()

    def _get_sortkey(self) -> Sortkey:
        return (self.target.__class__.__name__, self.base_filename)


@dataclasses.dataclass(frozen=True, kw_only=True, repr=False)
class PDFTask(RenderTask):
    template_name: str
    template_args: dict[str, Any] = dataclasses.field(compare=False)

    @property
    def tex_filename(self) -> str:
        return f"{self.base_filename}.tex"

    @property
    def pdf_filename(self) -> str:
        return f"{self.base_filename}.pdf"

    @property
    def output_filename(self) -> str:
        return self.pdf_filename


@dataclasses.dataclass(frozen=True, kw_only=True, repr=False)
class CSVTask(RenderTask):
    rows: list[dict[str, str]] = dataclasses.field(compare=False)
    fields: list[str] = dataclasses.field(compare=False)
    write_header: bool = True
    csv_dialect: type[csv.Dialect] = CdEDialect

    @property
    def csv_filename(self) -> str:
        return f"{self.base_filename}.csv"

    @property
    def output_filename(self) -> str:
        return self.csv_filename


@dataclasses.dataclass(frozen=True)
class RenderTargetGroup(RenderTarget):
    display_name: ClassVar[str]
    description: ClassVar[str]

    target_classes: ClassVar[list[str]]

    def create_tasks(self) -> list["RenderTask"]:
        targets_by_name = RenderTarget.get_target_classes_by_name()

        tasks = []
        for target_class in self.target_classes:
            tasks.extend(targets_by_name[target_class](self.event, self.config).create_tasks())
        return tasks

    @classmethod
    def get_all_target_group_classes(cls) -> list[type[Self]]:
        return cls.get_all_target_classes()

    @classmethod
    def get_target_group_classes_by_name(cls) -> dict[str, type[Self]]:
        return {
            target_group_class.__name__: target_group_class for target_group_class in cls.get_all_target_group_classes()
        }


def render_template(
    task: PDFTask, output_dir: pathlib.Path, jinja_env: jinja2.Environment, cleanup: bool = True
) -> bool:
    """
    Helper method to do the Jinja template rendering and LuaLaTeX execution.

    :param task: A PDFTask to define the job to be done. It contains the following fields:
        job_name: TeX jobname, defines filename of the output files
        template_name: filename of the Jinja template to render and compile
        template_args: dict of arguments to be passed to the template
        double_tex: if True, execute LuaLaTeX twice to allow building of links, tocs, longtables etc.
    :param output_dir: Output directory. Absolute or relative path from working directory.
    :param jinja_env: The jinja Environment to use for template rendering
    :param cleanup:
    :return: True if rendering was successful
    """
    # Get template
    try:
        template = jinja_env.get_template(_override_template_name(task.template_name))
    except jinja2.TemplateNotFound:
        template = jinja_env.get_template(task.template_name)

    if task.subdirectory:
        output_dir /= task.subdirectory
        output_dir.mkdir(parents=True, exist_ok=True)

    # render template
    with open(output_dir / task.tex_filename, "w", encoding="utf-8") as outfile:
        outfile.write(template.render(**task.template_args))

    # Execute LuaLaTeX once
    print(f"Compiling {task.job_name} ...")
    process = subprocess.Popen(
        ["latexmk", "-lualatex", "--interaction=batchmode", task.tex_filename],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=output_dir,
    )
    process.wait()
    rc = process.returncode
    success = True
    if rc != 0:
        print(f"Compiling '{task.job_name}' failed.")
        success = False

    # Clean up
    if cleanup and success:
        exp = re.compile(rf"^{re.escape(task.job_name)}\.(.+)$")
        for f in output_dir.iterdir():
            match = re.match(exp, str(f.name))
            if match and match.group(1) not in ("pdf",):
                f.unlink()

    return success


def write_csv(task: CSVTask, output_dir: pathlib.Path) -> bool:
    """Helper to write csv data into a file."""

    if task.subdirectory:
        output_dir /= task.subdirectory
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Writing CSV '{task.job_name}'.")
    with open(output_dir / task.csv_filename, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, task.fields, dialect=task.csv_dialect)
        if task.write_header:
            w.writeheader()
        for row in task.rows:
            w.writerow(row)

    return True


def _override_template_name(template_name: str) -> str:
    """For a given `template_name`, get the name of the associated custom override template."""
    template_path = pathlib.PurePosixPath(template_name)
    result = template_path.with_stem(template_path.stem + ".override")
    return str(result)
