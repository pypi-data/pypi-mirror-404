# Copyright (C) 2026 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch
from heatmap_cli.heatmap import run, _read_and_prepare_data, _refresh_output_dir

def test_file_not_found_error_direct(tmpdir):
    config = argparse.Namespace(
        input_filename="non_existent.csv",
        output_dir=str(tmpdir),
        purge=False,
        yes=False
    )
    with pytest.raises(FileNotFoundError):
        _read_and_prepare_data(config)

def test_duplicate_dates_error_direct(tmpdir):
    csv_path = Path(tmpdir) / "duplicate.csv"
    with open(csv_path, "w") as f:
        f.write("2023-01-01,100\n")
        f.write("2023-01-01,200\n")
    
    config = argparse.Namespace(
        input_filename=str(csv_path),
        annotate=False
    )
    with pytest.raises(ValueError, match="Duplicate dates found"):
        _read_and_prepare_data(config)

def test_refresh_output_dir_purge_os_error(tmpdir):
    output_dir = Path(tmpdir) / "output"
    output_dir.mkdir()
    
    config = argparse.Namespace(
        output_dir=str(output_dir),
        purge=True,
        yes=True
    )
    
    with patch("heatmap_cli.heatmap.shutil.rmtree") as mocked_rmtree:
        mocked_rmtree.side_effect = OSError("Access denied")
        # Should not raise, but log error
        _refresh_output_dir(config)
        mocked_rmtree.assert_called_once()

def test_missing_csv_filename_cli(cli_runner):
    ret = cli_runner()
    assert "the following arguments are required: CSV_FILENAME" in ret.stderr
