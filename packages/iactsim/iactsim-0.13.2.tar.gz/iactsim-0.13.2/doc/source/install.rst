.. Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
.. SPDX-License-Identifier: GPL-3.0-or-later
..
.. This file is part of iactsim.
..
.. iactsim is free software: you can redistribute it and/or modify
.. it under the terms of the GNU General Public License as published by
.. the Free Software Foundation, either version 3 of the License, or
.. (at your option) any later version.
..
.. iactsim is distributed in the hope that it will be useful,
.. but WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
.. GNU General Public License for more details.
..
.. You should have received a copy of the GNU General Public License
.. along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

.. _install:

Install
=======

Prerequisites
~~~~~~~~~~~~~

* **Python:** >= 3.11
* **Compiler:** gcc (standard) or nvcc (optional)
* **CMake:** >= 3.15
* **Runtime:** NVIDIA Drivers, CUDA, CuPy

Environment setup
~~~~~~~~~~~~~~~~~

We strongly recommend using a virtual environment (e.g., mamba or conda):

.. code-block:: bash

    mamba create -n simenv python=3.13
    mamba activate simenv

Install via PyPI
~~~~~~~~~~~~~~~~

If you have the prerequisites installed, you can install the latest release directly:

.. code-block:: bash

    pip install iactsim -v

Optional: using NVHPC compilers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Building with gcc is the standard and requires no special configuration. However, if you specifically wish to use the nvcc, you must configure the environment **before** installation.

Please refer to the **NVIDIA HPC SDK** section in :ref:`runtime_configuration` for detailed instructions on setting up the environment.

Custom Compiler Flags
~~~~~~~~~~~~~~~~~~~~~

You can customize the build options by passing arguments to CMake via pip. The following flags are available:

* **CMAKE_CXX_COMPILER=<compiler>**: specify the C++ compiler executable (e.g., nvcc, g++).
* **USE_ZLIBNG=<ON|OFF>**: enable/disable zlib-ng support. Default is ON.
  For the C++ part, by default `zlib-ng <https://github.com/zlib-ng/zlib-ng>`_ (*zlib data compression library for the next generation systems*) will be used (CMake will clone the repo automatically). **This is strongly recommended if you plan to read compressed CORSIKA files.**
  If you have to use the standard system `zlib <https://zlib.net/>`_, you can set this to OFF.

Example: explicitly use nvcc and disable zlib-ng
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    python -m pip install . -v -C cmake.args="-DCMAKE_CXX_COMPILER=nvcc;-DUSE_ZLIBNG=OFF"

Install from source
~~~~~~~~~~~~~~~~~~~

1. Clone the repository:

   .. code-block:: bash

      git clone https://gitlab.com/davide.mollica/iactsim.git
      cd iactsim

2. Editable install:
   First, install the build dependencies required for the editable install:

   .. code-block:: bash

      pip install scikit-build-core pybind11 "setuptools_scm[toml]>=8.0" cmake ninja

   Then, install the package in editable mode. This configuration disables build isolation, ensuring that **only modified C++ files will be recompiled**:

   .. code-block:: bash

      python -m pip install --no-build-isolation -e .

.. _runtime_configuration:

Runtime Configuration
~~~~~~~~~~~~~~~~~~~~~

1. Install CuPy (required)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

iactsim relies on CuPy for GPU offloading. You must install the cupy package that matches your specific CUDA version.

.. code-block:: bash

    pip install cupy-cuda<XXX>

Replace <XXX> with your CUDA version (e.g., cupy-cuda12x for CUDA 12).
For detailed instructions, refer to the `CuPy documentation <https://docs.cupy.dev/en/stable/install.html>`_.

2. NVIDIA HPC SDK (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are using the NVIDIA HPC SDK to provide CUDA libraries, you **must** `configure the enviroment <https://docs.nvidia.com/hpc-sdk//hpc-sdk-install-guide/index.html#install-linux-end-usr-env-settings>`_ so that CuPy can locate the necessary libraries (you can download HPC SDK from the `NVIDIA website <https://developer.nvidia.com/hpc-sdk>`_).

We suggest to use `Environment Modules <https://modules.readthedocs.io/en/latest/>`_ to handle SDK configuration and then define ``NVCC`` and ``CUDA_PATH`` enviromental variables:

.. code-block:: bash

    module load nvhpc
    export NVCC=$NVHPC_ROOT/compilers/bin/nvcc
    export CUDA_PATH=$NVHPC_ROOT/cuda

With ``conda``/``mamba`` enviroments you can use the provided configuration script ``configure_conda_env``

.. code-block:: bash

    mamba activate simenv
    configure_conda_env simenv
    mamba deactivate

This adds an activation script and a deactivation script to the ``simenv`` enviroment that will automatically handle the configuration when it is activated or deactivated.
