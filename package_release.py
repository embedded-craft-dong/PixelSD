"""Package only allowlisted public project files; never archive the workspace."""
import hashlib
import zipfile
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent
    release=root/'release';release.mkdir(exist_ok=True)
    source=['app.py','core.py','i18n.py','jobs.py','build_release.py','package_release.py','requirements.txt','requirements-build.txt','README.md','VALIDATION.md','.gitignore','.github/workflows/build.yml','tests/test_core.py','tests/test_ui.py','tests/test_extended.py','icon.ico']
    licenses=[p.relative_to(root).as_posix() for p in (root/'licenses').glob('*') if p.is_file()]
    for name,files in [('PixelSD-0.3.0-source.zip',source+licenses),('PixelSD-0.3.0-windows-x64.zip',['dist/PixelSD.exe','README.md','VALIDATION.md']+licenses)]:
        with zipfile.ZipFile(release/name,'w',zipfile.ZIP_DEFLATED) as z:
            for relative in files:
                target='PixelSD.exe' if relative=='dist/PixelSD.exe' else relative
                z.write(root/relative,'PixelSD/'+target)
    sums=[]
    for path in sorted(release.glob('PixelSD-0.3.0-*.zip')):sums.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name)
    (release/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='ascii')

if __name__=='__main__':main()
