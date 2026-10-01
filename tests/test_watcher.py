import importlib.util
import os
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "watcher", os.path.join(os.path.dirname(__file__), "..", "scripts", "adxl_toggle_watcher.py"))
w = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(w)


class ToggleTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        w.PRINTER_CFG = os.path.join(self.dir.name, "printer.cfg")
        w.BACKUP_DIR = os.path.join(self.dir.name, "bk")

    def tearDown(self):
        self.dir.cleanup()

    def write(self, text):
        with open(w.PRINTER_CFG, "w") as f:
            f.write(text)

    def read(self):
        with open(w.PRINTER_CFG) as f:
            return f.read()

    def test_enable_disable_roundtrip(self):
        self.write("[mcu]\n#[include adxl345.cfg]\n")
        self.assertIs(w.include_is_active(), False)
        self.assertTrue(w.set_include(True))
        self.assertIn("\n[include adxl345.cfg]\n", self.read())
        self.assertIs(w.include_is_active(), True)
        self.assertTrue(w.set_include(False))
        self.assertIn("#[include adxl345.cfg]", self.read())
        self.assertGreaterEqual(len(os.listdir(w.BACKUP_DIR)), 1)

    def test_spaced_comment(self):
        self.write("# [include adxl345.cfg]\n")
        self.assertTrue(w.set_include(True))
        self.assertIs(w.include_is_active(), True)

    def test_missing_line(self):
        self.write("[mcu]\n")
        self.assertIsNone(w.include_is_active())
        self.assertFalse(w.set_include(False))
        self.assertTrue(w.set_include(True))
        self.assertIs(w.include_is_active(), True)


if __name__ == "__main__":
    unittest.main()
