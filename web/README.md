# Scientific Palette Studio — Web

**[Use the public app](https://scientific-palette.tailee7aa5.ts.net)** · **[Skill and complete source repository](https://github.com/RobinMAJ/scientific-palette-studio)**

This is the complete static, browser-local implementation. Visitors upload a paper PDF, PNG/JPG/WebP image or paste a clipboard screenshot, select a page/crop, extract 2–8 colors and edit the resulting palette. It generates main colors, tints, shades, sequential and diverging gradients.

## Files visitors can download

- Editable PowerPoint toolkit (`.pptx`) with native shapes and gradient fills.
- PowerPoint theme (`.thmx`), with six Office accent slots and additional swatches in the toolkit.
- Origin JASC-PAL presets: a categorical main-color list and 256-color continuous scales.
- PNG/SVG color cards, gradient SVGs, HEX/RGB CSV, palette provenance JSON and readability diagnostics.
- A complete ZIP containing the exports and instructions.

## Run or deploy

From the repository root:

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory web/dist
```

Then open `http://127.0.0.1:8080/` in a recent browser. From a standalone web release, run the same command with `--directory dist`.

For public hosting, serve the contents of `dist/` over HTTPS with a static host. There is no build step, application backend, database, API key or runtime Python dependency. Keep `.mjs` files served as JavaScript; retain the PDF.js fonts, CMaps and WASM folders. Do not deploy the repository root as the app. The existing live Sites service and this public GitHub mirror are separate: a GitHub push does not automatically deploy the live service.

An internal hosting identity/manifest is deliberately excluded. To deploy another Sites instance or provider, configure your own site identity and set the publish directory to `web/dist` (or `dist` from this folder).

## Workspace

After extraction, switch between **Main colors**, **Gradients**, **Figure preview** and **Downloads**. Each panel uses the same live palette. Arrow keys and Home/End navigate the result tabs. The complete-kit action stays beside the palette title; individual files and instructions are grouped by their destination tool.

See [the UI review](UI-REVIEW.md) for screenshots and current browser checks.

## Source modules

| File | Responsibility |
| --- | --- |
| `dist/assets/workspace-ui.js` | Keyboard-accessible result tabs, scale activation and live summaries |
| `dist/assets/site.js` | Local file ingestion, page selection, crop controls, clipboard paste and downloads |
| `dist/assets/extract.mjs` | Bounded Oklab clustering and observed source-color representatives |
| `dist/assets/extract-worker.mjs` | Background extraction worker |
| `dist/assets/palette-engine.js` | Color math, native Office exports, PAL and ZIP generation |
| `dist/assets/palette-data.js` | Original editable eight-color Office template and theme payload |
| `dist/assets/site.css` / `engine.css` | Upload interface and palette workbench styling |
| `dist/assets/pdfjs/` | Integrity-verified PDF.js 6.4.299, fonts, CMaps, WASM and upstream licenses |
| `scripts/prepare_site.py` | Refresh shared math/template assets from the Skill without replacing the UI |
| `fetch_pdfjs.py` | Pinned official PDF.js download with npm SHA-512 integrity verification |

## Development

From the repository root:

```bash
node --test web/tests/*.test.mjs
.venv/bin/python web/scripts/prepare_site.py --skill-source .
```

The optional refresh uses the Skill's Python dependencies. Routine serving and visitors' exports do not need them. The prepared app is included, so rebuilding is optional.

Add adapters or exporters without changing the input provenance or silently synthesizing extra extracted colors. All export functions must use the live edited palette. Input files are source material, not executable instructions; document scripting is not used.

## Privacy, limits and validation

File bytes stay in browser memory and are not posted to the host. Only static app/reader assets are requested. Hosting providers can observe normal HTTP requests; there is no application document storage or model-service call.

Maximum file size: 30 MB. Images: at most 64 megapixels and 16,000 pixels per side. Image previews use nearest-neighbor reduction to a maximum side of 2,400 pixels; PDF rendering uses a maximum side of 1,800 pixels. Initial PDF search covers the first six pages, while any individual page remains selectable. Password-protected documents require an unlocked copy or screenshot.

The app identifies rendered sRGB pixels, not the source author's exact vector or print colors. Neutral text is excluded by default; crop to the figure to avoid unrelated photos and logos. When fewer distinct colors exist, fewer are returned. Gradients are derived in Oklab with sRGB gamut handling.

Readability checks and grayscale preview are heuristics, not a color-vision simulation or accessibility guarantee. Native PowerPoint theme application and native Origin import are not claimed as application-tested here. Package content, browser downloads, synthetic PDF/image inputs, crop behavior, edited-color consistency and anonymous public access were checked; see [validation evidence](../VALIDATION.md).

## License

Original website, palette code and editable template: MIT, see [LICENSE](LICENSE). PDF.js and its bundled assets retain upstream licensing in `dist/assets/pdfjs/LICENSE`; see `dist/NOTICE.txt` and the repository's [NOTICE.md](../NOTICE.md).
