"""
Unit tests for utility functions.
"""

import pytest
from src.utils import format_file_size, parse_save_filename


class TestFormatFileSize:
    """Tests for format_file_size function."""

    def test_bytes(self):
        assert format_file_size(0) == "0.0 B"
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(1023) == "1023.0 B"

    def test_kilobytes(self):
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(10240) == "10.0 KB"

    def test_megabytes(self):
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 5) == "5.0 MB"
        assert format_file_size(1024 * 1024 * 100) == "100.0 MB"

    def test_gigabytes(self):
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(1024 * 1024 * 1024 * 2) == "2.0 GB"

    def test_terabytes(self):
        assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"


class TestParseSaveFilename:
    """Tests for parse_save_filename function."""

    def test_manual_save(self):
        result = parse_save_filename("HL-0-0.sav")
        assert result["slot"] == "Slot 0"
        assert result["type"] == "Manual Save"
        assert result["display"] == "Slot 0 - Manual Save"

    def test_autosave_1(self):
        result = parse_save_filename("HL-0-1.sav")
        assert result["slot"] == "Slot 0"
        assert result["type"] == "Auto #1"
        assert result["display"] == "Slot 0 - Auto #1"

    def test_autosave_higher_slot(self):
        result = parse_save_filename("HL-3-2.sav")
        assert result["slot"] == "Slot 3"
        assert result["type"] == "Auto #2"
        assert result["display"] == "Slot 3 - Auto #2"

    def test_unknown_format(self):
        result = parse_save_filename("random_save.sav")
        assert result["slot"] == "Unknown"
        assert result["type"] == "Save"
        assert result["display"] == "random_save.sav"

    def test_partial_match(self):
        result = parse_save_filename("HL-notanumber.sav")
        assert result["slot"] == "Unknown"
        assert result["type"] == "Save"
