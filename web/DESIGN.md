# Scientific Palette Studio — UI direction

A researcher's working color desk: turn a reference figure into editable colors, continuous scales and files for existing tools. The reference and extracted colors carry the identity.

## Tokens

- Graphite `#292D3E` for text.
- Slate `#626979` for supporting instructions.
- Paper `#F4F5F8` for the workspace surround.
- Violet `#6250B8` for actions and selected tabs.
- Lilac `#EFEDF8` for interactive context.
- Evergreen `#416D59` for readiness and local-processing reassurance.

Avenir Next, where installed, followed by Segoe UI and a system sans-serif fallback. Restrained heading weight, deliberate spacing, explicit HEX/RGB values and quiet supporting text. No external font request is required.

## Layout and design review

The source controls sit beside the reference canvas. Results occupy one workspace with four tabs: Main colors, Gradients, Figure preview and Downloads. One complete-kit action sits beside the palette title; individual exports are grouped by PowerPoint, Origin, and color cards/values.

The original page placed eight competing actions in a single row and required scrolling through every result section. The revised hierarchy gives main colors visual weight, keeps gradients easy to find, and makes advanced readability checks optional. Violet identifies interface actions while source colors remain unchanged. Gradients represent exportable scales rather than decoration.

The empty-state plot reuses the original site's illustration, explicitly labeled as an example. The three numbered usage steps describe the actual sequence. All content stays in English.

## Interaction

Tabs support click, arrow keys, Home/End, visible focus, selected state and linked panels. New sources start at main colors; editing preserves the current panel. All tabs share the live palette. Continuous scales support keyboard activation; a skip link reaches the workspace. Narrow screens stack reference controls and canvas, use two/three-column swatches, and stack export destinations.

Acceptance checks cover source ingestion, cropping, source-exact fixture colors, edit propagation, tabs, native Office/PAL packages, mobile reflow and public deployment. Full accessibility certification and native Origin/PowerPoint application acceptance are not claimed.
