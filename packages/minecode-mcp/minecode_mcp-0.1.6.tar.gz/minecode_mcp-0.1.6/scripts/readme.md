
---

**Release**
- **Script**: `scripts/release.ps1` — full release workflow (clean, bump, build, push, publish).
- **Token**: `pip_token.txt` or environment variable `PYPI_API_TOKEN` (the script sets `TWINE_USERNAME=__token__` and `TWINE_PASSWORD` from the token).
- **Behavior**: removes `dist/`, `build/` and any `*.egg-info`, bumps the patch number in `pyproject.toml` (when `-Bump`), commits, tags `vX.Y.Z`, pushes, builds sdist/wheel, and uploads the release.
- **Python**: prefers `venv\Scripts\python.exe` if present, otherwise uses `python` on PATH.
- **Examples**:

```powershell
# Bump, build, push tag, and publish
.\scripts\release.ps1 -Bump -Publish

# Build and publish without bump
.\scripts\release.ps1 -Publish

# Just build (no bump, no publish)
.\scripts\release.ps1
```

- **Notes**: the older `scripts/bump_version.*` utilities were consolidated into `release.ps1`; keep your PyPI API token in `pip_token.txt` or set `PYPI_API_TOKEN` for CI.
