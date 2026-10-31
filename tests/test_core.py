import struct
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from core import encode, containers, prepare, validate_range, write_pair, write_index, validate_size, c_array, write_outputs
import json

class ConversionTests(unittest.TestCase):
    def test_c_array(self):
        image=Image.new('RGB',(3,1));image.putdata([(255,0,0),(0,255,0),(0,0,255)])
        a=c_array(12,encode(image),(3,1)).decode('ascii')
        self.assertIn('0xF800, 0x07E0, 0x001F',a)
        self.assertIn('static const uint16_t IMG0012[3]',a)
        self.assertIn('#define IMG0012_WIDTH 3',a)
        self.assertEqual(a,c_array(12,encode(image,'big'),(3,1),'big').decode('ascii'))
        with tempfile.TemporaryDirectory() as d:
            write_outputs(d,1,encode(image),(3,1),'c')
            self.assertEqual([p.suffix for p in Path(d).iterdir()],['.h'])
            write_outputs(d,2,encode(image),(3,1),'both')
            self.assertTrue(all((Path(d)/('IMG0002'+ext)).exists() for ext in ['.bin','.r56','.h']))
            # If the last file conflicts, the newly created first two roll back.
            (Path(d)/'IMG0003.h').write_bytes(b'original')
            with self.assertRaises(FileExistsError):write_outputs(d,3,encode(image),(3,1),'both')
            self.assertFalse((Path(d)/'IMG0003.bin').exists())
            self.assertEqual((Path(d)/'IMG0003.h').read_bytes(),b'original')
    def test_custom_dimensions(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'synthetic.png';Image.new('RGB',(100,100),'red').save(p)
            for size in [(320,240),(240,240),(480,320),(13,29),(1,1),(2047,1)]:
                for fit in ['contain','cover','stretch']:
                    im=prepare(p,fit,size);self.assertEqual(im.size,size)
                pixels=encode(im);a,b=containers(pixels,size)
                header=int.from_bytes(a[:4],'little')
                self.assertEqual((header>>10)&2047,size[0]);self.assertEqual(header>>21,size[1])
                self.assertEqual(header&1023,4)
                self.assertEqual(struct.unpack('<HH',b[4:8]),size)
                self.assertEqual(len(a),size[0]*size[1]*2+4)
                self.assertEqual(len(b),size[0]*size[1]*2+12)
            size=(480,320)
            write_pair(d,1,encode(prepare(p,size=size)),size)
            write_index(d,[1],'contain',size)
            index=json.loads((Path(d)/'INDEX_0001_0001.JSON').read_text())
            self.assertEqual((index['width'],index['height']),size)
            self.assertEqual(index['images'][0]['bytes'],(Path(d)/'IMG0001.bin').stat().st_size)
        for size in [(0,1),(1,-2),(2048,1),(1,2048),(1.5,2)]:
            with self.assertRaises(ValueError):validate_size(size)
        with self.assertRaises(ValueError):containers(b'\0'*8,(3,3))
    def test_known_colors(self):
        for color, expected in [('red',b'\x00\xf8'),('lime',b'\xe0\x07'),('blue',b'\x1f\x00')]:
            im=Image.new('RGB',(240,320),color)
            p=encode(im)
            self.assertEqual(p,expected*76800)
            a,b=containers(p)
            self.assertEqual(len(a),153604);self.assertEqual(len(b),153612)
            self.assertEqual(a[:4],bytes.fromhex('04 c0 03 28'))
            self.assertEqual(b[:12],b'R565'+struct.pack('<HHI',240,320,0))
            self.assertEqual(a[4:],b[12:])
        self.assertEqual(encode(Image.new('RGB',(1,1),'red'),'big'),b'\xf8\x00')
        self.assertEqual(encode(Image.new('RGB',(1,1),'red'),color='BGR'),b'\x1f\x00')
    def test_range(self):
        validate_range(12,21,10)
        for args in [(0,2,3),(1,3,2),(3,1,3),(9999,10000,2)]:
            with self.assertRaises(ValueError):validate_range(*args)
    def test_fit_and_transparency(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'synthetic.png';Image.new('RGBA',(100,100),(255,0,0,255)).save(p)
            im=prepare(p);self.assertEqual(im.getpixel((0,0)),(0,0,0));self.assertEqual(im.getpixel((120,160)),(255,0,0))
            for mode in ['cover','stretch']:self.assertEqual(prepare(p,mode).getpixel((0,0)),(255,0,0))
            Image.new('RGBA',(100,100),(255,0,0,0)).save(p)
            self.assertEqual(prepare(p).getpixel((120,160)),(0,0,0))
    def test_no_overwrite_and_rollback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'IMG0001.r56';p.write_bytes(b'existing')
            with self.assertRaises(FileExistsError):write_pair(d,1,b'\0'*153600)
            self.assertEqual(p.read_bytes(),b'existing');self.assertFalse((Path(d)/'IMG0001.bin').exists())
            write_pair(d,2,b'\0'*153600);write_index(d,[2],'contain')
            self.assertNotIn('source',(Path(d)/'INDEX_0002_0002.JSON').read_text())
            with self.assertRaises(FileExistsError):write_index(d,[2],'contain')

if __name__=='__main__':unittest.main()
