
# cde-render – CdE Event Template Renderer

This repository contains a Python 3 script to render LaTeX based participant lists, course lists, nametags,
participation letters (“Teilnahmebriefe”) and other documents, as well as a set of configurable LaTeX templates for
these documents.

The templates are rendered to TeX files using the Jinja2 template engine, and afterwards compiled with LuaLaTeX. A set
of Python functions creates the rendering tasks (including the selection of a template and calculation of additional
data) for different targets. The tasks are rendered and compiled in parallel to make use of multiprocessors for the
time-consuming LaTeX compilation. 

The default target functions, templates and configuration data can be extended and overridden to adapt the documents
to the needs of a specific CdE events.



## Setup

### Prerequisites

You need the following software on your computer:

* Python 3.10 or higher

* A LaTeX installation with LuaLaTeX and
    * koma-script
    * colortbl
    * xcolor
    * longtable
    * tikz
    * libertine (the *Linux Libertine* font) for the default templates

`lualatex` must be available in the $PATH to be called by the Python script.

#### Setting up Prerequisites on Linux systems

… on Ubuntu & Debian:
```bash
sudo apt install python3 texlive-latex-base texlive-latex-recommended texlive-latex-extra \
                 texlive-luatex texlive-fonts-extra texlive-lang-german
```

… on Arch Linux:
```bash
sudo pacman -S python texlive-core texlive-fontsextra
```


#### Setting up Prerequisites on Windows systems

* Download and run the "Windows x86-64 executable installer" of the latest Python 3 release from
  https://www.python.org/downloads/windows/
  * Select *Add Python 3.X to PATH* before installing
  * You may want to use the *Customize installation* menu to install Python for all users and disable unnecessary
    components. Only *pip* is required. In this case you should make sure that *Add Python to the Environment variables*
    is checked.
* Download and run the latest MiKTeX installer from https://miktex.org/download
* (Optional) if you want to install and update the template rendering scripts via Git, download and run the latest
  "64-bit Git for Windows Setup" from https://git-scm.com/download/win
  * It's recommended to "Use the Nano editor by default"
  * All other default settings are typically good
* Log off and on again, to make sure, your %PATH% is up to date


### Installation

Create a new folder. This will become your *custom folder*.

Open up a terminal in that folder (on Windows preferably a *Git Bash*).

Depending on how you want to install the script there are different options on how to proceed.

