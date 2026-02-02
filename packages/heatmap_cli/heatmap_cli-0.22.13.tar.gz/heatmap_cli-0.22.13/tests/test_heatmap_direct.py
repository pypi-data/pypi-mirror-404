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
import pandas as pd
from heatmap_cli.heatmap import _generate_heatmap

def test_generate_heatmap_direct(tmpdir):
    config = argparse.Namespace(
        annotate=True,
        cbar=True,
        cmap_min=0,
        cmap_max=10000,
        author="Test Author",
        title="Test Title",
        output_dir=str(tmpdir),
        format="png",
        open=False
    )
    
    # Create a small dummy pivoted dataframe
    df = pd.DataFrame(
        [[10, 20], [30, 40]], 
        index=[1, 2], 
        columns=["01", "02"]
    )
    
    # This should cover many missing lines by running in the same process
    _generate_heatmap(1, "vlag", config, df)
    
    # Check if file was created
    output_files = list(Path(str(tmpdir)).glob("*.png"))
    assert len(output_files) >= 1

from pathlib import Path
