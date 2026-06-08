<p align="center">
  <img src="logo/pydaq-logo.png" alt="PYDAQ" class="center" width="50%" height="50%">
</p>

[![PyPI version](https://img.shields.io/pypi/v/pydaq?color=a26969)](https://pypi.org/project/pydaq/)
[![License](https://img.shields.io/pypi/l/pydaq?color=a26969)](https://opensource.org/licenses/BSD-3-Clause)
[![python](https://img.shields.io/pypi/pyversions/pydaq?color=a26969)](https://pypi.org/project/pydaq/)
[![status](https://img.shields.io/pypi/status/pydaq?color=a26969)](https://pypi.org/project/pydaq/)
[![contributors](https://img.shields.io/github/contributors/samirmartins/pydaq?color=a26969)](https://github.com/samirmartins/pydaq/graphs/contributors)
[![downloads](https://static.pepy.tech/badge/pydaq/month)](https://pepy.tech/projects/pydaq)
[![openissues](https://img.shields.io/github/issues/samirmartins/pydaq?color=a26969)](https://github.com/samirmartins/pydaq/issues)
[![issuesclosed](https://img.shields.io/github/issues-closed-raw/samirmartins/pydaq?color=a26969)](https://github.com/samirmartins/pydaq/issues)
[![forks](https://img.shields.io/github/forks/samirmartins/pydaq?color=a26969&style=social)](https://github.com/samirmartins/pydaq/network/members)
[![stars](https://img.shields.io/github/stars/samirmartins/pydaq?color=a26969&style=social)](https://github.com/samirmartins/pydaq/stargazers)

# PYDAQ - Data Acquisition and Experimental Analysis with Python ([www.pydaq.org](https://www.pydaq.org))

PYDAQ is a Python package for data acquisition, signal generation, system identification, digital filtering, and real-time control using Arduino and NI-DAQ devices.

It provides a unified graphical interface, command-line tools, and Jupyter notebook examples for laboratory experiments, rapid prototyping, teaching, and research workflows.

---

## Capabilities

PYDAQ supports the following experimental workflows:

| Capability | Description |
| :--- | :--- |
| Data acquisition | Acquire, plot, and save experimental data from Arduino or NI-DAQ boards |
| Signal generation | Send user-defined input signals, including nonlinear excitation signals |
| Step-response experiments | Run automatic step-response tests and save the resulting data |
| PRBS-based experiments | Generate excitation signals for system identification workflows |
| System identification | Estimate linear and nonlinear black-box models from experimental data using [SysIdentPy](https://www.sysidentpy.org) |
| Digital filtering | Apply FIR and IIR filters directly to acquired data in real time |
| PID control | Run real-time or simulated P, PI, PD, and PID control with Ziegler-Nichols tuning |
| LQR control | Simulate or implement Linear Quadratic Regulator control for state-space systems |
| Multi-channel workflows | Work with multiple Arduino or NI-DAQ channels |
| Benchmarking | Estimate the maximum reliable sampling frequency supported by the local system |

Further details about benchmarking are available in the [benchmarking documentation](https://pydaq.org/benchmarking/).

---

## Installation

Install PYDAQ with `pip`:

```console
pip install pydaq
```

Main dependencies include `numpy`, `scipy`, `matplotlib`, `pyserial`, `nidaqmx`, `PySide6`, `sysidentpy`, `bitarray`, and `packaging`. Specific dependency versions are defined in the project configuration files.

**Hardware notes:**

- Arduino workflows do not require NI-DAQmx drivers.
- NI-DAQ workflows require the [NI-DAQmx drivers](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#494676).

PYDAQ is tested up to Python 3.14. It may run on newer versions, but without guarantees.

---

## Graphical user interface

All main workflows are available from a single graphical interface.

Launch the GUI with:

```python
from pydaq.pydaq_global import PydaqGui

PydaqGui()
```

More details are available in the [documentation](https://pydaq.org) and in the [Jupyter notebook examples](examples).

---

## Screenshots

<p align="center">
  <img src="docs/img/new_gif.gif" alt="PYDAQ graphical interface" class="center" width="75%" height="75%">
</p>

---

## Contributing

Contributions are welcome. Please read the [contribution guide](CONTRIBUTING.md) before submitting a pull request.

---

## Citation

[![DOI](https://joss.theoj.org/papers/10.21105/joss.05662/status.svg)](https://doi.org/10.21105/joss.05662)

This is the **seminal publication** of the PYDAQ project and should be cited in any work that uses PYDAQ.

- Martins, S. A. M. (2023). *PYDAQ: Data Acquisition and Experimental Analysis with Python*. Journal of Open Source Software, 8(92), 5662. https://doi.org/10.21105/joss.05662

```bibtex
@article{Martins_PYDAQ_Data_Acquisition_2023,
  author  = {Martins, Samir Angelo Milani},
  doi     = {10.21105/joss.05662},
  journal = {Journal of Open Source Software},
  month   = dec,
  number  = {92},
  pages   = {5662},
  title   = {{PYDAQ: Data Acquisition and Experimental Analysis with Python}},
  url     = {https://joss.theoj.org/papers/10.21105/joss.05662},
  volume  = {8},
  year    = {2023}
}
```

Additional related publications are available in the [`papers`](https://github.com/samirmartins/pydaq/tree/main/papers) directory.
