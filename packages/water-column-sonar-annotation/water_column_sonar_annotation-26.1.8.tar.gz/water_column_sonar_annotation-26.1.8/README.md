# Water Column Sonar Annotation

Tool for converting EVR files to annotated regions of interest in parquet format

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/CI-CMG/water-column-sonar-annotation/test_action.yaml)
![PyPI - Implementation](https://img.shields.io/pypi/v/water-column-sonar-annotation) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/CI-CMG/water-column-sonar-annotation) ![GitHub repo size](https://img.shields.io/github/repo-size/CI-CMG/water-column-sonar-annotation)

# Setting up the Python Environment

> Python 3.12.12

# Installing Dependencies

```
source .venv/bin/activate

uv pip install --upgrade pip

uv pip install -r pyproject.toml --all-extras

uv run pre-commit install
```

# Pytest

```
uv run pytest tests -W ignore::DeprecationWarning
```

or
> uv run pytest tests/cruise --cov=water_column_sonar_annotation --cov-report term-missing

```
uv run pre-commit install --allow-missing-config
# or
uv run pre-commit install
```

# Test Coverage

TODO

# Tag a Release

Step 1 --> increment the semantic version in the zarr_manager.py "metadata" & the "pyproject.toml"

```commandline
git tag -a v26.1.0 -m "Releasing v26.1.0"
git push origin --tags
gh release create v26.1.0
```

# To Publish To PROD

```commandline
uv build --no-sources
uv publish
```

# UV Debugging

```
uv lock --check
uv lock
uv sync --extra dev
#uv run pytest tests
```

## Annotation format

- https://roboflow.com/formats/coco-json
- https://www.v7labs.com/blog/coco-dataset-guide
