# Validation status — public release v1.0.0

This release combines the local Skill/CLI with the browser-local web implementation. Validation covers technical behavior and export contents; it does not certify scientific figure readability or native application compatibility on every platform.

## Local Skill and CLI

- 20 Python checks cover source-color extraction, synthetic PDF input, neutral opt-in, sparse lines, page/crop limits, alpha handling, exact tonal midpoint anchors, sRGB gamut, sequential/diverging lightness, input validation, source/output hashes and refusal to overwrite outputs.
- A project-owned synthetic PDF's colored page recovered all six expected HEX values. No private source or real paper is bundled.
- The Skill Creator frontmatter validator passes. Shell/Python/JavaScript checks and portable package paths are checked separately.
- The original editable Office template passed package/layout/font/import checks. The generated demo imported through Artifact Tool and its four slides were independently rendered and inspected.
- Offline JavaScript helpers agree with Python's demonstration ramps. ZIP CRCs, OOXML relationships/XML and PAL records are checked.

## Website

- 11 Node checks cover deterministic source-color representatives, neutral filtering, thin-line preservation, lower-frequency antialias pixels, sample bounds, fewer colors without invented hues, native template slots, tonal anchors, edited anchors, gradient lightness, PAL and ZIP helpers.
- Browser image upload recovered six known exact colors. Clipboard-image paste recovered the same six colors.
- A project-owned two-page PDF automatically selected colored page 2; manual page selection worked. A neutral page produced a useful error without a fabricated palette.
- A crop covering two sample swatches returned exactly those two colors and explicitly reported fewer than the six requested.
- Typed HEX edits propagated to gradients and downloaded files. A browser-generated kit contained valid PNG, ZIP, PPTX, THMX, SVG, CSV and PAL contents. Edited `#AA3344` appeared in the native swatch, Office accent and Origin RGB record.
- An eight-color browser kit retained all eight native PPT swatches, six Office accents and two extra colors.
- Mobile layout had no horizontal overflow at a narrow test viewport; crop overlay aligned with the source preview. Temporary viewport changes were reset.
- PDF.js package SHA-512 matched official npm metadata. Worker, font, CMap and WASM URLs resolve against the page origin, rather than the worker directory.
- The public website and its reader assets returned HTTP 200 to anonymous requests. Public-page extraction and Origin-preset download were exercised. The updated public PDF page recovered all six colors without console errors/warnings.

## Limits

- Native Origin import was not performed. JASC-PAL support and import instructions follow OriginLab's official documentation; header/count/RGB contents were checked.
- Native PowerPoint opening/theme application is not claimed. OOXML validation, browser-generated downloads and independent Artifact Tool rendering are different evidence from actual Office acceptance.
- The offline file is structurally/helper-tested. Full interactive browser acceptance was performed on the HTTP(S) web app, which shares palette/export logic; it is not a claim that every managed browser permits local `file:` pages.
- No color-vision-deficiency simulation, accessibility certification, CMYK calibration, numerical data-limit inference or automatic recoloring of an existing project is included.

The final GitHub publication also checks anonymous metadata, README access and download contents against the reviewed source. Release archives exclude credentials, hosting identity, virtual environments, caches and source papers.
