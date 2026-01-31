"""Tests classes in modalities module"""

import unittest
from pydantic import BaseModel

from aind_data_schema_models.modalities import Modality


class TestModality(unittest.TestCase):
    """Tests methods in Modality class"""

    def test_from_abbreviation(self):
        """Tests modality can be constructed from abbreviation"""

        self.assertEqual(Modality.ECEPHYS, Modality.from_abbreviation("ecephys"))

    def test_type_resolution(self):
        """Define a class using .ONE_OF and ensure that there are no issues passing an example of that type"""

        class TEST_CLASS(BaseModel):
            """Test class with modality field"""

            modality: Modality.ONE_OF

        test_instance = TEST_CLASS(modality=Modality.EMG)
        self.assertIsNotNone(test_instance)

        json = test_instance.model_dump_json()
        deserialized_instance = TEST_CLASS.model_validate_json(json)
        self.assertEqual(test_instance, deserialized_instance)


if __name__ == "__main__":
    unittest.main()
