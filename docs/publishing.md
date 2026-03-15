# Publishing LENS Python SDK

## Package Name

The SDK currently targets the package name `lens-python`.

Before publishing, verify the final PyPI name you want to own and keep consistent across:

- `sdk/pyproject.toml`
- `sdk/README.md`
- GitHub releases
- install examples in `README.md`

## GitHub Setup

In the GitHub repository settings:

1. Enable GitHub Actions.
2. Enable trusted publishing for PyPI, or configure a PyPI API token if you prefer manual secrets.
3. If using trusted publishing, configure PyPI to trust this repository and the `publish-pypi.yml` workflow.

## Continuous Integration

The `ci.yml` workflow runs on push and pull request. It:

- runs server and SDK tests
- builds the dashboard
- builds the Python package

## Publishing a Release

1. Bump the SDK version in `sdk/pyproject.toml`.
2. Commit and push to `main`.
3. Create and push a tag in this format:

```bash
git tag sdk-v0.1.0
git push origin sdk-v0.1.0
```

That tag triggers:

- `publish-pypi.yml` to publish the package to PyPI
- `release.yml` to attach the built wheel and sdist to a GitHub release

## Local Release Check

Before tagging, run:

```bash
pytest server/tests sdk/tests
cd dashboard && npm run build
cd ..
python -m build ./sdk
python -m twine check sdk/dist/*
```

## Recommended Next Improvements

- add TestPyPI publish support first
- add changelog generation
- add provider-specific example projects for OpenAI, Anthropic, and Gemini
