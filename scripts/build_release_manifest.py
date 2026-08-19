"""Build a release manifest with provenance and integrity evidence.

ATLAS-059 requires "signed release artifacts, SBOM, provenance, and
validation evidence." No signing key or HSM is provisioned yet (open
question, `docs/059_Release_Process.md`) — this manifest establishes the
*content* a signature would cover: exact git commit, SBOM checksum, and a
checksum of the manifest itself. `signature` is explicitly null with a
`signed: false` flag rather than a fabricated value, so nothing downstream
can mistake a checksum for a cryptographic attestation.

Usage: python scripts/build_release_manifest.py <version> [output_path]
Requires sbom.json to already exist (run generate_sbom.py first).
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _git_is_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip() == ""


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_release_manifest.py <version> [output_path]")
        return 1
    version = sys.argv[1]

    sbom_path = REPO_ROOT / "sbom.json"
    if not sbom_path.exists():
        print("sbom.json not found — run scripts/generate_sbom.py first.")
        return 1

    manifest = {
        "version": version,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "git_working_tree_clean": _git_is_clean(),
        "sbom_sha256": _sha256_file(sbom_path),
        "signed": False,
        "signature": None,
        "signature_note": (
            "No signing key is provisioned yet (docs/059_Release_Process.md open question). "
            "This manifest's own sha256 (computed after writing, see *.sha256 sidecar) is an "
            "integrity checksum, not a cryptographic attestation of authorship."
        ),
    }

    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / f"release-manifest-{version}.json"
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    checksum = _sha256_file(output_path)
    output_path.with_suffix(output_path.suffix + ".sha256").write_text(
        f"{checksum}  {output_path.name}\n", encoding="utf-8"
    )

    print(f"Wrote {output_path}")
    print(f"Wrote {output_path}.sha256 ({checksum})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
