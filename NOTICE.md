# Notices

Original workflow code, HTML, template content and demonstration colors belong to this project. No Microsoft-supplied Office theme or Origin proprietary preset is redistributed.

Oklab matrices and equations follow [Björn Ottosson's original description](https://bottosson.github.io/posts/oklab/), which makes its conversion implementation available in the public domain and under MIT. This project acknowledges its author and implements the published equations in Python and JavaScript.

NumPy, Pillow and Poppler are separate, unbundled dependencies with their own licenses. Artifact Tool only authored the project's original reusable PPTX template; none of its runtime/library code is included.

JASC PAL, Office OOXML and SVG are file formats. Interoperability does not imply endorsement by OriginLab, Microsoft or format owners. User source articles/images are not included; this package does not grant rights to redistribute them.

## Bundled web reader

The website vendors the official `pdfjs-dist` 6.4.299 distribution. PDF.js is maintained by Mozilla and contributors and uses Apache License 2.0; bundled third-party font, CMap and WASM licenses/notices remain in `web/dist/assets/pdfjs/`. See its [LICENSE](web/dist/assets/pdfjs/LICENSE) and `VERSION.json` for the pinned npm tarball URL and integrity value. Its code is not covered by this project's MIT license.

The public website and Skill are distributed together. Hosting provider infrastructure, source-repository credentials, internal Site identity and personal runtime environments are not included. The synthetic example figure, color card and web screenshot were generated for this project; no article or journal figure is redistributed.
