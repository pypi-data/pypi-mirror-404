"""
Getting Started with mixref
============================

This example shows the basic usage of mixref for audio analysis.

mixref is designed for music producers who need quick, actionable insights
about their mixes. This example demonstrates the core workflow.
"""

# %%
# Basic Setup
# -----------
# 
# First, let's check that mixref is installed and working.

import mixref

print(f"mixref version: {mixref.__version__}")

# %%
# Understanding the CLI
# ---------------------
#
# mixref is primarily a command-line tool. While you can use it
# programmatically (we'll show that later), most producers will use
# it from the terminal.
#
# Basic commands:
#
# .. code-block:: bash
#
#    # Get help
#    mixref --help
#
#    # Check version
#    mixref --version
#
#    # Analyze a track (coming soon)
#    mixref analyze my_track.wav
#
#    # Compare with reference (coming soon)
#    mixref compare my_mix.wav reference.wav --genre dnb

# %%
# Next Steps
# ----------
#
# - Learn about LUFS metering in the meters examples
# - Check out BPM detection in the detective examples
# - See A/B comparison workflows in the compare examples
#
# **Tip for producers**: Start by analyzing reference tracks in your genre
# to understand the target loudness and spectral balance.

print("Ready to analyze some audio! 🎧")
