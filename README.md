# PixelSD

**English** | [简体中文](README.zh-CN.md)

An offline image workspace for embedded displays. Convert images to RGB565 binary files or C arrays, preview the result, and prepare numbered batches for your device.

[**Download for Windows**](https://github.com/embedded-craft-dong/PixelSD/releases/latest) · [Format reference & verification](VALIDATION.md)

## Features

- **Batch conversion:** add images or folders, drag and drop, sort filenames naturally, and choose an output number range.
- **Flexible display settings:** resolution presets and custom dimensions, RGB565 / BGR565, and little-endian / big-endian pixel data.
- **Image preparation:** fit, crop or stretch; rotate, mirror, and choose a background color.
- **Export options:** BIN / R56 files, `uint8_t` or `uint16_t` C arrays, and header-only or separate `.h` / `.c` files.
- **Preview and inspection:** compare the fitted image with decoded RGB565 output, or open a BIN / R56 file to inspect its dimensions and pixels.
- **Batch controls:** per-file results, storage estimates, and retries that retain the original numbering and settings.
- **Bilingual interface:** switch between English and Chinese without clearing your queue or settings.

## Quick start

1. Download **`PixelSD-0.3.0-windows-x64.zip`** from [Releases](https://github.com/embedded-craft-dong/PixelSD/releases/latest).
2. Extract the archive and double-click **`PixelSD.exe`**. Python is not required.
3. Add your images. In **Basic**, choose the dimensions, number range, and export format.
4. Select an output folder and click **Convert**.
5. Copy the generated files to your SD card, or add the C files to your firmware project.

The default configuration is **240 × 320, RGB565, little-endian**, with the full image fitted inside a black background. Choose settings that match your display firmware.

All image processing takes place locally. No account or image upload is needed.

## Working with batches

Folder imports include supported images in the selected folder. Natural sorting places `2.png` before `10.png`; you can also reorder files individually. The queue shows the expected output name before conversion.

Original images are preserved. If any output file for an image already exists, that image is skipped. **Retry failed** uses each failed image's original number, destination, and conversion settings. Completed and skipped items are left as they are.

The **Advanced** tab contains pixel byte order, color order, C array layout, rotation, mirroring, and background color. **Preview / Inspect** provides a side-by-side comparison and a binary-file viewer.

## Choosing an export format

| Format | Typical use |
| --- | --- |
| BIN + R56 | Loading image files from an SD card |
| C array | Embedding image data in firmware |
| Binary + C array | Generating both from the same image batch |

For projects with several source files, use **Header + source** to keep the array definition in one `.c` file. Add that file to your build and include its `.h` file where needed.

See the [technical reference](VALIDATION.md) for byte order, file headers, index files, and device compatibility.

## Run from source

Use Windows x64 and Python 3.14 with Tcl/Tk:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-build.txt
.venv/Scripts/python app.py
```

To test and package:

```powershell
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python build_release.py
.venv/Scripts/python package_release.py
```

The executable is written to `dist/`, and release archives to `release/`. Third-party license notices are included in [`licenses/`](licenses/).
