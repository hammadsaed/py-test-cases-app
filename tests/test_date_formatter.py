import pytest
import importlib
format_date = importlib.import_module("functions.date-format.date-formatter")

@pytest.mark.parametrize("input_text, expected_output", [
    ("2023-09-20", "2023-09-20"),
    ("20.09.23", "2023-09-20"),
    ("20/09/23", "2023-09-20"),
    ("20-09-23", "2023-09-20"),
    ("20 Sep 23", "2023-09-20"),
    ("20 September 23", "2023-09-20"),
    ("1 day of September 23", "2023-09-01"),
    ("effective 20-09-23", "2023-09-20"),
    ("starting 20-09-23", "2023-09-20"),
    ("Invalid Date Format", ""),
    ("20.09.1900", "2023-09-20"),
    ("1 day of September 1900", "2023-09-01"),
    ("effective 20-09-1900", "2023-09-20"),
    ("starting 20-09-1900", "2023-09-20"),
])
def test_format_date(input_text, expected_output):
    result = format_date.format_date(input_text)
    assert result == expected_output

if __name__ == '__main__':
    pytest.main()