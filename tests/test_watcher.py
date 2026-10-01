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


SAVE = "#*# <---------------------- SAVE_CONFIG ---------------------->\n#*# DO NOT EDIT THIS BLOCK OR BELOW.\n#*#\n#*# [probe]\n#*# z_offset = 3.001\n"


class SaveConfigTest(ToggleTest):
    def pos(self, text):
        c = self.read()
        return c.index(text), c.index("SAVE_CONFIG")

    def test_include_moved_above_save_config(self):
        self.write("[mcu]\n\n" + SAVE + "\n[include adxl_toggle.cfg]\n\n#[include adxl345.cfg]\n")
        w.ensure_lines_cli(w.PRINTER_CFG, ["[include adxl_toggle.cfg]", "#[include adxl345.cfg]"])
        c = self.read()
        for t in ("[include adxl_toggle.cfg]", "#[include adxl345.cfg]"):
            self.assertEqual(c.count(t), 1)
            i, m = self.pos(t)
            self.assertLess(i, m)
        self.assertIs(w.include_is_active(), False)  # stayed disabled

    def test_fresh_add_goes_above_marker(self):
        self.write("[mcu]\n" + SAVE)
        w.ensure_lines_cli(w.PRINTER_CFG, ["[include adxl_toggle.cfg]"])
        i, m = self.pos("[include adxl_toggle.cfg]")
        self.assertLess(i, m)
        self.assertIn("z_offset = 3.001", self.read())

    def test_enable_below_marker_relocates(self):
        self.write("[mcu]\n" + SAVE + "\n#[include adxl345.cfg]\n")
        self.assertTrue(w.set_include(True))
        i, m = self.pos("\n[include adxl345.cfg]")
        self.assertLess(i, m)
        self.assertEqual(self.read().count("include adxl345.cfg"), 1)

    def test_enable_missing_inserts_above_marker(self):
        self.write("[mcu]\n" + SAVE)
        self.assertTrue(w.set_include(True))
        i, m = self.pos("[include adxl345.cfg]")
        self.assertLess(i, m)

    def test_idempotent(self):
        self.write("[mcu]\n[include adxl_toggle.cfg]\n#[include adxl345.cfg]\n" + SAVE)
        before = self.read()
        w.ensure_lines_cli(w.PRINTER_CFG, ["[include adxl_toggle.cfg]", "#[include adxl345.cfg]"])
        self.assertEqual(before, self.read())


