# Use the palette in PowerPoint and Origin

All colors are sRGB. Main colors and derived gradients are stored separately in `palette.json`. A derived gradient is not presented as a palette extracted from the article.

## Offline workbench

Open `palette-workbench.html` in a modern browser. No external scripts, network requests, account or API key are required. Click a swatch to change a main color. Every tint, shade, continuous scale and downloadable preset updates. The original source and saved bundle are not modified.

- Copy HEX/RGB into a custom-color dialog; click a discrete shade to copy its HEX.
- Use grayscale view and inspect the line/marker and heatmap previews.
- Download the complete kit, editable PPTX toolkit, Office theme, or Origin palettes.
- Browser edits retain source hashes and original main colors in exported JSON; edited colors are marked `user-edited`.

Browser kits contain an SVG color card; command-line kits also include PNG, RGB CSV and a SHA-256 manifest. PowerPoint gradients use 17 native stops. SVG/JSON store 257 samples with an exact midpoint; Origin files have 256 samples, with the nearest two entries around that midpoint.

## PowerPoint fills

Open `powerpoint/palette-toolkit.pptx`. Copy a swatch, shade or gradient shape into your presentation. Use **Format Painter** to transfer its fill, or duplicate and resize the shape. Under **Format Shape → Fill → Gradient fill**, its native color stops remain editable. Gradient bars are not screenshots.

## PowerPoint theme

Choose **Design → Themes → Browse for Themes**, then select `powerpoint/palette.thmx`. The location of the gallery control varies with the Office version.

Office has six accent-color slots. Main colors 1–6 map to those slots; fewer colors repeat. Colors 7–8 remain in the editable deck and CSV. A theme changes objects using theme colors; it does not replace every manually assigned RGB fill in an existing deck.

`powerpoint/theme-colors.xml` is a color-scheme-only alternative. Microsoft documents the macOS custom-color directory as `~/Library/Application Support/Microsoft/Office/User Templates/My Themes/Theme Colors/`. Windows commonly uses `%APPDATA%\Microsoft\Templates\Document Themes\Theme Colors\`. This tool does not install application preferences automatically.

Exported themes and slides use a white background. A different background in palette JSON is an audit target, not a complete dark-slide theme.

## Origin import

For Origin 2021 and later:

1. **Tools → Color Manager → Import from Files**.
2. Import `origin/main-colors.pal` for categorical series, or a tonal, sequential or diverging PAL for a continuous colormap.
3. Choose the imported color list in the relevant **Plot Details → Group** color increment controls for grouped lines/scatter/bars.
4. Choose a continuous palette in **Colormap/Contours** for heatmaps/contours/surfaces.
5. Set actual data limits and the meaningful diverging midpoint in Origin. PAL contains RGB entries only; it cannot set units, limits or a numerical center.

Origin also accepts supported PAL files by drag-and-drop. By default, imported palettes of fewer than 20 colors become color lists (`.oth`); 256-entry files remain palettes. We generate genuine JASC ASCII PAL, not renamed CSV or undocumented `.oth` internals.

Older versions support Microsoft binary PAL or JASC ASCII PAL through the Palette button, Color Chooser, or **Graph → Apply Palette to ColorMap**. Persistent installation can use the user's `Palettes` folder; consult your version's documentation.

## Readability and source limits

- Extraction uses rendered pixels, not an author's original palette definition. Compression, anti-aliasing, profiles and rendering can change values.
- Choose figure pages/crops. Text, logos, photographs and heatmaps can dominate small categorical series.
- Sequential gradients aim for ordered Oklab lightness. Check the monotonicity report and the scale at its final display size.
- A diverging color center still needs a numerical center chosen in the plotting software.
- Contrast and separation thresholds are heuristics, not an accessibility certificate. Grayscale is not a color-vision-deficiency simulation. Use markers, dash styles, labels or patterns.
- Neutral sources may need `--include-neutrals` or manual seeds. Do not call invented extra hues extracted colors.

## Official references

- [Origin: supported external palettes](https://docs.originlab.com/quick-help/use-external-color-palette/)
- [Origin: Color Manager and import behavior](https://docs.originlab.com/origin-help/color-manager/)
- [Microsoft: create and apply a theme](https://support.microsoft.com/en-au/powerpoint/create-your-own-theme-in-powerpoint)
- [Microsoft: custom theme-color files](https://support.microsoft.com/en-us/powerpoint/create-or-delete-a-custom-theme-color)
- [Oklab: original equations](https://bottosson.github.io/posts/oklab/)
- [W3C: text contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
