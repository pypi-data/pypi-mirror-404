# ActivePaths
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![NumPy](https://img.shields.io/badge/NumPy-4DABCF?logo=numpy&logoColor=fff)](#)
[![Pytest](https://img.shields.io/badge/Pytest-fff?logo=pytest&logoColor=000)](#)
[![PyPI](https://img.shields.io/badge/PyPI-3775A9?logo=pypi&logoColor=fff)](#)
![License](https://img.shields.io/github/license/kuslavicek/activepaths)
![Version](https://img.shields.io/github/v/release/kuslavicek/activepaths)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/kuslavicek/activepaths)


A library for rare dynamical event sampling in non-equilibrium systems, based on Transition Path Sampling (RTP-TPS) and Variational Path Sampling (VPS).

## Features

- **Rare Dynamical Event Sampling**: Efficiently sample rare events in active matter systems.
- **RTP-TPS**: Transition Path Sampling for Run-and-Tumble Particles.
- **VPS**: Variational Path Sampling for computing large deviation functions.
- **Analysis Tools**: Tools for estimating transition rates and large deviation rate functions.

## Installation

```bash
pip install activepaths
```

## Usage

### RTP-TPS Example (Conceptual)

```python
from activepaths.core import StateTuple
from activepaths.sampling.tps import is_reactive_indicator

# ... (Initialize trajectory and define reactant/product states) ...
# is_reactive = is_reactive_indicator(trajectory, is_reactant, is_product)
```

### VPS Example (Conceptual)

```python
from activepaths.sampling.vps import calculate_stochastic_action

# ... (Define system parameters and trajectory) ...
# action = calculate_stochastic_action(trajectory, mobility, force, dt, T)
```

## Development

To set up the development environment:

```bash
git clone https://github.com/USER/activepaths.git
cd activepaths
pip install -e .
pip install -r requirements.txt
pytest
```


## References

This project incorporates research from the following papers:

- **Transition-path sampling for Run-and-Tumble particles**
  Thomas Kiechl, Thomas Franosch, Michele Caraglio
  *arXiv:2411.12368*

- **Variational path sampling of rare dynamical events**
  Aditya N. Singh, Avishek Das, David T. Limmer
  *arXiv:2502.01852* 
