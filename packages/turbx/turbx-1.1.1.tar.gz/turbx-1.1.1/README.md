# turbx
[![PyPI version](https://badge.fury.io/py/turbx.svg)](https://badge.fury.io/py/turbx)
[![Downloads](https://pepy.tech/badge/turbx)](https://pepy.tech/project/turbx)
<!---
[![pipeline status](https://gitlab.iag.uni-stuttgart.de/transi/turbx/badges/master/pipeline.svg)](https://gitlab.iag.uni-stuttgart.de/transi/turbx/-/commits/master)
-->

## About

`turbx` is a package for processing turbulent flow datasets. Primary data access classes are `super()`ed wrappers of `h5py.File` that make data & metadata access tidy and performant. Workloads requiring heavy I/O and compute are made scalable using parallelization and high-performance collective MPI-IO.

## Pre-installation requirements

### `h5py`
`turbx` is designed to be used with parallel-mode `h5py`, the `python3` API for `HDF5`. Most basic workflows will still work transparently with the basic serial install of `h5py`, however data-heavy workflows will require the full API functionality. This requires:

- A parallel `HDF5` installation
- `h5py` built with `HDF5_MPI="ON"`; see [h5py docs](https://docs.h5py.org/en/stable/mpi.html)

<br>

Confirm that `h5py` was built with MPI support:
```python
>>> import h5py
>>> h5py.get_config().mpi
True
```


### `mpi4py`

High-performance collective MPI-IO and MPI operations are handled with `mpi4py`. This requires:

- An MPI implementation such as `OpenMPI` or `MPICH`
- `mpi4py`; see [mpi4py docs](https://mpi4py.readthedocs.io/en/stable/install.html)




## Installation

### TL;DR
Install binary directly from [PyPI](https://pypi.org/project/turbx):

```
python3 -m pip install --upgrade turbx
```

---

### Non-root install with `--user`

The `--user` flag can be added to install to `~/.local/lib/pythonX.Y/site-packages` rather than `site-packages` of the `python3` installation itself. This is often required for HPC environments where installing packages for the system `python3` is not allowed for regular users.

<br>

### Editable installs

`turbx` can also be installed from source in `editable` mode (see [setuptools docs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)). Once the source is acquired (PyPI or GitLab), the source can be installed from the project root folder:

```
python3 -m pip install --upgrade -e .
```

<br>

### Installing on systems with no outbound network access

If the restricted install environment requires `devpi-server`:


**On a local machine with internet access:**
```
devpi-server
```

**On a local machine with internet access:**
```
ssh -R <remote_port>:localhost:<local_devpi_port> user@domain.com
```

- `<local_devpi_port>` is the port on which `devpi-server` is running locally
- `<remote_port>` is an arbitrary free port on the system login node used to expose the mirror remotely
- After connecting, the PyPI mirror will be reachable on the server side at: `http://localhost:<remote_port>`

**On the remote system:**
```
python3 -m pip install --upgrade [--user] [--editable] --index-url http://localhost:<remote_port>/root/pypi/+simple/ <package-or-path>
```

