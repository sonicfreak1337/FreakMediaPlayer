# Skin system

The player ships with two built-in skins:

- **Freaky** is the original navy, gold and neon-blue interface and the default.
- **Fastilicious** is a black-metal console with red/orange hot-metal accents,
  custom character artwork and matching control icons.

Choose a skin from the `SKIN` dropdown in the application title bar. The choice
is applied immediately and restored on the next launch. The reload button beside
the dropdown rescans custom skins; the `…` button opens their folder.

## Custom skin folder

Put each custom skin in its own directory below:

```text
%LOCALAPPDATA%\FreakMediaPlayer\skins\
```

Example layout:

```text
skins\
  my-skin\
    skin.json
    style.qss
    assets\
      logo.png
      icons\
        play.png
```

## Manifest

`skin.json` uses schema version 1:

```json
{
  "schema_version": 1,
  "id": "my-skin",
  "name": "My Skin",
  "description": "A personal player design",
  "extends": "freaky",
  "stylesheet": "style.qss",
  "colors": {
    "accent": "#ff3ca6",
    "highlight": "#55f5d2",
    "panel_background": "#160c21"
  },
  "assets": {
    "app_logo.png": "assets/logo.png",
    "icons/pause_icon.png": "assets/icons/play.png"
  }
}
```

`extends` accepts `freaky`, `fastilicious`, or `null`. An inherited skin may
omit `stylesheet` and change only colors or assets. A standalone skin with
`"extends": null` must supply a stylesheet. Custom QSS is appended to the base
skin, so a small file can override only the selectors that need to change.

The optional `colors` object changes the Qt palette, custom-painted controls and
matching colors in the inherited stylesheet. Available semantic roles are:

```text
background, panel_background, panel_sunken, panel_border,
header_background, header_highlight, text_primary, text_secondary,
display, accent, highlight, playing_row_background, playing_row_text,
artwork_background, artwork_border, spectrum_active, spectrum_inactive,
graph_background, graph_band, graph_band_disabled
```

## Assets

Asset keys are the logical paths used by the player. Any omitted asset falls back
to the packaged artwork, so a skin can replace one icon or the complete set.
Explicit mappings in `skin.json` may use any file name inside the skin folder.

As a shortcut, an asset with the same logical path can be placed below the
skin's `assets` directory without adding it to the manifest. For example:

```text
assets\app_logo.png
assets\icons\next_icon.png
assets\icons\repeat_one_on.png
```

The logical icon names are the file names in
`src/freak_media_player/assets/icons`. PNG is the existing format, while Qt may
also load other supported raster formats.

## QSS tokens

Custom stylesheets can refer to semantic colors and resolved skin assets:

```css
#appTitleBar {
    border-bottom: 2px solid {{color:accent}};
    background-image: url("{{asset:background.png}}");
}
```

Paths must stay inside the skin directory. Invalid manifests, unknown color
roles, missing mapped files and path traversal are rejected without preventing
the application from starting; Freaky remains the safe fallback.
