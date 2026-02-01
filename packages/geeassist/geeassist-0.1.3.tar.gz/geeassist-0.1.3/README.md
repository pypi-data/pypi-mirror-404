# Google Earth Engine Assistant (geeassistant)

**geeassistant** is a Python package designed to simplify the learning curve and daily usage of Google Earth Engine (GEE). It provides high-level wrappers, intuitive utility functions, and streamlined workflows for geospatial analysis.

## Features

- **Simplified Initialization**: One-line authentication and initialization.
- **Easy Indices**: Built-in functions for calculating NDVI, NDWI, EVI, etc.
- **Smart Filtering**: Helpers to filter collections by date, bounds, and metadata more intuitively.
- **Exporting Made Simple**: Wrappers for exporting images and tables to Drive or Cloud Storage.
- **Learning Modules**: access to simplified documentation and code snippets directly from the package.

## Installation

```bash
pip install geeassistant
```

## Usage

```python
import geeassistant as gea
import ee

# Initialize session
gea.init()

# Load a collection and calculate NDVI
l8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA')
ndvi_chem = gea.indices.calculate_ndvi(l8.first(), 'B5', 'B4')

print("NDVI calculated!")
```

## Documentation

Full documentation is available at [https://yourusername.github.io/geeassistant](https://yourusername.github.io/geeassistant).

## License

MIT
