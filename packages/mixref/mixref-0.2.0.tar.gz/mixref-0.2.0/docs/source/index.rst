mixref Documentation
====================

**CLI Audio Analyzer for Music Producers**

Sharp, opinionated audio analysis for electronic music production. Built for producers who need quick insights on Drum & Bass, Techno, and House tracks.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index
   auto_examples/index

Features
--------

🎚️ **LUFS Metering**
   EBU R128 loudness measurement with platform-specific targets (Spotify, YouTube, Club)

🎵 **BPM & Key Detection**
   Genre-aware tempo and key analysis with Camelot notation

📊 **Spectral Analysis**
   Frequency band breakdown for mixing decisions (Sub, Bass, Mids, Highs, Air)

🔄 **A/B Comparison**
   Compare your mix against professional references with smart suggestions

🎯 **Genre Presets**
   Tailored feedback for DnB, Techno, and House productions

Getting Started
---------------

Install mixref::

   pip install mixref

Analyze a track::

   mixref analyze my_track.wav

Compare with a reference::

   mixref compare my_mix.wav reference.wav --genre dnb

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
