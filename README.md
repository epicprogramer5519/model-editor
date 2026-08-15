# MELCOR Model Editor

A desktop GUI for building and editing MELCOR 1.8.6 `.inp` models, built
on top of [MELKIT](https://github.com/manjavacas/melkit) for all file
parsing/writing.

This is the first component of a four-part suite (Model Editor,
Calculation Server, Job Status, Configuration Tool, AptPlot-style
plotting tool) — the rest can reuse `app/melkit_bridge.py` and follow
the same PySide6 pattern.

## What it does

- Opens a MELCOR `.inp` file and renders Control Volumes (CVs) and Flow
  Paths (FLs) as an interactive node diagram (auto-laid-out with
  `networkx`, since MELCOR files don't store visual coordinates).
- Lets you click any CV or FL to see and edit every field MELKIT
  exposes, in a property panel on the right.
- Lets you create new CVs and FLs through dialogs, and delete existing
  ones.
- A tree browser on the left lists every CV / FL / CF in the model,
  including CFs (not yet drawn on the diagram — CF wiring is a good
  next step).
- All edits go through MELKIT's `Toolkit.write_object` /
  `update_object` / `remove_object`, so the on-disk `.inp` file stays
  in MELCOR's native format at all times — there's no separate/lossy
  internal representation.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py                          # opens with no file loaded
python main.py sample_files/sample_model.inp   # opens a file directly
```

A tiny synthetic test model (`sample_files/sample_model.inp`, 4 CVs / 3
FLs — not derived from any real facility model) is included so you can
try the editor immediately.

## Project layout

```
model_editor/
  main.py                  # entry point
  app/
    melkit_bridge.py       # wraps melkit.Toolkit: layout, CRUD, templates
    items.py                # CVNodeItem / FLEdgeItem (QGraphicsItem)
    scene.py                 # builds the diagram from a ModelBridge
    object_list.py           # left dock: CV/FL/CF tree browser
    property_panel.py        # right dock: field editor
    dialogs.py                # "New CV" / "New FL" dialogs
    main_window.py            # QMainWindow wiring it all together
  sample_files/
    sample_model.inp          # small synthetic test model
```

## Building a Windows .exe

Once you've tested the app on your target platform:

```bash
pip install pyinstaller
pyinstaller --name ModelEditor --windowed --onefile main.py
```

The `.exe` will land in `dist/ModelEditor.exe`. `--windowed` suppresses
the console window; drop it while testing if you want to see tracebacks.
Note MELKIT is GPL-3.0 licensed — see the license notes on its
[GitHub repo](https://github.com/manjavacas/melkit) before distributing
a packaged build.

## Known limitations / good next steps

- CFs (Control Functions) are listed but not drawn on the diagram or
  wired to the CVs/FLs that reference them — `toolkit.get_connected_cfs`
  already gives you that data if you want to add CF nodes.
- The auto-layout is a generic spring layout; a real editor would let
  you drag nodes and *persist* their positions (e.g. in a sidecar JSON
  file, since MELCOR's own format has nowhere to store x/y).
- No validation on field values yet (e.g. checking `PVOL` is a valid
  float) — the property panel currently accepts any string.
- No multi-file / undo support yet.
