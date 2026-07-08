import os
import tempfile
import unittest
from unittest.mock import patch

import main


class MainProcessingTests(unittest.TestCase):
    def test_get_new_image_files_filters_existing_and_non_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = os.path.join(tmpdir, "old.jpg")
            new_image = os.path.join(tmpdir, "new.png")
            non_image = os.path.join(tmpdir, "notes.txt")
            for path in [existing, new_image, non_image]:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("x")

            with patch.object(main, "SD_CARD_FOLDER", tmpdir):
                known = {"old.jpg"}
                result = main.get_new_image_files(known)

            self.assertEqual(result, ["new.png"])


if __name__ == "__main__":
    unittest.main()
