[![Build Status](https://github.com/ladybug-tools/dragonfly-iesve/workflows/CI/badge.svg)](https://github.com/ladybug-tools/dragonfly-iesve/actions)

[![Python 3.10](https://img.shields.io/badge/python-3.10-orange.svg)](https://www.python.org/downloads/release/python-3100/) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)

# dragonfly-iesve

Dragonfly extension for export to IES-VE GEM file format

## Installation
```console
pip install dragonfly-iesve
```

## QuickStart
```python
import dragonfly_iesve

```

## [API Documentation](http://ladybug-tools.github.io/dragonfly-iesve/docs)

## Local Development
1. Clone this repo locally
```console
git clone git@github.com:ladybug-tools/dragonfly-iesve

# or

git clone https://github.com/ladybug-tools/dragonfly-iesve
```
2. Install dependencies:
```console
cd dragonfly-iesve
pip install -r dev-requirements.txt
pip install -r requirements.txt
```

3. Run Tests:
```console
python -m pytest tests/
```

4. Generate Documentation:
```console
sphinx-apidoc -f -e -d 4 -o ./docs ./dragonfly_iesve
sphinx-build -b html ./docs ./docs/_build/docs
```
