import tempfile
import threading
import unittest
import shutil
import subprocess
from pathlib import Path
from PIL import Image
from core import prepare,encode,decode,read_binary,containers,c_files,collect_images,natural_key,write_outputs
from jobs import Config,Job,run_jobs,retry_jobs

class ExtendedTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('gcc'),'GCC is optional for C integration test')
    def test_generated_c_compiles_and_links(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for ctype in ('uint8_t','uint16_t'):
                for layout in ('header','split'):
                    generated=c_files(1,b'\x00\xf8',(1,1),ctype=ctype,layout=layout)
                    for ext,data in generated.items():(p/('IMG0001'+ext)).write_bytes(data)
                    (p/'other.c').write_text('#include "IMG0001.h"\nint other(void){return IMG0001_WIDTH;}\n',encoding='ascii')
                    expected='0' if ctype=='uint8_t' else '0xF800'
                    (p/'main.c').write_text('#include "IMG0001.h"\nint other(void);\nint main(void){return !(other()==1 && IMG0001[0]=='+expected+');}\n',encoding='ascii')
                    args=['gcc','-std=c99','-Wall','-Werror','main.c','other.c']
                    if layout=='split':args+=['IMG0001.c']
                    subprocess.run(args+['-o','check.exe'],cwd=p,check=True,capture_output=True)
                    subprocess.run([str(p/'check.exe')],check=True,capture_output=True)
    def test_roundtrip_and_reject_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            image=Image.new('RGB',(3,2));image.putdata([(255,0,0),(0,255,0),(0,0,255),(123,201,77),(0,0,0),(255,255,255)])
            for endian in ('little','big'):
                for color in ('RGB','BGR'):
                    pixels=encode(image,endian,color)
                    decoded=decode(pixels,image.size,endian,color)
                    self.assertEqual(encode(decoded,endian,color),pixels)
                    for ext,data in zip(('.bin','.r56'),containers(pixels,image.size)):
                        p=Path(d)/('sample'+ext);p.write_bytes(data)
                        restored,meta=read_binary(p,endian,color)
                        self.assertEqual(restored.tobytes(),decoded.tobytes());self.assertEqual(meta['width'],3)
                        p.write_bytes(data[:-1])
                        with self.assertRaises(ValueError):read_binary(p)
            p=Path(d)/'bad.bin';p.write_bytes(b'\0'*16)
            with self.assertRaises(ValueError):read_binary(p)
            p=Path(d)/'bad.r56';p.write_bytes(b'R565'+b'\0'*8)
            with self.assertRaises(ValueError):read_binary(p)
    def test_rotation_mirror_background(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'sample.png'
            im=Image.new('RGB',(2,1));im.putdata([(255,0,0),(0,0,255)]);im.save(p)
            self.assertEqual(list(prepare(p,'stretch',(1,2),90).get_flattened_data()),[(255,0,0),(0,0,255)])
            self.assertEqual(prepare(p,'stretch',(2,1),mirror='horizontal').getpixel((0,0)),(0,0,255))
            Image.new('RGBA',(2,2),(0,0,0,0)).save(p)
            self.assertEqual(prepare(p,size=(4,6),background='#ffffff').getpixel((0,0)),(255,255,255))
    def test_c_bytes_split_and_overwrite(self):
        pixels=b'\x00\xf8\xe0\x07'
        h=c_files(1,pixels,(2,1),ctype='uint8_t')['.h'].decode()
        self.assertIn('0x00, 0xF8, 0xE0, 0x07',h)
        for ctype in ('uint8_t','uint16_t'):
            data=c_files(7,pixels,(2,1),ctype=ctype,layout='split')
            self.assertIn(b'extern const',data['.h']);self.assertNotIn(b' = {',data['.h'])
            self.assertIn(b'#include "IMG0007.h"',data['.c'])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'IMG0001.c';p.write_bytes(b'existing')
            with self.assertRaises(FileExistsError):write_outputs(d,1,pixels,(2,1),'both',layout='split')
            self.assertEqual(list(Path(d).iterdir()),[p]);self.assertEqual(p.read_bytes(),b'existing')
    def test_folder_sort_dedupe_nonrecursive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for n in ['10.png','2.png','1.png']:(p/n).touch()
            (p/'sub').mkdir();(p/'sub'/'3.png').touch();(p/'ignore.txt').touch()
            files=collect_images([p,p/'2.png'])
            self.assertEqual([Path(f).name for f in files],['1.png','2.png','10.png'])
    def test_retry_preserves_number_and_config(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);good=p/'good.png';bad=p/'bad.png';existing=p/'existing.png'
            Image.new('RGB',(2,2),'red').save(good);bad.write_bytes(b'bad');Image.new('RGB',(2,2),'blue').save(existing)
            (p/'IMG0014.h').write_bytes(b'keep')
            config=Config(size=(2,2),mode='c',ctype='uint8_t',layout='split')
            jobs=[Job(str(file),12+i,d,config) for i,file in enumerate([good,bad,existing])]
            cancel=threading.Event();results=run_jobs(jobs,cancel)
            self.assertEqual([r.status for r in results],['done','failed','skipped'])
            pending=retry_jobs(results);self.assertEqual([j.number for j in pending],[13]);self.assertEqual(pending[0].config,config)
            Image.new('RGB',(2,2),'green').save(bad)
            self.assertEqual(run_jobs(pending,cancel)[0].status,'done')
            self.assertTrue((p/'IMG0013.c').exists());self.assertEqual((p/'IMG0014.h').read_bytes(),b'keep')
            cancel.set();self.assertEqual(run_jobs([Job(str(good),25,d,config)],cancel)[0].status,'cancelled')
            self.assertFalse((p/'IMG0025.h').exists())
