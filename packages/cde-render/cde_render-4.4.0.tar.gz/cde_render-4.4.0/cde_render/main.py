#!/usr/bin/env python3
import argparse
import concurrent.futures
import getpass
import importlib.util
import inspect
import locale
import multiprocessing
import pathlib
import subprocess
import sys
import tempfile
import time
import traceback
from collections.abc import Callable, Generator
from typing import Any, NoReturn, TypeVar

import jinja2
import pytz
import requests

from . import common, data, default, render, util
from .aux_data import get_event_data
from .common import NOTO_EMOJI_FONT_URL
from .puzzles import NametagPuzzle
from .render import CSVTask, PDFTask, RenderTarget, RenderTargetGroup, RenderTask

T = TypeVar("T")
Job = tuple[Callable[..., bool], RenderTask, pathlib.Path, tuple[Any, ...]]


def main(default_base_dir: pathlib.Path = pathlib.Path().resolve()) -> NoReturn:
    args = parse_cli_arguments(default_base_dir=default_base_dir)

    if args.version:
        import importlib.metadata

        print(importlib.metadata.version("cde-render"))
        sys.exit(0)

    if args.custom_dir is None:
        custom_dir = default_base_dir / "custom"
        if not custom_dir.is_dir():
            custom_dir = default_base_dir
    else:
        custom_dir = args.custom_dir.resolve()

    if args.setup:
        setup(custom_dir=custom_dir, replace=args.setup_replace)

    if not custom_dir.is_dir():
        print(f"The specified custom directory '{custom_dir!s}' either does not exist or is no directory.")
        sys.exit(1)

    config = read_config(custom_dir, args.definitions)

    # This is consumed by 'RenderTarget.matching_registrations'.
    config.setdefault("cli", {}).setdefault("match_registrations", []).extend(args.match_registrations)
    config.setdefault("cli", {}).setdefault("exclude_registrations", []).extend(args.exclude_registrations)

    try:
        locale.setlocale(locale.LC_TIME, (config["data"]["time_locale"], "UTF-8"))
    except Exception as e:
        print(f"Warning: Could not set locale: {e}")

    import_target_modules(custom_dir)

    # if no targets are given, show help output
    if not args.targets:
        if target_classes := RenderTarget.get_target_classes_by_name().values():
            print("\nNo targets given. Please specify one or more of the following targets:\n")
            print("=== Available targets ===\n")
            max_name_length = max(len(target_class.__name__) for target_class in target_classes)
            for target_class in sorted(target_classes, key=lambda class_: class_.__name__):
                print(
                    common.format_target_description(
                        name=target_class.__name__,
                        description=target_class.description,
                        max_name_length=max_name_length,
                    )
                )

            if target_group_classes := RenderTargetGroup.get_target_group_classes_by_name().values():
                print("\n... and/or specify one or more of the following target groups:\n")
                print("=== Available target groups ===\n")
                max_name_length = max(len(target_group_class.__name__) for target_group_class in target_group_classes)
                for target_group_class in sorted(target_group_classes, key=lambda class_: class_.__name__):
                    print(
                        common.format_target_description(
                            name=target_group_class.__name__,
                            description=target_group_class.description,
                            subtargets=sorted(target_group_class.target_classes),
                            max_name_length=max_name_length,
                        )
                    )

        else:
            print(
                "No targets are available. This script is pretty useless. Take a look at the documentation,"
                " to see, how targets can be added"
            )
        sys.exit(1)

    # read input json file
    event = get_event_data(config, args.input, custom_dir)
    if event is None:
        sys.exit(1)

    if args.output is None:
        output_dir = default_base_dir / "output"
    else:
        output_dir = args.output.resolve()

    if not output_dir.is_dir():
        if _confirm(f"Output directory '{output_dir!s}' does not exist. Create (y/n)? "):
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"Could not create output directory at {output_dir!s}: {e}")
                sys.exit(1)
        else:
            print("Aborting.")
            sys.exit(1)

    tasks = match_targets(set(args.targets), event, config)

    jobs = create_jobs(tasks, output_dir=output_dir, no_cleanup=args.no_cleanup, custom_dir=custom_dir)

    if not jobs:
        print("No jobs created.")
        sys.exit(1)

    sys.exit(not run_jobs(jobs, args.max_threads))


