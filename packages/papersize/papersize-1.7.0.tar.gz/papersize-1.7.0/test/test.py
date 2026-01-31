# Copyright 2017-2025 Louis Paternault
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests"""

import unittest
from decimal import Decimal

import papersize


class TestDefinition(unittest.TestCase):
    """Test format definitions."""

    # pylint: disable = invalid-name

    def testValidDefinitions(self):
        """Test that :data:`papersize.SIZES` is correctly defined."""
        for key, value in papersize.SIZES.items():
            self.assertEqual(
                papersize.parse_papersize(key), papersize.parse_papersize(value)
            )


class TestParse(unittest.TestCase):
    """Test parsing related functions."""

    # pylint: disable = invalid-name

    def assertIterAlmostEqual(self, iter1, iter2):
        """Assert iterators of elements are almost items.

        Both arguments are expected to be iterators of the same size, and
        iterators with the same indexes are checked to be almost equal.
        """

        for left, right in zip(iter1, iter2):
            self.assertAlmostEqual(Decimal(left), Decimal(right))

    def testExceptions(self):
        """Test module exceptions"""
        try:
            papersize.parse_length("cm")
        except papersize.CouldNotParse as error:
            self.assertEqual(str(error), "Could not parse string 'cm'.")

        try:
            papersize.rotate((1, 2), "portrait")  # pyright: ignore[reportArgumentType]
        except papersize.UnknownOrientation as error:
            self.assertEqual(
                str(error),
                "'portrait' is not one of `papersize.PORTRAIT` or `papersize.LANDSCAPE`",
            )

    def testParseLength(self):
        """Test :func:`papersize.parse_length`."""
        for args, result in [(("10cm", "mm"), 100), (("10in",), 722.7)]:
            self.assertAlmostEqual(papersize.parse_length(*args), Decimal(result))

        self.assertRaises(papersize.CouldNotParse, papersize.parse_length, "cm")

    def testParseCouple(self):
        """Test :func:`papersize.parse_couple`."""
        for args, result in [
            (("10cmx1mm",), (284.5275591, 2.845275591)),
            (("10cmx1mm", "mm"), (100, 1)),
            (("10cm 1mm", "mm"), (100, 1)),
            (("10cm×1mm", "mm"), (100, 1)),
            (("2pc x 3pt", "pt"), (24, 3)),
            (("2cc x 3dd", "dd"), (24, 3)),
        ]:
            with self.subTest(args=args, result=result):
                self.assertIterAlmostEqual(papersize.parse_couple(*args), result)

        self.assertRaises(
            papersize.CouldNotParse, papersize.parse_papersize, "2cmx2cm 2cm"
        )

    def testParsePaperSize(self):
        """Test :func:`papersize.parse_papersize`."""
        for args, result in [
            (("A4", "cm"), (21, 29.7)),
            (("20cm x 1mm", "cm"), (20, 0.1)),
            (("Ledger",), (1228.59, 794.97)),
        ]:
            self.assertIterAlmostEqual(papersize.parse_papersize(*args), result)

        self.assertRaises(
            papersize.CouldNotParse, papersize.parse_papersize, "Hello, world!"
        )

    def testConvertLength(self):
        """Test :func:`papersize.convert_length`."""
        for args, result in [((10, "cm", "mm"), 100), ((1, "mm", "pt"), 2.845275591)]:
            self.assertAlmostEqual(papersize.convert_length(*args), Decimal(result))


class TestOrientation(unittest.TestCase):
    """Test orientation related tools."""

    # pylint: disable = invalid-name

    def testPortraitLandscape(self):
        """Test portrait/landscape functions."""
        self.assertTrue(papersize.is_portrait(10, 11))
        self.assertTrue(papersize.is_portrait(10, 10))
        self.assertFalse(papersize.is_portrait(11, 10))

        self.assertFalse(papersize.is_landscape(10, 11))
        self.assertTrue(papersize.is_landscape(10, 10))
        self.assertTrue(papersize.is_landscape(11, 10))

        self.assertFalse(papersize.is_square(10, 11))
        self.assertTrue(papersize.is_square(10, 10))
        self.assertFalse(papersize.is_square(11, 10))

    def testStrictFuzzy(self):
        """Test strict and fuzzy options."""
        # Test strict
        self.assertTrue(papersize.is_landscape(10, 10, strict=False))
        self.assertTrue(papersize.is_portrait(10, 10, strict=False))
        self.assertFalse(papersize.is_landscape(10, 10, strict=True))
        self.assertFalse(papersize.is_portrait(10, 10, strict=True))
        self.assertTrue(papersize.is_landscape(10, 10))
        self.assertTrue(papersize.is_portrait(10, 10))

        # Test fuzzy
        self.assertTrue(papersize.is_square(1, 1.000000001, fuzzy=True))
        self.assertFalse(papersize.is_square(1, 1.000000001, fuzzy=False))
        self.assertTrue(papersize.is_portrait(1.000000001, 1, fuzzy=True))
        self.assertFalse(papersize.is_portrait(1.000000001, 1, fuzzy=False))
        self.assertTrue(papersize.is_landscape(1, 1.000000001, fuzzy=True))
        self.assertFalse(papersize.is_landscape(1, 1.000000001, fuzzy=False))

        # Test fuzzy and ndigits
        self.assertFalse(papersize.is_square(1, 1.000000001, fuzzy=True, ndigits=10))
        self.assertFalse(papersize.is_square(1, 1.000000001, fuzzy=False, ndigits=10))
        self.assertFalse(papersize.is_portrait(1.000000001, 1, fuzzy=True, ndigits=10))
        self.assertFalse(papersize.is_portrait(1.000000001, 1, fuzzy=False, ndigits=10))
        self.assertFalse(papersize.is_landscape(1, 1.000000001, fuzzy=True, ndigits=10))
        self.assertFalse(
            papersize.is_landscape(1, 1.000000001, fuzzy=False, ndigits=10)
        )

        # Test strict and fuzzy
        self.assertTrue(papersize.is_square(1, 1.000000001, fuzzy=True))
        self.assertFalse(papersize.is_square(1, 1.000000001, fuzzy=False))
        self.assertTrue(papersize.is_square(1.000000001, 1, fuzzy=True))
        self.assertFalse(papersize.is_square(1.000000001, 1, fuzzy=False))

    def testRotate(self):
        """Test :func:`papersize.rotate` function."""
        self.assertEqual(papersize.rotate((10, 11), papersize.PORTRAIT), (10, 11))
        self.assertEqual(papersize.rotate((10, 11), papersize.LANDSCAPE), (11, 10))

        self.assertRaises(
            papersize.UnknownOrientation, papersize.rotate, (1, 2), "portrait"
        )


class TestHelp(unittest.TestCase):
    """Test that every unit or paper format are described"""

    # pylint: disable = invalid-name

    def testHelpUnits(self):
        """Test that units are correctly described"""
        self.assertSetEqual(
            {unit.lower() for unit in papersize.UNITS if unit},
            {unit.lower() for unit in papersize.UNITS_HELP},
        )

    def testSizesHelp(self):
        """Test that sizes are correctly described"""
        self.assertSetEqual(
            {size.lower() for size in papersize.SIZES if size},
            {size.lower() for size in papersize.SIZES_HELP},
        )
