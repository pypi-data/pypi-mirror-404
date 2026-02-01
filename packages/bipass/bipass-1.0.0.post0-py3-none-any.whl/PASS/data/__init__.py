# The Clear BSD License
#
# Copyright (c) 2024 Julia Burton
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted (subject to the limitations in the disclaimer
# below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Data utilities for BI-PASS.

This module provides functions for accessing bundled trajectory data,
including on-demand extraction from compressed archives.
"""

import zipfile
from importlib import resources
from pathlib import Path

# Cache directory for extracted trajectories (in user's cache dir)
_CACHE_DIR = Path.home() / ".cache" / "bipass" / "trajectories"


def _get_zip_path() -> Path:
    """Get path to the bundled trajectory zip file using importlib.resources."""
    return resources.files(__package__).joinpath("simulated_trajectories.zip")


def ensure_trajectories_extracted() -> Path:
    """Extract trajectory CSVs from zip if not already present.

    This function checks if the trajectory CSV files have been extracted
    from the bundled zip archive. If not, it extracts them to a cache
    directory in the user's home folder.

    Returns:
        Path: Path to the directory containing the extracted CSV files.

    Raises:
        FileNotFoundError: If the trajectory zip file is not found.
    """
    csv_dir = _CACHE_DIR / "csv"

    # Check if already extracted (directory exists and has CSV files)
    if csv_dir.exists() and any(csv_dir.glob("*.csv")):
        return csv_dir

    # Get the zip file from package resources
    zip_path = _get_zip_path()

    # For traversable resources, we need to handle both Path and non-Path cases
    if hasattr(zip_path, "is_file") and zip_path.is_file():
        # Direct file path (editable install or regular install)
        zip_file_path = Path(zip_path)
    else:
        raise FileNotFoundError(
            "Trajectory data archive not found in package.\n"
            "Please ensure the package was installed correctly with data files."
        )

    # Create cache directory
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Extract the zip file
    print(f"Extracting trajectory data to {_CACHE_DIR}...")
    with zipfile.ZipFile(zip_file_path, "r") as z:
        z.extractall(_CACHE_DIR)

    csv_count = len(list(csv_dir.glob("*.csv")))
    print(f"Extracted {csv_count} trajectory files.")

    return csv_dir


def get_trajectories_path() -> Path:
    """Get the path to the trajectory data directory, extracting if needed.

    This is a convenience function that ensures trajectories are extracted
    and returns the path to the directory containing them.

    Returns:
        Path: Path to the directory containing trajectory CSV files.
    """
    return ensure_trajectories_extracted()


def list_trajectories() -> list[Path]:
    """List all available trajectory CSV files.

    Returns:
        list[Path]: Sorted list of paths to trajectory CSV files.
    """
    csv_dir = ensure_trajectories_extracted()
    return sorted(csv_dir.glob("*.csv"))
