import tempfile
import unittest
from pathlib import Path
from app import App
from PIL import Image

class UIStateTests(unittest.TestCase):
    def test_language_keeps_state(self):
        app=App();app.withdraw()
        try:
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'synthetic.png';Image.new('RGB',(8,8),'red').save(p)
                app.files=[str(p)];app.start.set('12');app.end.set('12')
                app.image_width.set('128');app.image_height.set('64')
                app.output=d;app.index.select();app.refresh()
                app.export.set('二进制 + C 数组')
                app.rotation.set('90°');app.mirror.set('水平镜像');app.layout.set('头文件 + 源文件')
                config_before=app.config()
                before=(list(app.files),app.start.get(),app.end.get(),app.output,app.output_size(),app.index.get(),app.export_mode(),app.fit_value())
                for language in ['English','中文','English']:
                    app.switch_language(language);app.update_idletasks()
                    after=(list(app.files),app.start.get(),app.end.get(),app.output,app.output_size(),app.index.get(),app.export_mode(),app.fit_value())
                    self.assertEqual(before,after)
                    self.assertEqual(config_before,app.config())
                app.worker(app.files,12,d,app.fit_value(),'little','RGB',True,app.output_size(),app.export_mode())
                self.assertEqual((Path(d)/'IMG0012.bin').stat().st_size,128*64*2+4)
                self.assertTrue((Path(d)/'IMG0012.h').exists())
                app.apply_preset('320 × 240');self.assertEqual(app.output_size(),(320,240))
                app.reset_display();self.assertEqual(app.output_size(),(240,320))
                self.assertEqual(app.fit_value(),'contain');self.assertEqual(app.color.get(),'RGB565')
        finally:app.destroy()

    def test_drop_payload_and_reader(self):
        from types import SimpleNamespace
        app=App();app.withdraw()
        try:
            self.assertTrue(app.TkdndVersion)
            with tempfile.TemporaryDirectory(prefix='pixel sd ') as d:
                p=Path(d)/'test image.png';Image.new('RGB',(2,2),'red').save(p)
                event=SimpleNamespace(data='{'+str(p)+'}')
                self.assertEqual(app.on_drop(event),'copy');self.assertEqual(len(app.files),1)
                app.on_drop(event);self.assertEqual(len(app.files),1)
                app.busy=True;self.assertEqual(app.on_drop(event),'refuse_drop');app.busy=False
                from core import write_pair
                write_pair(d,1,b'\x00\xf8'*4,(2,2))
                app.inspect_file(Path(d)/'IMG0001.r56')
                self.assertEqual(app.current_page,'preview')
                self.assertIn('2 × 2',app.preview_info.cget('text'))
                app.switch_language('English');self.assertIsNotNone(app.inspector_path)
        finally:app.destroy()
