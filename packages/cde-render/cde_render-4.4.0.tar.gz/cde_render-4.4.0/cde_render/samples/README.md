# Custom templates, assets and targets for use with the `cde_template_renderer` for EVENT XY.

## Overview

- Configuration options are in [config.toml](config.toml).
- Custom templates and overrides for default templates are in [templates](templates).
- Custom assets are in [assets](assets).
- The default targets, assets and templates are available in [samples](samples) for reference.

### How to use these custom targets

*Explain your custom targets and how to use them here.*

## How to create custom targets, templates, overrides and assets

First have a look at some of the configuration options in the [config.toml](config.toml).

You can include custom assets or override the default by placing them in the [assets](assets) directory.
Assets in there will be preferred over default assets with the same name.
You can view the default assets in the [samples -> assets](samples/assets) directory.

### More customization

If you need more customization than the config plus custom assets can provide you have two other options:

You can override specific sections of the default templates using the override templates in the [templates](templates) directory.
For more information on overriding templates see the template renderers
[README](https://tracker.cde-ev.de/gitea/orgas/cde_template_renderer_v3#templates).

You can create new targets or override default targets in [targets.py](targets.py).
For more information see the template renderers [README](https://tracker.cde-ev.de/gitea/orgas/cde_template_renderer_v3#targets).