If you simply need to _run_ the script to generate the default templates or templates that someone already created, the easiest way is by [using uvx](#uvx), however this requires you to [install uv(x)](https://docs.astral.sh/uv/getting-started/installation/#pypi).

If you want or need to write custom templates, targets, etc. you should install this script into a virtual environment. This can also be done [using uv](#uv-venv), but is also possbile [using just python](#python-venv), without needing to install anything further.

#### uvx

You can tun this script without further setup using [uv(x)](https://docs.astral.sh/uv/getting-started/installation/#pypi).

This will automatically create a temporary single-use virtual environment in the background. (Don't worry about this if you don't know what that means, it is not important).

You can use

```bash
uvx cde-render
```

to automatically run the most up-to-date version of this script.

You can use

```bash
uvx cde-render@latest
uvx cde-render@4.3.0
```

to run the specific versions of this script instead.

You can use

```bash
uv tool install cde-render
uv tool install cde-render@latest
uv tool install cde-render@4.3.0
```

to install (a specific version of) this script, which will then be used as the default when using ``uvx`` even if newer versions become available.

#### uv venv

You can also use [uv](https://docs.astral.sh/uv/getting-started/installation/#pypi). to set up a (persistent, reusable) virtual environment like this:

```bash
uv venv
uv pip install cde-render
```

And then run the script using

```bash
uv run cde-render
```

or by activating the virtual environment using

```bash
. .venv/bin/activate
cde-render
```

To update the script use:

```bash
uv pip install -U cde-render
```

#### python venv

You can also use pythons build in ``venv`` module to create a (persistent, reusable) virtual environment.

```bash
python3 -m venv venv
. venv/bin/activate
pip install cde-render
```

To upgrade to the latest master version, open up a terminal within your custom folder and type:
```bash
pip install -U cde-render
git pull
```

In order to run the script, open up a terminal within your custom folder and type:
```bash
. venv/bin/activate
```

You should see `(venv)` appear at the beginning of every new line. This means your virtual environment is activated.
All further steps will assume that this is the case, so make sure that it is.

You can check if everything worked by typing:
```bash
cde-render
```

You should see a list of available targets and target groups.

### Collation

The template renderer has support for collation, meaning natural language sorting. This will enable numbers within strings to
be sorted numerically instead of lexicographically, letters with accents or umlauts to be sorted like their base variants, etc.
E.g. without collating the list `["A-1", "A-10", "A-2"]` is already sorted, but with collating it will be sorted as `["A-1", "A-2", "A-10"]` instead. 

To enable support for collating you can attempt to install the `pyicu` dependency by adding `[icu]` during installation as shown above:

```bash
uvx cde-render[icu]

# or
uv pip install cde-render[icu]

# or
pip install cde-render[icu]
```

For this to work, you need to install some prerequisites first. You can find more information [here](https://pypi.org/project/pyicu/).

For Ubuntu & Debian:

```bash
sudo apt install python3-dev g++ pkg-config libicu-dev
```

You can also install ``pyicu`` via ``apt``, though you will need to make that available to your virtual environment:

```bash
sudo apt install python3-icu
```

The ``cde_render.common.COLLATING`` variable will be set to ``True`` if collating was set up successfully.


## Usage

Regardless of how you installed this script, the following will assume that you are running it as

```bash
cde-render
```

Depending on your choice of installation, you may need to substitute

```bash
uvx cde-render

# or
uv run cde-render

# or
. venv/bin/activate
cde-render
```

accordingly.

### Data source

To render and compile PDF file, first you need to provide a data source. This can either be a partial event export downloaded
from CdEDB or an CdEDB-Orga-Token to automatically retrieve this data from the CdEDB.

#### API

Create a new Orga-Token, copy it into a plain text file, then adjust the `[api]` section of your
[Configuration](#configuration-options) to point to that file.

You can create a Token here:

CdEDB -> Events -> EVENT_NAME -> Downloads & Import -> Orga-Tokens -> Create Orga Token.

An orga token has an expiration date that cannot be adjusted later, after which it will no longer work. Don't set this too far
into the future. You can always create a new token later if necessary or revoke an existing token.

#### Partial export

Alternatively you can manually download a partial event export from the CdEDB and place it in your custom directory.
You can find the export here:

CdEDB -> Events -> EVENT_NAME -> Downloads -> Partial Event Export -> JSON file

To use the downloaded file instead of the API invoke the script using:

```bash
cde-render -i xxx_partial_export_event.json
```
where `xxx_partial_export_event.json` is the file (or the path to the file) you downloaded.

### Targets

Open up a terminal in your custom directory and type:

```bash
cde-render TARGETS
```
where `TARGETS` is a space-separated list of the targets and/or target groups you want to render and compile.
You will be prompted to install the required LaTeX packages on the first run with targets if you haven't done so already.

If you are not sure about the available targets and their names, run the Python script without any targets to get a list
of all targets with a description.

You can limit the rendering to only specific tasks of a target, by specifying the target in combination with the task name:

```bash
cde-render Nametags:nametags_A
cde-render ListsRooms:lists_rooms_O1 ListsRooms:room_lists_O2
```

The first command will only generate nametags for the part with the shortname `A`.
The second will only generate participation letters for the registrations with the `id` 1 and 3.

You can use `TARGET:` to see a list of all the tasks available under that target.

Some Targets (currently `Nametags`, `DepartureNametags`, `ParticipationLetters`, `Envelopes` and `DonationReceipts`) also allow
you to specify a registration or list of registrations to limit their output:

```bash
cde-render Nametags -r "Mickey Mouse" -r DB-1-9 -r DB-2-5
cde-render ParticipationLetters -r "D* Duck"
cde-render ParticipationLetters -r "Duck" -e "Donald"
```

The first command will generate only nametags for Mickey and whomever has the persona id 1 (because "DB-2-5" is not a valid DB-ID).
The second one will create letters for both Donald and Daisy Duck, but not Scrooge McDuck, even if he has set "Dagobert" as his nickname.
The third command will create letters for Daisy Duck and Scrooge McDuck but not Donald Duck.

### Command line parameters

To get an overview over all available parameters, use
```bash
cde-render --help
```

The most important parameters are:
* `-c CUSTOM_DIR` to specify a custom directory (see Customization) different from the default.
* `-r REGISTRATION_NAME1 [-r REGISTRATION_NAME2, ...]`
  to specify any number of registrations to limit some outputs to only those registrations.
  These are interpreted as regex patterns (which means that `()` will not behave like you might expect).

  This can match the registrations CdEDB-ID as well as their name, specifically:
  given names + family name or nickname + family name or given names + (nickname) + family name.
* `-e REGISTRATION_NAME1 [-e REGISTRATION_NAME2, ...]`
  to specify any number of registrations to exclude from some outputs.
  This works exactly like the `-r` parameter above and can be combined with it.

If you have a different custom directory be sure to include the `-c` parameter when running the script, to have custom targets,
templates and assets available.
Run the script without specifying targets to get a full list of all available targets (default targets and custom targets). 


## Customization

There are four different ways to customize the rendered PDF files for a specific CdE event:

* changing configuration options
* overriding and adding asset files
* overriding and adding targets
* overriding and adding templates

To get started with customization run:
```bash
cde-render --setup
```

First you will be prompted whether to create a `custom` subdirectory.
If you select `yes` two directories and a few files will be created in the new sub directory.
If you select `no` they are created in the current working directory instead.
If any of these files already exist and differ you will be prompted whether you want to replace them.

You can rerun this command later to revert any of your overrides or create any new ones created in an update.
Be sure to **use version control for your existing overrides**, and/or use the `--setup-replace skip` option to not lose
any of your customizations when doing so.

Start by customizing the default templates using the default configuration options.
If this is not sufficient for a certain template or use case (typically, the `tnletter.tex` template is such a case),
take a look into overriding some of the templates.
The templates' structure is designed to allow overriding selected portions without touching (or even understanding) the rest.
At the same time, they profit from code reuse, so only few overrides are required to effect the look of multiple documents.

If you want to add your own render targets and templates or do more sophisticated preprocessing of the rendered data
(e.g. filtering participants by certain criteria), you'll need to override targets or add your own.


### Configuration Options

Configuration options are read from two TOML files: The default config and the `config.toml` in your custom directory, if present.
Options in the custom `config.toml` override equally named options in the same section of the default config.
For a syntax reference, please refer to the official TOML specification: https://github.com/toml-lang/toml/blob/v0.5.0/README.md

If you used the `--setup` command from the [Customization](#customization) section, your custom folder contains a copy of the
default config that you are free to adjust.
Be sure to apply version control of your choice (e.g. Git, SVN, Mercurial, …) to your custom directory to keep track of
changes to your customization and/or share it with your fellow orgas.

You can easily add new sections and options to your custom `config.toml` and use them for easy adjustments in your overriden
or added templates and targets.
The configuration is available to the templates in the `CONFIG` variable and to targets
in the `self.config` attribute.


### Assets

Asset files are typically graphics or fonts to be used within the templates. The default templates are shipped with
defaullt graphics, especially for the nametags. Additional graphics files can be included by config options (e.g. for
the event logo and course logos) or by overriding the templates. Assets are included into the templates using the
`find_asset()` template function. It searches for file with the requested name in the custom directory's `assets` folder
and – if no matching file has been found – in the default assets folder.

If you used the `--setup` command from the [Customization](#customization) section, your custom folder contains an
`assets` folder with all the default assets, which you are free to replace.
Note that simply removing them will not have any effect, since `find_assets()` will still find them in the default assets.
Simply place a different file with the same name in your custom assets folder and it will be preferred to the default one.

Note that `find_assets` does not care about the exact extension unless you explicitly specify it.
Thus `find_asset("meal_vegetarian")` will find any of these files `meal_vegetation.pdf`, `meal_vegetarian.png`,
`meal_vegetarian.jpg`, and others in some (deterministic but unknown (to the author of this README) order of preference).

To use assets in subdirectories of the `assets/` folder, pass the relative path of the asset file to `find_asset()`,
using slashes (`/`) as path delimiter (even on Windows).


### Templates

The templates are rendered to TeX files by the Jinja2 template engine and afterwards compiled to PDF files by LuaLaTeX.
To avoid conflicts of the Jinja template syntax with TeX syntax (esp. considering curly brackets), we use a modified
Jinja environment with different delimiters:

|                | Default Jinja Syntax | Our Syntax           |
|----------------|----------------------|----------------------|
| Expressions    | `{{ expression }}`   | `<<< expression >>>` |
| Tags           | `{% tag %}`          | `<<% tag %>>`        |
| Comments       | `{# ... #}`          | `<<# ... #>>`        | 

This modification is consistent with the syntax of LaTeX templates in the CdE Datenbank source code.
Apart from that, the Jinja2 documentation applies to our templates: https://jinja.palletsprojects.com/en/stable/templates/

We use some global template variables, which are available in every template:

| Variable        | Type          | Description                                                |
|-----------------|---------------|------------------------------------------------------------|
| `EVENT`         | data.Event    | The full event data, as parsed from the CdEdb export file  |
| `CONFIG`        | dict          | The full configuration data from the `config.toml` files   |
| `UTIL`          | module        | The `util.py` module with some utilty functions            |
| `ENUMS`         | dict          | A dict of all enums defined in `data.py` to compare values |
| `now`           | datetime      | The timestamp of the starting of the script                |
| `find_asset`    | function      | Function to get full path of an asset by filename          |

Overriding templates works just like overriding assets: If you used the `--setup` command from the [Setup](#setup) section,
you already have a `templates` folder in your custom directory with all available override templates in them.
(If not, do so now, but be careful not to overwrite your config when prompted).

You can override any base template (which you can view in the `templates/base_templates` folder in your custom directory)
by making changes to any of the corresponding override templates.
Our base templates make heavy use of template inheritance and *blocks*.
In Jinja2, *Blocks* are placeholders with a default content, defined in a base template, which can be overriden by
sub-templates, *extending* this template.

If you really need to make adjustments to the base template itself, in a way that cannot be done with blocks, you will need to
copy that template from the `base_templates` folder into the `templates` folder and make your changes there.
This will take precedence over the default base template.
You can also replace the default template entirely this way, by not having it extend the `_base.tex` template.

The current inheritance tree of the default templates:
```
_base.tex
└── _base.override.tex
    ├── _lists.base.tex
    │   └── _lists.base.override.tex
    │       ├── checklist_arrival.tex
    │       ├── list_courses.tex
    │       ├── list_participants.tex
    │       ├── orga_list_vertrauenspersonen.tex
    │       └── ...
    ├── nametags.tex
    └── envelopes.tex
tnletter.tex
```
The primary purpose of `_base.tex` and `_lists.base.tex` is definition of common LaTeX code, used for all documents or
at least all lists. They may be overridden to change the overall look of the sub-templates.
The `_base.override.tex` and `_lists.base.override.tex` templates are empty by default, i.e. they don't make any changes
to the `_base.tex` resp. `_lists.base.tex` template.
They can be overridden in the custom templates folder to only redefine individual *blocks* of the base templates,
modifying the layout or behaviour of all templates without copying the full base template the custom directory.

In addition, there is an implicit *override* template for each of the target templates:
When the template rendering code searches for a template `some_template.tex` it will first look for a
`some_template.override.tex`. This allows you to create such an override template file in your custom directory, which
*extends* the default template instead of replacing it, e.g.:

`custom/templates/nametags.override.tex`:
```tex
<<% extends "nametags.tex" %>>
<<% block nametag_lodgement %>>
    Deine Unterkunft:\\
    <<< super() >>>
<<% endblock %>>
```

So, the actual template inheritance hierarchy looks more like this:
```
_base.tex
└── _base.override.tex
    ├── _lists.base.tex
    │   └── _lists.base.override.tex
    │       ├── checklist_arrival.tex
    │       │   └── checklist_arrival.override.tex  # if exists
    │       ├── list_courses.tex
    │       │   └── list_courses.override.tex       # if exists
    │       └── ...
    ├── nametags.tex
    │   └── nametags.override.tex                   # if exists
    └── envelopes.tex
        └── envelopes.override.tex                  # if exists
tnletter.tex
└── tnletter.override.tex                           # if exists
```

All of these override templates have already been placed in your custom `templates` directory, but they are empty so don't
do anything yet.

#### Additional Tricks

**Sub-Blocks:**
Sometimes *blocks* are nested within the base templates to allow redefinition of different sized parts of the code. For
example, the `nametags.tex` templates allows to override the nametags' rearside text (`block nametag_reartext`) or
the complete rearside (`block nametag_rearside`). When redefining/overriding a *block*, it es possible to use the
content of another *block*, including sub-blocks, as `<<< self.BLOCKNAME() >>>`. This way, it is possible to override a
*block* to rearrange its sub-blocks, but keep their individual default contents:
```tex
<<% block nametag_rearside %>>
    <<< self.nametag_rearlefticons() >>>
    \hspace{\fill}
    <<< self.nametag_rearrighticons() >>>
    
    
    \vspace{\fill}
    <<< self.nametag_reartext() >>>
<<% endblock %>>
```


**No Cleanup:** By default, the `output/` directory is cleaned up after each successful rendering task. I.e. all files
with the jobname and an extension different from `.pdf` are deleted – including the generated `.tex` file and the
LuaLaTeX `.log`. The command line option `-n` disables this cleanup, which can be quite helpful to debug the templates.


**Lua-Visual-Debug:** The default `_base.tex` templates can include the `lua-visual-debug` LuaTeX packge which will
colorfully highlight all TeX boxes and spaces in the PDF file. This is controlled by the config option
`layout.lua-visual-debug`. It may be temporarily enabled with the `-D` command line option:
```bash
cde-render -D layout.lua-visual-debug=true Nametags
```


### Targets

Targets are defined in the default targets file and you can override them or define your own in the `targets.py` file in the
custom directory.
Targets are subclasses of the abstract class `cde_render.render.RenderTarget` and should declare two class variables:
`display_name` which can be any shortish string that nicely describes the target and `description` which tells the user
what the target does and is shown in the list of available targets along with the name of the target class.

To be valid (and no longer abstract) a target needs to implement the `create_tasks` method, which takes no arguments and
returns a list of `cde_render.render.RenderTask` objects, though that class is also abstract, so actually the target returns a
list of non-abstract render tasks: Either `cde_render.render.PDFTask` to create a PDF via LuaLaTeX, or `cde_render.render.CSVTask` to
simply write a CSV file via python. All tasks also have a `display_name` and `description` attribute, which follow the same
guidelines as the targets but are unimportant when using this script via the CLI. A tasks `base_filename` however can be used
to select this task specifically when rendering the associated target, rather than all of its tasks.

`RenderTargets` have two instance attributes: `event` and `config`. When invoking the script, matching targets will be
instantiated, and `create_tasks` will be called to determine the files that should be rendered. A `CSVTask` is pretty simple
and only contains a list of column headers, a list of data rows and a filename, which is enough to create the CSV file.

A `PDFTask` has a `template_name` and `template_args`. These are the name of the (base) template to be used and the additional
arguments passed to that template respectively.

All children of `cde_render.render.RenderTarget` that do not have any subclasses themselves are automatically made available to be
chosen for rendering. There are no targets with subclasses by default, but you can import them from `cde_render.targets` and create
a subclass to adjust their name, `display_name`, `description` (technically you don't need to inherit from them for these two,
you can just set their class variables), or implementation of `create_tasks`. You can also inherit from then and simply set
`disabled = True` to simply remove them from being chosen.

You can view the default targets in the `default_targets.py` file in your custom directory.
Also have a look at `sample_targets.py`, which shows some examples of what can be done to customize targets.
Changes made there have no effect, your custom targets need to be in `targets.py` in your custom directory.


## Development

For contributing changes to the cde_render core code or default targets/templates, see [development.md](./development.md),
for further information and guidelines.
