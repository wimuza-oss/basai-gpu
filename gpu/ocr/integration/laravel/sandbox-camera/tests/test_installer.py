from pathlib import Path
import importlib.util
import unittest

module = Path(__file__).resolve().parents[1] / 'install_sandbox.py'
spec = importlib.util.spec_from_file_location('install_sandbox', module)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestInstaller(unittest.TestCase):
    def test_insert_above_recording_panel_when_no_ktp_panel_exists(self):
        text = b'''<div class="col-md-6">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <div class="panel-title"><strong>Rekaman Sidang</strong></div>
                    </div>
                </div>
            </div>'''
        out = mod.install_view(text).decode()
        self.assertIn('<livewire:basai.ktp-camera />', out)
        self.assertLess(out.index('<livewire:basai.ktp-camera'), out.index('Rekaman Sidang'))
        self.assertEqual(mod.install_view(out.encode()).decode(), out)

    def test_replace_existing_ktp_panel_without_touching_recording(self):
        text = '''<div class="col-md-6">
                <div class="panel panel-default" x-data="basKtpCapture()">
                    <strong>Ambil Data KTP Saksi</strong>
                    <button>Buka Kamera</button>
                    <button>Submit ke SIPP</button>
                </div>

                <div class="panel panel-default">
                    <div class="panel-heading">
                        <div class="panel-title"><strong>Rekaman Sidang</strong></div>
                    </div>
                    <div>Upload Audio</div>
                </div>
            </div>'''
        out = mod.install_view(text.encode()).decode()
        self.assertNotIn('x-data="basKtpCapture()"', out)
        self.assertIn('Upload Audio', out)
        self.assertIn('Rekaman Sidang', out)
        self.assertEqual(out.count('<livewire:basai.ktp-camera'), 1)

    def test_unknown_shape_aborts_without_modifying_original(self):
        with self.assertRaises(RuntimeError):
            mod.install_view(b'<div>Another dashboard structure</div>')

    def test_unknown_second_panel_aborts(self):
        html = '''                <div class="panel panel-default" x-data="basKtpCapture()"><span>Unknown</span></div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <div class="panel-title"><strong>Rekaman Sidang</strong></div>
                '''
        with self.assertRaises(RuntimeError):
            mod.install_view(html.encode())


if __name__ == '__main__':
    unittest.main()
