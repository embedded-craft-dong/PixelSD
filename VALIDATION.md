# Format reference and verification

**English** | [简体中文](VALIDATION.zh-CN.md) · [Back to README](README.md)

## Supported images and processing

PixelSD accepts JPG, PNG, BMP, WebP and TIFF images supported by Pillow. Animated inputs use the first frame. EXIF orientation is applied before clockwise rotation, mirroring and resizing. Transparent pixels are composited onto the selected background.

Output dimensions are 1–2047 pixels per axis. Color output is 16-bit RGB565 or BGR565. The current conversion pipeline does not apply ICC color management or dithering. Preview rendering is scaled to the window; large images may take longer to process.

## Binary containers

| Container | Header | Total size |
| --- | --- | --- |
| BIN | Little-endian `uint32`: `4 \| (width << 10) \| (height << 21)` | `width × height × 2 + 4` bytes |
| R56 | ASCII `R565`, little-endian `uint16` width, `uint16` height, then a zero `uint32` | `width × height × 2 + 12` bytes |

Pixel data follows the header in row order. Header byte order is always little-endian; the pixel byte order is configurable. At the default 240 × 320 resolution, BIN is 153,604 bytes and R56 is 153,612 bytes.

The BIN layout uses the [LVGL 8 TRUE_COLOR header](https://github.com/lvgl/lvgl/blob/v8.3.11/src/draw/lv_img_buf.h) with 16-bit pixels. The device's color depth and driver settings must match. The inspector supports these specific layouts, rather than arbitrary files with a `.bin` extension. RGB/BGR order and pixel byte order must be selected when reading a file; they are not identified by these headers.

## C arrays

- `uint16_t`: RGB565 red is `0xF800`. Values are independent of the export byte-order setting; their in-memory representation follows the target CPU.
- `uint8_t`: the same red pixel is `0x00, 0xF8` in little-endian output and `0xF8, 0x00` in big-endian output.
- **Header only:** emits a `static const` array. Including it in multiple translation units may create multiple copies.
- **Header + source:** emits an `extern const` declaration and a single definition, with width/height macros and C++-compatible declarations.

Arrays contain pixels only. Platform-specific storage attributes such as `PROGMEM` can be added in the firmware project when required. Display transfer byte order should be configured in the driver.

## Batch indexes and storage estimates

The optional `INDEX_start_end.JSON` lists successful BIN outputs from the current operation. It requires binary output, RGB565 and little-endian pixels. It does not replace an existing `INDEX.JSON`. A retry index lists only the files successfully retried; firmware requirements determine how indexes should be combined.

Pixel storage is exactly `width × height × 2` bytes per image. Firmware usage also depends on linking, alignment and storage attributes. Disk estimates are approximate and exclude index files; C source text includes formatting and declarations.

## Verification

Version 0.3.0 passed 14 automated tests covering:

- Known pixel values, endianness, RGB/BGR round trips and custom dimensions.
- Container headers, exact lengths and rejection of malformed files.
- Rotation, mirroring, backgrounds and C output combinations.
- Existing-file protection, rollback, folder sorting, deduplication and retry settings.
- Language-switch state preservation, drag-and-drop payload handling and binary inspection.

Generated C files were compiled, linked across source files and executed using GCC. The C integration test is optional when GCC is unavailable. Source and packaged EXE startup were checked on the build machine.

These checks cover host-side conversion and application behavior. Device rendering depends on the target firmware and display driver; independent Windows machines and hardware configurations require their own verification.

## Windows distribution notes

Release binaries target Windows x64 and are currently unsigned. Run with normal user privileges: Windows can block drag-and-drop from a normal Explorer window into an elevated application. Third-party notices are included in [`licenses/`](licenses/).
