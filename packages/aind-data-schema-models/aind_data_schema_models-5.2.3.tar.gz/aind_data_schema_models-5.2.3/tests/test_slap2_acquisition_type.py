"""Tests classes in slap2_acquisition_type module"""

import unittest

from aind_data_schema_models.slap2_acquisition_type import Slap2AcquisitionType


class TestSlap2AcquisitionType(unittest.TestCase):
    """Tests methods in Slap2AcquisitionType class"""

    def test_class_construction(self):
        """Tests enum can be instantiated via string"""

        self.assertEqual(Slap2AcquisitionType.INTEGRATION, Slap2AcquisitionType("integration"))


if __name__ == "__main__":
    unittest.main()
