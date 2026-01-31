Installation
============

Requirements
------------

- Python 3.12 or 3.13
- pip or uv package manager

.. warning::

   **Python 3.13 on Windows**: Currently not supported due to numpy/librosa compatibility issues.
   Windows users should use Python 3.12. This limitation does not affect Linux or macOS users.

Install from PyPI
-----------------

.. code-block:: bash

   pip install mixref

Or using uv:

.. code-block:: bash

   uv pip install mixref

Development Installation
------------------------

Clone the repository:

.. code-block:: bash

   git clone https://github.com/caparrini/mixref.git
   cd mixref

Install with uv:

.. code-block:: bash

   uv sync --all-extras

This installs mixref with all dependencies including development and documentation tools.

Verify Installation
-------------------

Check that mixref is installed correctly:

.. code-block:: bash

   mixref --version

You should see output like::

   mixref version 0.1.0

System Requirements
-------------------

**Supported Platforms**

- **Linux**: Python 3.12, 3.13 ✅
- **macOS**: Python 3.12, 3.13 ✅
- **Windows**: Python 3.12 only ⚠️

.. note::

   Our CI/CD pipeline tests on all three platforms. See test results at 
   https://github.com/caparrini/mixref/actions

**Audio Libraries**

mixref uses system audio libraries for file I/O:

- **Linux**: libsndfile (usually pre-installed)
- **macOS**: libsndfile via Homebrew: ``brew install libsndfile``
- **Windows**: Included in Python packages

**Optional: FFmpeg**

For MP3 support, install FFmpeg:

- **Linux**: ``apt-get install ffmpeg``
- **macOS**: ``brew install ffmpeg``
- **Windows**: Download from https://ffmpeg.org
