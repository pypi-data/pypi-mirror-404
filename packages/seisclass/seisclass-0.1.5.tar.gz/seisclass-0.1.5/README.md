# seisclass

Seismic event classification package for identifying natural and non-natural earthquakes.

## Overview

`seisclass` is a Python package designed to classify seismic events using machine learning models. It provides one main function:
- `check_seed`: Analyzes a seismic data file (SEED format) with corresponding phase file, returning a comma-separated result string: event_type,earthquake_prob,explode_prob,collapse_prob

For detailed information about the program and to cite it in your research publications, please refer to the following papers:

[1] Jia, L., Chen, H., & Xing, K. (2022). Rapid classification of local seismic events using machine learning. Journal of Seismology, 26(5), 897-912.

[2] Jia, L., Chen, S., Li, Y., & Zheng, P. (2025). A Semisupervised Seismic Events Classifier Based on Generative Adversarial Network. Seismological Research Letters, 96(3), 2039-2051.

Git-Repository: [https://github.com/epnet2018/]

## Installation

You can install the package from PyPI:

```bash
pip install seisclass
```

Or install from source:

```bash
pip install .
```

## Dependencies

- numpy
- obspy
- tensorflow
- keras
- joblib
- scikit-learn
- pandas

## Usage

### Basic Usage

```python
from seisclass import check_seed

# Analyze a SEED file with corresponding phase file
result = check_seed('path/to/seed/file', 'path/to/phase/file')
print(result)
```

### Advanced Usage

```python
# Specify a different model
result = check_seed('path/to/seed/file', 'path/to/phase/file', model_str='251111nw')
```

## Testing

To run the tests:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- Jia Luozhao - [18429320@qq.com](mailto:18429320@qq.com)

## Project Structure

```
seisclass/
├── seisclass/
│   ├── __init__.py          # Package initialization and API exposure
│   ├── check_wave.py        # Core functionality
│   ├── model/
│   │   └── 251111nw/         # Model files
│   ├── packages/
│   │   └── read_phase.py     # Phase file parser
│   └── resource/
│       ├── test.phase        # Test phase data
│       └── test.seed         # Test seed data
├── tests/
│   ├── __init__.py
│   └── test_checkwave.py     # Tests
├── setup.py                 # Setup configuration
├── pyproject.toml           # Modern PyPI configuration
├── README.md                # This file
├── LICENSE                  # License file
└── requirements.txt         # Dependencies
```