def parse_cli_arguments(default_base_dir: pathlib.Path) -> argparse.Namespace:
    default_threads = max(1, multiprocessing.cpu_count() - 1)

    parser = argparse.ArgumentParser(description="Template renderer for CdE Events")
    parser.add_argument(
        "targets",
        metavar="TARGETS",
        type=str,
        nargs="*",
        help=(
            "Specifies which templates to render. Separate multiple targets with spaces."
            " Run without targets to get a list of available targets."
            ' Specify "TARGET:" to get a list of available task for that target.'
            ' Specify "TARGET:TASK_NAME" to only render that specific task.'
        ),
    )
    parser.add_argument("-v", "--version", action="store_true", help="Print version information, then exit.")
    parser.add_argument(
        "-c",
        "--custom-dir",
        type=pathlib.Path,
        help=(
            "Path of custom directory to find config file, templates and assets."
            " Defaults to the current working directory or a `custom` folder inside."
        ),
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help=(
            "Setup a custom directory by creating a sample config, empty override templates,"
            " and copying the base templates and sample assets."
            " Does not fetch any data or render any templates"
        ),
    )
    parser.add_argument(
        "--setup-replace",
        choices=["replace", "prompt", "skip"],
        default="prompt",
        help=(
            "What to do for differing existing files during setup. Has no effect when not combined"
            ' with --setup. Defaults to "prompt", i.e. ask for every file.'
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        type=pathlib.Path,
        help=(
            "Path of a partial export file. Typically xxx_partial_export_event.json."
            " This is required if you don't want to use the Orga-API."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="Path of the output directory. Defaults to the `output` directory in your current working directory.",
    )
    parser.add_argument(
        "-j",
        "--max-threads",
        type=int,
        default=default_threads,
        help=(
            f"Maximum number of concurrent template renderings and LuaLaTeX compile processes. "
            f"Defaults to {default_threads} on your system."
        ),
    )
    parser.add_argument(
        "-n",
        "--no-cleanup",
        action="store_const",
        const=True,
        default=False,
        help="Don't delete rendered template and LaTeX auxiliary files after compilation.",
    )
    parser.add_argument(
        "-D",
        action="append",
        dest="definitions",
        default=[],
        help=(
            "Override a specific config value in the format `-D section.key=value`. This can be used "
            "to try config options temporarily. Might be specified multiple times with different "
            "options. The whole argument is parsed as a TOML document. This means, for setting a "
            "string value, you need to pass double quotes, but make sure that your shell does not "
            "interpret them. Example:\n"
            '-D layout.logo_file=\\"a_different_logo.pdf\\"'
        ),
    )
    parser.add_argument(
        "-r",
        "--registration",
        action="append",
        dest="match_registrations",
        default=[],
        help=(
            "Name of a person registered for the event. Limits some targets to only consider"
            " matching registrations. Can be given multiple times. Can be a regex pattern."
            " Needs to match either the name or CdEDB-ID of the user."
        ),
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        dest="exclude_registrations",
        default=[],
        help=(
            "Name of a person registered for the event. Limits some targets to exclude"
            " matching registrations. Can be given multiple times. Can be a regex pattern."
            " Needs to not match the name and CdEDB-ID of the user."
        ),
    )
    return parser.parse_args()


def _confirm(prompt: str) -> bool:
    return input(prompt).lower() in {"y", "yes", "j", "ja"}


def _download_file(url: str, output_path: pathlib.Path) -> None:
    with output_path.open("wb") as f:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            # print(f"{int(r.headers["Content-Length"]) / 2 ** 20:.2f} MB")
            for chunk in r.iter_content(chunk_size=2**16):
                f.write(chunk)
            print(f"Downloaded {output_path.name!r}.")


def setup(custom_dir: pathlib.Path = pathlib.Path().resolve(), replace: str = "prompt") -> NoReturn:
    print(f"Target for custom directory is: '{custom_dir!s}'")
    if custom_dir.name != "custom":
        if _confirm("Set up subdirectory 'custom' (y) or use this directory (n) for custom config and templates? "):
            custom_dir /= "custom"

    if custom_dir.is_dir() and any(custom_dir.iterdir()):
        if not _confirm("Custom directory not empty. Continue anyway? (y/n)? "):
            sys.exit(1)

    def maybe_copy(
        source: pathlib.Path | str, destination: pathlib.Path, confirm_msg: str, *, replace_without_prompt: bool = True
    ) -> None:
        if isinstance(source, pathlib.Path):
            source_bytes = source.read_bytes()
        else:
            source_bytes = source.encode("utf-8")
        if destination.is_file() and source_bytes == destination.read_bytes():
            # print(f"File {destination} is already identical. Skipping.")
            return
        if (
            not destination.exists()
            or (replace == "replace" and (replace_without_prompt or _confirm(confirm_msg)))
            or (replace == "prompt" and _confirm(confirm_msg))
        ):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source_bytes)

    # 1. Create (empty) custom dir.

    custom_dir.mkdir(parents=True, exist_ok=True)

    # 1.1. Copy sample config.

    config = custom_dir / "config.toml"
    maybe_copy(
        default.CONFIG,
        config,
        "Custom config already exists. Overwrite (y) or skip (n)? ",
        replace_without_prompt=False,
    )

    # 1.2. Copy "empty" targets.py.

    samples_source = pathlib.Path(__file__).parent / "samples"
    msg = "Differing custom targets.py already exists. Overwrite (y) or skip (n)? "
    maybe_copy(
        samples_source / "empty_targets.py",
        custom_dir / "targets.py",
        msg,
        replace_without_prompt=False,
    )

    msg = "Differing custom README already exists. Overwrite (y) or skip (n)? "
    maybe_copy(
        samples_source / "README.md",
        custom_dir / "README.md",
        msg,
        replace_without_prompt=False,
    )

    # 1.4. Create empty assets dir.

    assets_dir = custom_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print("Initialized 'config.toml', 'targets.py' and 'assets' directory.")

    # 1.5. Potentially install a default emoji font.
    noto_emoji_font_path = assets_dir / "NotoColorEmoji.ttf"
    if not noto_emoji_font_path.exists() and _confirm("Install 'Noto Color Emoji' font (~10 MB) (y/n)? "):
        _download_file(NOTO_EMOJI_FONT_URL, noto_emoji_font_path)

    # 2. Create templates dir.

    templates_dir = custom_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # 2.1. Copy override templates.

    for override_template in (default.TEMPLATES / "overrides").glob("_*base.override.tex"):
        msg = f"Differing override template '{override_template.name}' already exists. Overwrite (y) or skip (n)? "
        maybe_copy(override_template, templates_dir / override_template.name, msg)

    # 2.2. Create empty override templates for every base template.

    override_template_template = (default.TEMPLATES / "overrides" / "_override.txt").read_text()
    for target_template in default.TEMPLATES.glob("[!_]*.tex"):
        override_template = templates_dir / f"{target_template.stem}.override.tex"
        msg = f"Differing override template '{override_template.name}' already exists. Overwrite (y) or skip (n)? "
        maybe_copy(override_template_template.format(template_name=target_template.name), override_template, msg)

    print("Initialized 'templates' directory with empty override templates.")

    # 3. Create samples dir.

    samples_dir = custom_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # 3.1. Copy default targets into samples dir.

    msg = "Differing default targets already exist. Overwrite (y) or skip (n)? "
    maybe_copy(pathlib.Path(__file__).parent / "default" / "targets.py", samples_dir / "default_targets.py", msg)

    # 3.2. Copy sample custom targets into sample dir.

    msg = "Differing sample targets already exist. Overwrite (y) or skip (n)? "
    maybe_copy(samples_source / "targets.py", samples_dir / "targets.py", msg)

    # 3.3. Copy default assets into samples dir.

    for asset in default.ASSETS.iterdir():
        msg = f"Differing sample asset {asset.name} already exists. Overwrite (y) or skip (n)? "
        maybe_copy(asset, samples_dir / "assets" / asset.name, msg)

    # 3.4. Copy default templates into samples dir.

    for base_template in default.TEMPLATES.glob("_*base.tex"):
        msg = f"Differing base template '{base_template.name}' already exists. Overwrite (y) or skip (n)? "
        maybe_copy(base_template, samples_dir / "templates" / base_template.name, msg)

    for target_template in default.TEMPLATES.glob("[!_]*.tex"):
        msg = f"Differing template '{target_template.name}' already exists. Overwrite (y) or skip (n)? "
        maybe_copy(target_template, samples_dir / "templates" / target_template.name, msg)

    print("Initialized sample targets, assets and templates. You can reference them in the 'samples' directory.")

    # 4. Setup orga token.

    config = read_config(custom_dir, [])
    if config.get("api") and config["api"].get("token_file"):
        token_path = (custom_dir / config["api"]["token_file"]).resolve()
        msg = "If you have an Orga-Token paste it here to setup data retrieval via API. (Leave empty to continue) "
        if orga_token := getpass.getpass(msg).strip():
            msg = f"Differing token file '{token_path}' already exists. Overwrite (y) or skip (n)? "
            maybe_copy(orga_token, token_path, msg)

    # 5. Setup git repository.

    if not (custom_dir / ".git").exists() and _confirm("Set up local git repository (y/n)? "):
        msg = "Differing  '.gitignore' already exists. Overwrite (y) or skip (n)? "
        maybe_copy(samples_source / ".gitignore", custom_dir / ".gitignore", msg)
        subprocess.call(["git", "init"], cwd=custom_dir)
        subprocess.call(["git", "add", "."], cwd=custom_dir)
        subprocess.call(["git", "commit", "-m", "Initial commit"], cwd=custom_dir)

    print("All set up!")
    sys.exit(0)


def merge_into_dict(target: dict[T, Any], overrides: dict[T, Any]) -> None:
    """
    Update/extend `target` recursively by adding/merging/overriding entries from `overrides`
    """
    for k, v in overrides.items():
        if k in target and isinstance(v, dict) and isinstance(target[k], dict):
            merge_into_dict(target[k], v)
        else:
            target[k] = v


def read_config(custom_dir: pathlib.Path, definitions: list[str]) -> dict[str, Any]:
    try:
        import tomllib as toml

        TomlDecodeError = toml.TOMLDecodeError
        binary_toml = True
    except ImportError:
        import toml

        TomlDecodeError = toml.TomlDecodeError
        binary_toml = False

    with open(default.CONFIG, mode="rb" if binary_toml else "r") as f:
        # Warning: This is either tomllib (https://docs.python.org/3/library/tomllib.html)
        #   or the toml library (https://github.com/uiri/toml)
        config = toml.load(f)
    assert isinstance(config, dict)
    custom_config_file = custom_dir / "config.toml"
    if custom_config_file.is_file():
        with custom_config_file.open(mode="rb" if binary_toml else "r") as f:
            merge_into_dict(config, toml.load(f))
    else:
        print(f"Warning: No config file at {custom_config_file}.")

    for definition in definitions:
        try:
            # Warning: This is either tomllib (https://docs.python.org/3/library/tomllib.html)
            #   or the toml library (https://github.com/uiri/toml)
            def_data = toml.loads(definition)
        except TomlDecodeError as e:
            print(f"Invalid cli definition '{definition}': {e}")
            continue
        merge_into_dict(config, def_data)
    return config


def import_target_modules(custom_dir: pathlib.Path | None) -> None:
    from .default import targets  # noqa: F401

    NametagPuzzle.refresh_global_puzzle_classes()
    RenderTarget.refresh_global_target_classes()
    RenderTargetGroup.refresh_global_target_classes()

    if custom_dir:
        custom_targets_file = custom_dir / "targets.py"
        if custom_targets_file.is_file():
            spec = importlib.util.spec_from_file_location("custom.targets", custom_targets_file)
            if spec:
                foo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(foo)  # type: ignore
                NametagPuzzle.refresh_global_puzzle_classes()
                RenderTarget.refresh_global_target_classes()
                RenderTargetGroup.refresh_global_target_classes()


def match_targets(targets: set[str], event: data.Event, config: dict[str, Any]) -> list[RenderTask]:
    target_classes_by_name = RenderTarget.get_target_classes_by_name()
    target_group_classes_by_name = RenderTargetGroup.get_target_group_classes_by_name()

    if not target_classes_by_name:
        raise RuntimeError("No RenderTargets registered. Cannot match targets.")

    tasks: list[RenderTask] = []
    for target in targets:
        target_name, task_name = target.split(":", 1) if ":" in target else (target, None)

        if target_class := target_classes_by_name.get(target_name):
            new_tasks = target_class(event, config).create_tasks()
        elif target_group_class := target_group_classes_by_name.get(target_name):
            new_tasks = target_group_class(event, config).create_tasks()
        else:
            print(f"Unknown target {target!r}.")
            continue

        if task_name is not None:
            new_tasks_by_name = {task.base_filename: task for task in new_tasks}
            # TODO: Allow matching multiple tasks at once, perhaps using re.
            if task := new_tasks_by_name.get(task_name):
                tasks.append(task)
            elif task_name:
                print(f"Unknown task {task_name!r} for target {target_name!r}.")
            if not task:
                print(f"Available tasks: {', '.join(map(repr, new_tasks_by_name.keys()))}.")
        else:
            tasks.extend(new_tasks)

    return sorted(set(tasks))


def create_jinja2_environment(
    event: data.Event, config: dict[str, Any], *, custom_dir: pathlib.Path | None = None
) -> jinja2.Environment:
    # Initialize lists of template and asset directories
    template_dirs = [default.TEMPLATES]
    if custom_dir:
        custom_template_dir = custom_dir / "templates"
        if custom_template_dir.is_dir():
            template_dirs.insert(0, custom_template_dir)

    asset_dirs = [default.ASSETS]
    if custom_dir:
        custom_asset_dir = custom_dir / "assets"
        if custom_asset_dir.is_dir():
            asset_dirs.insert(0, custom_asset_dir)

    # Construct Jinja environment
    timezone = pytz.timezone(config.get("data", {}).get("timezone"))
    jinja_env = render.get_latex_jinja_env(template_dirs, asset_dirs, timezone)
    jinja_env.filters["int_to_words"] = util._int_to_words_filter
    jinja_env.filters["override"] = util._override_filter
    jinja_env.filters["phone"] = common.phone_filter
    jinja_env.globals["CONFIG"] = config
    jinja_env.globals["EVENT"] = event
    jinja_env.globals["ENUMS"] = {e.__name__: e for e in common.ALL_ENUMS}
    jinja_env.globals["UTIL"] = util

    return jinja_env


def create_jobs(
    tasks: list[RenderTask],
    *,
    output_dir: pathlib.Path,
    no_cleanup: bool = False,
    custom_dir: pathlib.Path | None = None,
) -> list[Job]:
    if not tasks:
        return []

    jinja_env = create_jinja2_environment(tasks[0].target.event, tasks[0].target.config, custom_dir=custom_dir)

    jobs: list[Job] = []
    for task in tasks:
        if isinstance(task, PDFTask):
            jobs.append((render.render_template, task, output_dir, (jinja_env, not no_cleanup)))
        elif isinstance(task, CSVTask):
            jobs.append((render.write_csv, task, output_dir, ()))
        else:
            print(f"Warning: Unhandled task type: {task!r}. Skipping.")
    return jobs


def gather_all_tasks(
    event: data.Event, config: dict[str, Any], custom_dir: pathlib.Path | None = None
) -> list[RenderTarget]:
    import_target_modules(custom_dir)

    ret = []

    for target_class in RenderTarget.get_all_target_classes():
        if inspect.isabstract(target_class):
            print(f"RenderTarget subclass {target_class!r} is abstract. Skipping.")
            continue
        target = target_class(event, config)
        target.create_tasks()
        ret.append(target)

    return ret


def match_and_render(
    targets: set[str], event: data.Event, config: dict[str, Any], custom_dir: pathlib.Path | None = None
) -> Generator[tuple[RenderTask, bytes | None]]:
    """Match the given targets to the event, render them and yield the results as they finish."""
    import_target_modules(custom_dir=custom_dir)
    tasks = match_targets(targets, event, config)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = pathlib.Path(tmpdir)
        jobs = create_jobs(tasks, output_dir=tmppath, no_cleanup=False, custom_dir=custom_dir)
        cpu_count = max(1, multiprocessing.cpu_count() - 1)

        for successful_task in run_jobs_concurrently(jobs, cpu_count):
            try:
                print(f"Rendered {successful_task}.")
                yield (successful_task, (tmppath / successful_task.output_filepath).read_bytes())
            except FileNotFoundError:
                print(f"Failed to read output for {successful_task}.")
                yield (successful_task, None)


class JobsFailedError(Exception):
    pass


def run_jobs(jobs: list[Job], max_workers: int) -> bool:
    """Wrapper around the runner coroutine that waits for them to finish and returns True if all succeeded."""
    try:
        sum(1 for _ in run_jobs_concurrently(jobs, max_workers))
    except JobsFailedError:
        return False
    return True


def run_jobs_concurrently(jobs: list[Job], max_workers: int) -> Generator[RenderTask]:
    """
    Runs the given jobs in the given number of worker threads, yielding the successful tasks as they are finished.
    """
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        print(f"Starting {len(jobs)} Tasks, {max_workers} at a time ...")

        # Wrap the rendering jobs in a shutter to be able to cancel all remaining jobs.
        shutter = render.ScheduleShutter()
        # Map the submitted futures to the tasks they contain...
        futures = {}
        for fun, task, output_dir, args in jobs:
            future = executor.submit(shutter.wrap(fun), task, output_dir, *args)
            futures[future] = task

        try:
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        # ... so we can yield the successful tasks as the finish.
                        yield futures.pop(future)
                except Exception as exc:
                    traceback.print_exception(type(exc), exc, exc.__traceback__)
        except (KeyboardInterrupt, SystemExit):
            shutter.shutdown = True
            print("Waiting for running compile tasks to be finished ...")
            executor.shutdown()
            print("All pending compile tasks have been cancelled. Stopping.")
            return

    time_taken = time.time() - start_time
    print(f"Finished all tasks in {time_taken:.2f} seconds.")
    # Any unsuccessful tasks remain in here.
    if futures:
        print(
            f"{len(futures)} of {len(jobs)} render tasks failed. See above exceptions or LuaLaTeX log files\n"
            "for more information"
        )
        raise JobsFailedError(len(futures))
