"""Generate a minimal software bill of materials (ATLAS-059 Release Process).

Not a full CycloneDX/SPDX implementation — that tooling choice is an open
question (`docs/059_Release_Process.md`). This produces a flat,
machine-readable component list (name, version, ecosystem) from the
backend's installed distributions and the frontend's locked npm packages,
which is enough to answer "what exact versions shipped in this release."

Usage: python scripts/generate_sbom.py [output_path]
"""
import json
import sys
from importlib import metadata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def backend_components() -> list[dict[str, str]]:
    return sorted(
        (
            {"name": dist.metadata["Name"], "version": dist.version, "ecosystem": "pypi"}
            for dist in metadata.distributions()
            if dist.metadata["Name"]
        ),
        key=lambda c: c["name"].lower(),
    )


def frontend_components() -> list[dict[str, str]]:
    lockfile = REPO_ROOT / "frontend" / "package-lock.json"
    if not lockfile.exists():
        return []
    data = json.loads(lockfile.read_text(encoding="utf-8"))
    packages = data.get("packages", {})
    components = []
    for path, info in packages.items():
        if not path or not isinstance(info, dict):
            continue
        name = info.get("name") or path.rsplit("node_modules/", 1)[-1]
        version = info.get("version")
        if not version:
            continue
        components.append({"name": name, "version": version, "ecosystem": "npm"})
    return sorted(components, key=lambda c: c["name"].lower())


def main() -> int:
    sbom = {
        "sbom_format": "atlas-flat-v1",
        "components": {
            "backend": backend_components(),
            "frontend": frontend_components(),
        },
    }
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "sbom.json"
    output_path.write_text(json.dumps(sbom, indent=2), encoding="utf-8")
    total = len(sbom["components"]["backend"]) + len(sbom["components"]["frontend"])
    print(f"Wrote {output_path} ({total} components).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
