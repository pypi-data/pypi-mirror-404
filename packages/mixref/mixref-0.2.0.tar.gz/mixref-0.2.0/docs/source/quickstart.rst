Quick Start
===========

Basic Usage
-----------

Analyze a single track
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mixref analyze my_track.wav

This shows:

- Integrated LUFS loudness
- True peak levels
- Dynamic range (LRA)
- BPM and key (coming soon)
- Spectral balance (coming soon)

Genre-Specific Analysis
~~~~~~~~~~~~~~~~~~~~~~~

Get tailored feedback for your genre:

.. code-block:: bash

   # Drum & Bass
   mixref analyze neurofunk.wav --genre dnb

   # Techno
   mixref analyze warehouse_techno.wav --genre techno

   # House
   mixref analyze deep_house.wav --genre house

Genre presets adjust target ranges and provide specific mixing suggestions.

Compare with Reference
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mixref compare my_mix.wav reference_track.wav

Shows side-by-side comparison:

- Loudness differences
- Spectral balance delta
- Smart suggestions based on the gaps

Machine-Readable Output
~~~~~~~~~~~~~~~~~~~~~~~

Get JSON for automation:

.. code-block:: bash

   mixref analyze track.wav --json > analysis.json

Example output:

.. code-block:: json

   {
     "file": "track.wav",
     "duration": 332.5,
     "lufs": {
       "integrated": -8.2,
       "true_peak": -0.3,
       "lra": 6.2
     }
   }

Common Workflows
----------------

Mastering Check
~~~~~~~~~~~~~~~

Before uploading to streaming:

.. code-block:: bash

   mixref analyze master.wav

Check that:

- LUFS is around -14 for streaming
- True peak is below -1.0 dBTP
- No clipping warnings

Reference Study
~~~~~~~~~~~~~~~

Analyze a professional track:

.. code-block:: bash

   mixref analyze reference.wav --genre dnb

Learn the target numbers for your genre.

Mix vs Master Comparison
~~~~~~~~~~~~~~~~~~~~~~~~

Compare different versions:

.. code-block:: bash

   mixref compare mix_v1.wav mix_v2.wav --focus bass

Focus on specific frequency ranges to dial in your mix.

Next Steps
----------

- Check out :doc:`auto_examples/index` for detailed examples
- Read the :doc:`api/index` for programmatic usage
- Join the community for tips and feedback
