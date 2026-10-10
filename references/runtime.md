# Runtime

Normal use requires Python 3.10+, NumPy and Pillow. PDF input additionally requires Poppler's `pdfinfo` and `pdftoppm`. Everything runs locally without a model API.

```bash
python3 -m venv /path/to/scientific-palette-studio/.venv
/path/to/scientific-palette-studio/.venv/bin/python -m pip install -r /path/to/scientific-palette-studio/requirements.txt
```

Install Poppler with the appropriate package manager, for example `brew install poppler` on macOS or `sudo apt install poppler-utils` on Debian/Ubuntu. Follow user permissions; do not install globally just for a demo. The shell wrapper prefers `PALETTE_PYTHON`, then the skill's `.venv`, then PATH's `python3`.

For Codex desktop, call the read-only workspace-dependencies tool and set `PALETTE_PYTHON` to its returned Python path. Use its override/fallback executable directories for Poppler. Do not bake personal runtime paths into the package or copy a user's environment.

Optional overrides: `PALETTE_PYTHON`, `PALETTE_PDFINFO`, `PALETTE_PDFTOPPM`, and `PALETTE_FONT` for the PNG card's font.

PowerPoint, Origin, Node.js and Artifact Tool are not needed to generate presets. PowerPoint/Origin are needed for actual application import checks. A modern browser opens the offline workbench.

## Template maintenance

`scripts/build_template.mjs` authors the original native template using `@oai/artifact-tool` and the installed presentations skill's finalizer. This optional maintainer route needs a Codex desktop runtime. Read that skill's authoring and marker instructions first. Run in a private build directory with the runtime Node modules, then extract the template's original theme XML into `assets/base-theme.xml`. Normal users do not need to rebuild the template. No Microsoft-supplied theme is redistributed.
