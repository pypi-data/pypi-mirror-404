# truncated-gamma

[![](https://github.com/wkingc/truncated-gamma-rvs-py-package/actions/workflows/python-package.yml/badge.svg)](https://github.com/wkingc/truncated-gamma-rvs-py-package/actions/workflows/python-package.yml)

[![](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A Python package for generating random variates from a truncated gamma distribtion.

## Installation

```bash
pip install truncated-gamma-rvs
```

## Quick Start

```python
from truncated_gamma_rvs import truncgamma_rvs

# Generate 100,000 random variates from a gamma distribution truncated 
# to the interval [0, 1000], where the mean is 100 and the standard 
# deviation is 1/2 the value of the mean (e.g., the coefficient of variation).
x = truncgamma_rvs(
    mean_target = 100, 
    cv_target = 1/2, 
    A = 0, 
    B = 1000, 
    size = 100000, 
    random_state = 123)
```

## What is a Truncated Gamma Distribution?

A truncated gamma distribution is a gamma distribution that has been "cut off" at specified lower (A) and upper (B) bounds. This is useful when you need gamma-distributed random variables that must fall within a specific range.

## API Reference

### `truncgamma_rvs(mean_target, cv_target, A, B, size=1, random_state=None)`

Generate random variates from a truncated gamma distribution.

**Parameters:**

- `mean_target` (float): Target mean of the truncated distribution
- `cv_target` (float): Target coefficient of variation  
- `A` (float): Lower bound (≥ 0)
- `B` (float): Upper bound (> A)
- `size` (int, optional): Number of samples to generate (default: 1)
- `random_state` (int, optional): Random seed for reproducibility

**Returns:**

- `numpy.ndarray`: Array of random samples

### `TruncatedGamma(alpha, theta, A, B)`

Class for working with truncated gamma distributions.

**Parameters:**

- `alpha` (float): Shape parameter (> 0)  
- `theta` (float): Scale parameter (> 0)
- `A` (float): Lower bound (≥ 0)
- `B` (float): Upper bound (> A)

**Methods:**

- `truncgamma_m1()`: Calculate the first moment (mean)
- `truncgamma_m2()`: Calculate the second moment  
- `truncgamma_var()`: Calculate the variance
- `truncgamma_cv()`: Calculate the coefficient of variation

## Requirements

- Python ≥ 3.9
- numpy
- scipy

## Development

```bash
git clone https://github.com/wkingc/truncated-gamma-rvs-py-package.git
cd truncated-gamma-rvs-py-package
pip install -e ".[dev]"
python -m pytest
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Documentation

For a complete usage guide, see <https://www.kingcopeland.com/truncated-gamma-rvs-py/>.

## Citation

If you use this package in your research, please consider citing it:

```bibtex
@software{copeland2026tgammarvs,
  author = {Wade K. Copeland},
  title = {{truncated-gamma-rvs: A Python package for truncated gamma distributions}},
  url = {https://pypi.org/project/truncated-gamma-rvs/},
  version = {0.1.1},
  year = {2026}
}
```