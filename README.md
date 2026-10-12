# Scientific Palette Studio

**Turn a paper figure into a reusable color language for plots, heatmaps and slides.**

Scientific Palette Studio includes a Codex Skill, a deterministic local command-line tool, and a complete browser-based website. Extract main colors from a supplied PDF or image, generate tints, shades and gradients, and reuse the same colors in PowerPoint, Origin and other plotting tools.

**[Open the public website](https://scientific-palette.tailee7aa5.ts.net)** · **[Download a release](https://github.com/RobinMAJ/scientific-palette-studio/releases/latest)** · **[Report an issue](https://github.com/RobinMAJ/scientific-palette-studio/issues)**

![The public web workbench showing an original synthetic reference palette](docs/assets/web-preview.jpg)

## What you get

- **Main colors:** 2–8 representative source colors, editable HEX/RGB values and categorical presets.
- **Gradients:** a tonal light-to-main-to-dark gradient for every main color, a multihue sequential scale, and a neutral-center diverging scale.
- **PowerPoint:** an editable `.pptx` toolkit with native swatches and gradient fills, plus a `.thmx` theme.
- **Origin:** genuine JASC-PAL presets for categorical series and 256-color continuous colormaps.
- **Color cards and values:** PNG/SVG cards, gradient SVGs, CSV, palette JSON and readability diagnostics; a complete downloadable ZIP in the web app.
- **Browser workflow:** upload a PDF/image, drop a file, paste a clipboard screenshot, choose a PDF page, crop a figure, edit colors and preview lines or heatmaps.
- **Local workflow:** scripted extraction, source hashes, explicit page/crop selection, a self-contained offline workbench and output hash manifests.

Main colors and generated gradients keep separate provenance. A source with fewer distinct colors returns fewer rather than inventing extra extracted hues. No model API or API key is required.

## Choose how to use it

| Mode | Best for | Requirements |
| --- | --- | --- |
| [Public website](https://scientific-palette.tailee7aa5.ts.net) | Uploads, pasted screenshots, cropping and immediate downloads | A recent browser; no account or installation |
| Codex Skill | Asking an assistant to inspect a figure and create a complete kit | Codex or a compatible Skill host, Python dependencies, Poppler for PDFs |
| Local CLI | Reproducible batch work, source/output hashes and offline bundles | Python 3.10+, NumPy, Pillow; Poppler for PDFs |
| Self-hosted website | Your own public/private static deployment | Any static HTTP(S) host; the app needs no backend |

## Use the website

1. Open **[Scientific Palette Studio](https://scientific-palette.tailee7aa5.ts.net)**.
2. Upload a PDF, PNG, JPG or WebP, or paste a screenshot with **Ctrl+V / Cmd+V**. You can also start with 2–8 HEX colors or try the clearly labeled original sample.
3. For a PDF, the app initially checks the first six pages and selects the page with the largest retained colored sample. Choose any available page if your figure is elsewhere.
4. Drag over the preview to isolate a figure. Select the requested number of main colors, optionally include neutrals, then click **Extract colors**.
5. Edit a main swatch or HEX value. Switch between **Main colors**, **Gradients**, **Figure preview** and **Downloads**. Tints, shades, previews and all exports share the live edited palette.
6. Download the complete kit, or choose an individual export from the **Downloads** tab, grouped by PowerPoint, Origin and color cards/values.

The result tabs support arrow keys and Home/End. See the [UI review and screenshots](web/UI-REVIEW.md) for the current interface and tested workflow.

The public app is hosted on a NAS through a dedicated Tailscale Funnel HTTPS endpoint. It remains open to anonymous visitors; no Tailscale client or account is required to use it.

**Privacy:** the application processes file bytes in the visitor's browser; it does not post papers, images or screenshots to a server. App assets are fetched from the static host. Hosting providers can receive ordinary page and asset requests. There is no application account, document storage or model service.

Files are limited to 30 MB. Image inputs are limited to 64 megapixels and 16,000 pixels per side. Images are displayed and sampled using nearest-neighbor reduction to a maximum side of 2,400 pixels; PDFs render to a maximum side of 1,800 pixels. Password-protected PDFs need an unlocked copy or screenshot. Prefer a figure crop to a whole page containing unrelated photos, logos or colormaps.

## Install the Codex Skill

Clone the complete repository into your Skill directory:

```bash
git clone https://github.com/RobinMAJ/scientific-palette-studio.git \
  "$HOME/.codex/skills/scientific-palette-studio"

cd "$HOME/.codex/skills/scientific-palette-studio"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
sh scripts/run.sh doctor
```

For ZIP installation, download a release, extract it, and copy the entire `scientific-palette-studio` folder into `~/.codex/skills/`. Do not copy `SKILL.md` alone. Refresh or restart your Skill host if the Skill list has not updated.

PDF input additionally needs Poppler's `pdfinfo` and `pdftoppm`:

```bash
# macOS, with Homebrew installed:
brew install poppler

# Debian / Ubuntu:
sudo apt install poppler-utils
```

If Codex desktop provides bundled dependencies, discover them through its workspace-dependencies tool instead of assuming a personal runtime path. Supported overrides are `PALETTE_PYTHON`, `PALETTE_PDFINFO`, `PALETTE_PDFTOPPM` and `PALETTE_FONT`; see [runtime guidance](references/runtime.md).

PowerPoint and Origin are not required to generate their export files. Node.js is needed only for web tests and optional maintainer helpers.

### Ask Codex

> Use $scientific-palette-studio to extract the colors from Figure 3 in this PDF. Create six main colors, a tonal gradient for every color, sequential and diverging scales, a color card, a PowerPoint toolkit/theme, and Origin presets. Keep source and derived-color provenance separate.

> Use $scientific-palette-studio to match this supplied screenshot's colors, flag similar series, and export an offline workbench and reusable presets.

The Skill entrypoint is [SKILL.md](SKILL.md). It asks the assistant to inspect the relevant figure, preserve the source, and distinguish format validation from actual native-application testing.

## Use the local CLI

Run these commands from the repository/Skill folder. Output directories must be new; existing bundles are not overwritten.

```bash
# Check dependencies:
sh scripts/run.sh doctor

# Extract a figure from PDF page 3 using a normalized crop:
sh scripts/run.sh extract \
  --input /path/to/paper.pdf --pages 3 \
  --crop '0.08,0.20,0.92,0.84' --count 6 \
  --title 'Figure 3 palette' --output /path/to/new-kit

# Extract from an image:
sh scripts/run.sh extract \
  --input /path/to/figure.png --output /path/to/new-image-kit

# Start with supplied HEX values:
sh scripts/run.sh from-colors \
  --colors '#28669B' '#DB7853' '#439B91' \
  --output /path/to/new-manual-kit

# Generate the original demonstration:
sh scripts/run.sh demo --output /path/to/new-demo

# Re-export an edited palette JSON:
sh scripts/run.sh export \
  --palette /path/to/edited-palette.json --output /path/to/new-edited-kit
```

PDF pages are one-based. Without an explicit page selection, the CLI samples the first six pages; explicit selections accept up to 12 pages. Unlike the website's initial page selection, the CLI combines samples from the selected pages. Crop coordinates are normalized `left,top,right,bottom` within 0..1 and apply to each selected page/image. Use separate bundles when different pages need different crops. Add `--include-neutrals` for intentionally neutral palettes.

Open `palette-workbench.html` from the generated bundle to edit/copy colors and download updated native presets. Some managed browsers restrict local `file:` pages; a standard local browser or the public website can be used. No browser security settings need to be weakened.

## Use the files in PowerPoint and Origin

### PowerPoint

- Open `powerpoint/palette-toolkit.pptx`; copy a swatch or gradient shape into your deck. The fills and text are native editable objects.
- Use Format Painter to transfer the fill to another shape.
- Apply `powerpoint/palette.thmx` with **Design → Themes → Browse for Themes**.
- Office provides six accent slots. Main colors above six remain in the toolkit; fewer than six repeat across the accent slots.
- A theme updates theme-linked colors, not every object with a fixed RGB fill. The provided toolkit uses a white background.

### Origin

- Use **Tools → Color Manager → Import from Files** to import `.pal` files.
- `main-colors.pal` is the categorical series list. Tonal, sequential and diverging `.pal` files contain 256 continuous colors.
- Set data limits, colormap levels and a meaningful diverging midpoint in Origin. PAL contains RGB values only and does not encode numerical units or data ranges.
- Origin may save an imported short categorical list as its own `.oth` preset. This project supplies documented JASC-PAL rather than inventing proprietary OTH internals.

See [export instructions and official references](references/using-exports.md). Native Origin application import has not been tested in this workspace; format/content checks are reported separately.

## Self-host or develop the website

The complete app is in `web/dist/`, including the pinned PDF.js reader, fonts, CMaps and WASM assets. It works independently of Codex, Python and the local Skill after deployment.

Preview it locally:

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory web/dist
```

Open `http://127.0.0.1:8080/`. The app uses ES modules and workers, so serve it over HTTP(S), not by double-clicking its HTML. Clipboard-image paste requires a supported browser and a normal user paste action; HTTPS is recommended for public hosting.

Deploy the contents of `web/dist/` to a static host, or configure that folder as the publish directory. There is no build step, server application, secret or database. **Do not publish the repository root as the website**, because its root is the Skill/documentation package rather than the app.

The public Sites deployment is an independent live service. Pushing this GitHub repository does not automatically update that service. The published web source matches the verified app export; internal Site identifiers and write credentials are excluded. See [web/README.md](web/README.md) for the source modules, deployment details and limits.

## Repository layout

```text
scientific-palette-studio/
├── SKILL.md                    Codex Skill entrypoint
├── agents/openai.yaml          Skill UI metadata
├── scripts/                    Python CLI and optional maintainer helpers
├── assets/                     Original editable Office template and offline workbench
├── references/                 Runtime and export instructions
├── examples/demo/              Original example kit; no article bundled
├── tests/                      Python checks
├── docs/assets/                Original color card and website preview
└── web/
    ├── dist/                   Ready-to-serve static website and PDF.js assets
    ├── scripts/                Optional template/palette payload refresh
    └── tests/                  Browser-engine and extraction checks with Node
```

`agents/openai.yaml` is Skill metadata, not a separately running autonomous Agent.

## Tests and extension

```bash
# Use the Python environment in which requirements.txt was installed:
.venv/bin/python -m unittest discover -s tests -v

# Web core checks; Node.js 20+ recommended:
node --test web/tests/*.test.mjs

# Optional offline JavaScript helper checks:
node scripts/check_workbench.mjs
```

To refresh the shared browser palette/export payload after editing the Skill's math or original template:

```bash
.venv/bin/python web/scripts/prepare_site.py --skill-source .
```

This refreshes generated palette-engine/data assets and the base stylesheet; it preserves the upload interface and PDF handling. Inspect the result and rerun affected checks before deploying.

Extend the tool by adding exporters that consume the same main colors and gradient samples. Keep source/extracted/manual/edited/derived provenance, preserve schema `1.0` compatibility or provide an explicit migration, and test actual exported format content. New input adapters belong in `web/dist/assets/site.js` or the Python source loader; browser clustering is in `web/dist/assets/extract.mjs`.

The original native template can optionally be rebuilt with `scripts/build_template.mjs`, which needs a suitable Codex desktop Artifact Tool runtime. Ordinary users do not need it; the reusable template is already included.

Calibrated print color, validated color-vision-deficiency simulation, Office add-ins, Origin automation and semantic role inference are possible future extensions, not current features.

## Precision and validation

Rasterization, screenshots, compression, color profiles and antialiasing can change pixel values. Extraction identifies representative rendered sRGB colors rather than exact author-specified vector/print fills. The browser and Python pipelines have different sampling and representative-selection paths, so their ordering and results need not be bit-identical. Crop and inspect the source comparison.

Derived gradients use Oklab interpolation with chroma reduction to keep colors in sRGB. A main color remains the exact tonal midpoint. JSON/SVG scales use 257 samples; PAL uses 256; native PowerPoint gradients approximate the same ramp with 17 stops. Lightness monotonicity uses an explicit quantization tolerance.

Contrast, pair separation and grayscale views are heuristics, not an accessibility certification or color-vision-deficiency simulation. Use markers, dash styles and labels as well as color. No plot-data extraction, official journal-palette claim or CMYK calibration is implied.

[VALIDATION.md](VALIDATION.md) records the Python and web checks, synthetic PDF/image evidence, native export-content checks, independent rendering and remaining application-testing limits.

## License and attribution

Original workflow code, website, editable template content and original demonstration graphics: **MIT**. See [LICENSE](LICENSE).

Oklab follows Björn Ottosson's published equations. PDF.js 6.4.299 and bundled third-party assets retain their upstream notices and licenses. NumPy, Pillow and Poppler are separate dependencies. See [NOTICE.md](NOTICE.md) and [the PDF.js license](web/dist/assets/pdfjs/LICENSE).

No paper PDF, journal figure, personal API key, local virtual environment or deployment credential is bundled. Users remain responsible for rights in their source papers/images. Interoperability does not imply endorsement by Microsoft, OriginLab, Mozilla or journal publishers.
