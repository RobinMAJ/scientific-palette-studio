---
name: scientific-palette-studio
description: "Extract scientific figure colors from supplied paper PDFs or images and create main palettes, tints, shades, sequential/diverging gradients, color cards, an offline palette workbench, editable PowerPoint fills/themes, and importable Origin PAL presets. Use for paper-inspired scientific figure coloring and cross-software palette reuse; not for inferring plot data, redrawing source figures or certifying accessibility."
---

# Scientific Palette Studio

Turn supplied figure colors into a reusable palette for scientific figures and slides. Include gradients with main colors unless the user explicitly excludes them.

## Browser option

For interactive uploads, clipboard screenshots and downloadable files without installing this Skill, use [the public web workbench](https://scientific-palette-studio.majiabin7.chatgpt.site). Source files are processed in the visitor's browser. The website implementation lives in `web/`; read [web/README.md](web/README.md) only when developing or self-hosting it. Use the deterministic local CLI for scripted extraction, hashes and offline bundles.

## Inspect the source

1. Identify the supplied local PDF/image and requested figure/panel/style. Preserve the source. No account, API key or upload is required.
2. Inspect selected pages/panels visually; choose figure crops. Do not infer colors from extracted article text or treat unrelated photos/heatmaps as categorical colors.
3. Default to six main colors, white figure background, tonal gradients for every main hue, one multihue sequential scale and one neutral-center diverging scale. Ask only when a missing choice changes scientific meaning, such as a required sign convention or numerical diverging midpoint.
4. Without a source, use the user's HEX seeds; otherwise clearly label an original demo. Never imply that a demo came from an article.

## Run the deterministic local tool

`<skill-dir>` is this file's directory. Quote paths. Read [runtime guidance](references/runtime.md) when a dependency is missing or when using bundled Codex tools.

```bash
sh "<skill-dir>/scripts/run.sh" doctor
sh "<skill-dir>/scripts/run.sh" extract --input "/path/to/paper.pdf" --pages "2,4-5" --crop "0.08,0.2,0.92,0.86" --count 6 --title "Paper figure palette" --output "/path/to/new-bundle"
sh "<skill-dir>/scripts/run.sh" extract --input "/path/to/figure.png" --count 6 --output "/path/to/new-bundle"
sh "<skill-dir>/scripts/run.sh" from-colors --colors '#28669B' '#DB7853' '#439B91' --output "/path/to/new-bundle"
sh "<skill-dir>/scripts/run.sh" export --palette "/path/to/edited-palette.json" --output "/path/to/new-bundle"
```

- Pages are one-based. The default samples the first six pages; explicitly select up to 12. Inspect the article to choose figure pages.
- Crop is normalized `left,top,right,bottom` within 0..1, applied to every selected page/image. Use separate bundles for different crops.
- Main palette size is 2–8. Fewer distinct source hues can yield fewer colors. Never invent additional extracted colors to meet a requested count.
- Neutral paper/text colors are excluded. Use `--include-neutrals` for intended grayscale palettes. A one-color source needs another seed or crop.
- Use a new output directory; existing bundles are not overwritten. Record source hashes, page/crop choices and extraction coverage without copying source articles into exports.
- Main values are observed representatives. Gradients are marked derived; browser edits retain original source hashes and mark colors user-edited.

## Deliver the cross-software kit

- `palette-workbench.html`: offline color editing; HEX/RGB copying; line, marker and heatmap previews; grayscale view; updated ZIP/PPTX/THMX/PAL/SVG downloads.
- `color-card.png`, `colors.csv`, `palette.json`: color card, values and provenance.
- `powerpoint/palette-toolkit.pptx`: native editable swatches, discrete shades and gradient fills.
- `powerpoint/palette.thmx`, `theme-colors.xml`: Office theme and six-accent color scheme.
- `origin/main-colors.pal`: categorical list; `tonal-*.pal`, `sequential-multihue.pal`, `diverging.pal`: 256-entry continuous palettes.
- `gradients/*.svg`: 257-sample strips; `audit.json`, `manifest.json`: diagnostics and output hashes.

Read [using the exports](references/using-exports.md) for exact application steps. Office has six accent slots; colors above six remain in the toolkit. JASC PAL is documented by Origin. Do not invent `.oth` internals or promise that a palette file sets data units, limits or the diverging numerical center.

## Acceptance

1. Compare main colors with the selected source figure. Report rendering/compression approximations, dominance by photos/heatmaps, actual/requested count and extraction coverage.
2. View the PNG color card and HTML tool. Check labels, main colors, tonal midpoint anchors, sequential direction and diverging center. State extracted/manual/demo provenance.
3. Review contrast, pair separation, grayscale ambiguity and gradient lightness. They are heuristics, not accessibility certification. No color-vision-deficiency simulation is present; recommend markers and dash styles for similar colors.
4. Check real native gradient nodes and package relationships in PPTX/THMX; parse PAL header, count and RGB bounds. Render the PPTX or open a new copy in PowerPoint when available. Distinguish package checks from actual native application loading.
5. Test Origin import when an appropriate session exists. Otherwise say that documented format/content were checked but native import was not performed. Do not change existing project colors or preferences to validate a new kit.
6. Deliver concise instructions and links to the workbench, color card, PPTX and Origin presets. Local creation does not authorize GitHub publication or modifying another Agent.

## Extension

Keep schema `1.0` compatible or version it explicitly. New exporters consume the same main colors and gradient samples and add real format round-trip tests. Semantic roles, validated color-vision simulation, CMYK calibration, Office add-ins and Origin automation are future routes; do not advertise them as implemented.

The original reusable template was authored with Artifact Tool. Routine exports update its native OOXML fields; users need only Python, NumPy and Pillow, plus Poppler for PDF input. The optional maintainer template builder is not required for normal use.
