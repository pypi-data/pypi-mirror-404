import json
import unittest

from binsolver import Bin, Item, PackRequest


class TestModels(unittest.TestCase):
    def test_serialization(self):
        req = PackRequest(
            objective="minBins",
            items=[Item(id="item-1", w=10, h=10, d=10, quantity=1)],
            bins=[Bin(id="bin-1", w=100, h=100, d=100, quantity=1)],
        )

        data = req.model_dump(mode="json", by_alias=True, exclude_none=True)

        self.assertEqual(data["objective"], "minBins")
        self.assertEqual(data["items"][0]["w"], 10.0)
        self.assertEqual(data["bins"][0]["id"], "bin-1")

        req.allow_unplaced = True
        data = req.model_dump(mode="json", by_alias=True, exclude_none=True)
        self.assertIn("allowUnplaced", data)
        self.assertTrue(data["allowUnplaced"])

    def test_snake_case_input(self):
        """Test that we can initialize using snake_case args."""
        item = Item(id="1", w=1, h=1, d=1, allow_rotation=False)
        self.assertFalse(item.allow_rotation)

        data = item.model_dump(mode="json", by_alias=True, exclude_none=True)
        self.assertIn("allowRotation", data)
        self.assertFalse(data["allowRotation"])


if __name__ == "__main__":
    unittest.main()
