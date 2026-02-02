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
from heatmap_cli.heatmap import (
    _sanitize_string_for_filename,
    _generate_filename,
    _generate_title,
)

def test_sanitize_string_for_filename():
    assert _sanitize_string_for_filename("Hello World!") == "hello_world"
    assert _sanitize_string_for_filename("  Spaces  And  UPPER  ") == "spaces_and_upper"
    assert _sanitize_string_for_filename("Special@#$%^&*()Chars") == "specialchars"
    # Long string
    long_str = "a" * 200
    assert len(_sanitize_string_for_filename(long_str)) == 100

def test_generate_filename():
    config = argparse.Namespace(annotate=True, format="png")
    assert "001_title_vlag_annotated.png" == _generate_filename(config, 1, "vlag", "Title")
    
    config.annotate = False
    assert "001_title_vlag.png" == _generate_filename(config, 1, "vlag", "Title")

    config.format = "gif"
    assert "001_title_vlag_animated.gif" == _generate_filename(config, 1, "vlag", "Title")

def test_generate_title():
    config = argparse.Namespace(
        title=None, 
        year=2026, 
        week=52, 
        start_date=None, 
        end_date=None
    )
    assert _generate_title(config) == "Year 2026: Total Daily Walking Steps"
    
    config.week = 10
    assert _generate_title(config) == "Year 2026: Total Daily Walking Steps Through Week 10"
    
    config.start_date = "2026-01-01"
    config.end_date = "2026-01-31"
    assert "From 2026-01-01 to 2026-01-31" in _generate_title(config)
    
    config.title = "Custom Title"
    assert _generate_title(config) == "Custom Title"
