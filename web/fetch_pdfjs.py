"""Vendor the pinned, patched official PDF.js distribution with integrity verification."""
import base64, hashlib, io, json, tarfile, urllib.request
from pathlib import Path

VERSION = "6.4.299"
dest = Path(__file__).parent / "dist/assets/pdfjs"
metadata = json.load(urllib.request.urlopen(f"https://registry.npmjs.org/pdfjs-dist/{VERSION}", timeout=30))
data = urllib.request.urlopen(metadata["dist"]["tarball"], timeout=60).read()
assert metadata["dist"]["integrity"] == "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()
dest.mkdir(parents=True, exist_ok=True)
total = 0
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as package:
    for member in package.getmembers():
        relative = member.name.removeprefix("package/")
        if not member.isfile() or ".." in Path(relative).parts:
            continue
        if relative not in {"build/pdf.mjs", "build/pdf.worker.mjs", "LICENSE"} and not relative.startswith(("cmaps/", "standard_fonts/", "wasm/")):
            continue
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.extractfile(member).read())
        total += member.size
(dest / "VERSION.json").write_text(json.dumps({"version": VERSION, "integrity": metadata["dist"]["integrity"], "source": metadata["dist"]["tarball"]}, indent=2))
print(json.dumps({"version": VERSION, "verified": True, "bytes": total}))
