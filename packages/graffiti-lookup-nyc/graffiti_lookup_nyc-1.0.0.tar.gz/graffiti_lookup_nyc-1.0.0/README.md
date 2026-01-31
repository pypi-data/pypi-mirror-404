# PyPI Packaging

## Publishing to PyPI

1. Ensure you have the latest build tools:
  ```sh
  pip install -r requirements-dev.txt
  ```
2. Build the package:
  ```sh
  python -m build
  ```
3. Upload to PyPI:
  ```sh
  twine upload dist/*
  ```

If you want to use the alternate config, copy `setup-pypi.cfg` to `setup.cfg` before building.

# Graffiti Lookup NYC

This project provides a Python Class and CLI for looking up NYC 311 Graffiti Cleanup Requests.

## Setup
```
pip install -r requirements-dev.txt
```

It's also useful to install [`jq`](https://jqlang.github.io/jq/) to format the `JSON` output

## Usage

### Fetch by single SR ID
```
> python -m graffiti_lookup --id "G2589" | jq .
```
```json
{
  "address": "40-28 MAIN STREET, QUEENS",
  "service_request": "G2589",
  "created": "10/22/2003",
  "status": "Cleaning crew dispatched.  Property cleaned.",
  "last_updated": "10/22/2003"
}
```

### Fetch by multiple IDs:
```
> python -m graffiti_lookup --ids "G258700,G258801,G258900" | jq .
```
```json
[
  {
    "address": "1990 WESTCHESTER AVENUE, BRONX",
    "service_request": "G258700",
    "created": "12/17/2023",
    "status": "Cleaning crew dispatched. No graffiti on property.",
    "last_updated": "1/2/2024"
  },
  {
    "address": "180 ORCHARD STREET, MANHATTAN",
    "service_request": "G258801",
    "created": "12/19/2023",
    "status": "The property owner’s name cannot be determined.",
    "last_updated": "12/20/2023"
  },
  {
    "address": "153 ROEBLING STREET, BROOKLYN",
    "service_request": "G258900",
    "created": "12/21/2023",
    "status": "Cleaning crew dispatched.  Property cleaned.",
    "last_updated": "1/5/2024"
  }
]
```