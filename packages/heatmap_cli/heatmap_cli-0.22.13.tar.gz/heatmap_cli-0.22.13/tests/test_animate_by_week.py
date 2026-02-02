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

from pathlib import Path

def test_animate_by_week(cli_runner, csv_file, tmpdir):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "--animate-by-week", "-y", "2023", "-w", "1")
    assert ret.returncode == 0
    
    output_dir = Path(str(tmpdir.join("scripttest", "output")))
    gif_files = list(output_dir.glob("*.gif"))
    assert len(gif_files) == 1
    assert "animated" in gif_files[0].name

def test_animate_by_week_first_week(cli_runner, csv_file, tmpdir):
    # Testing week 1 case (config.week >= 2 else ...)
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "--animate-by-week", "-y", "2023", "-w", "1")
    assert ret.returncode == 0

def test_animate_by_week_later_week(cli_runner, csv_file, tmpdir):
    # Testing week >= 2 case
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "--animate-by-week", "-y", "2023", "-w", "2")
    assert ret.returncode == 0
