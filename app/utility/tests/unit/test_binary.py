from unittest import TestCase

from utility.binary import get_human_readable_size


class HumanReadableSizeUtilityTests(TestCase):
    """Test the get_human_readable_size function."""

    def test_raises_for_invalid_base(self) -> None:
        """Test that an exception is raised for an invalid base."""
        self.assertRaises(ValueError, get_human_readable_size, 12335415, base=10)

    def test_raises_for_negative_size(self) -> None:
        """Test that an exception is raised when the number is negative."""
        self.assertRaises(ValueError, get_human_readable_size, -81235283)

    def test_bytes_less_than_base(self) -> None:
        """Test when the number of bytes is less than the base."""
        param_list = [
            (0, 1024, "0 B"),
            (0, 1000, "0 B"),
            (5, 1024, "5 B"),
            (5, 1000, "5 B"),
            (1023, 1024, "1023 B"),
            (999, 1000, "999 B"),
        ]
        for size_bytes, base, expected in param_list:
            with self.subTest():
                size = get_human_readable_size(size_bytes, base=base, precision=2)
                self.assertEqual(size, expected)

    def test_bytes_equal_to_base_power(self) -> None:
        """Test when the number of bytes is equal to the base to some power."""
        param_list = [
            (1024, 1024, "1.00 KiB"),
            (1000, 1000, "1.00 KB"),
            (1024**2, 1024, "1.00 MiB"),
            (1000**2, 1000, "1.00 MB"),
            (1024**3, 1024, "1.00 GiB"),
            (1000**3, 1000, "1.00 GB"),
            (1024**4, 1024, "1.00 TiB"),
            (1000**4, 1000, "1.00 TB"),
        ]
        for size_bytes, base, expected in param_list:
            with self.subTest():
                size = get_human_readable_size(size_bytes, base=base, precision=2)
                self.assertEqual(size, expected)

    def test_in_between_sizes(self) -> None:
        """Test when the number of bytes is not equivalent to the base to some power."""
        param_list = [
            ((1024**2) / 2, 1024, "512.00 KiB"),
            ((1000**3) / 2, 1000, "500.00 MB"),
        ]
        for size_bytes, base, expected in param_list:
            with self.subTest():
                size = get_human_readable_size(size_bytes, base=base, precision=2)
                self.assertEqual(size, expected)
