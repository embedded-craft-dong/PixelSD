"""Run from the project directory with build requirements installed."""
import subprocess
import sys
import importlib.metadata as metadata
from pathlib import Path
from PIL import Image, ImageDraw

def main():
    root=Path(__file__).resolve().parent
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,check=True)
    folder=root/'licenses';folder.mkdir(exist_ok=True)
    for relative in ['LICENSE.txt','tcl/tcl8.6/license.terms','tcl/tk8.6/license.terms','tcl/tcl8.6.16/license.terms','tcl/tk8.6.16/license.terms']:
        path=Path(sys.base_prefix)/relative
        if path.is_file():(folder/('python-'+relative.replace('/','-'))).write_bytes(path.read_bytes())
    icon=Image.new('RGBA',(256,256),'#0d141d');draw=ImageDraw.Draw(icon)
    draw.rounded_rectangle((40,24,216,232),radius=24,fill='#75e0c2')
    draw.rounded_rectangle((58,45,198,185),radius=10,fill='#17222e')
    draw.polygon([(65,170),(112,98),(143,137),(162,112),(194,170)],fill='#75e0c2')
    draw.ellipse((153,66,176,89),fill='#75e0c2')
    draw.rounded_rectangle((105,204,151,213),radius=4,fill='#17222e')
    icon.save(root/'icon.ico',sizes=[(16,16),(32,32),(48,48),(128,128),(256,256)])
    for name in ['customtkinter','pillow','darkdetect','packaging','pyinstaller','altgraph','pefile','pywin32-ctypes','setuptools','tkinterdnd2']:
        dist=metadata.distribution(name)
        for file in dist.files or []:
            if any(word in str(file).lower() for word in ['license','copying']) and str(file).lower().endswith(('.txt','.md','.rst','license','copying')):
                path=Path(dist.locate_file(file))
                if path.is_file():(folder/(name+'-'+path.name)).write_bytes(path.read_bytes())
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed','--name','PixelSD','--icon','icon.ico','--add-data','icon.ico;.','--collect-all','customtkinter','--collect-all','tkinterdnd2','app.py'],cwd=root,check=True)

if __name__=='__main__':main()
