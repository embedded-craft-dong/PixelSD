# PixelSD

[English](README.md) | **简体中文**

面向嵌入式显示屏的离线图片工作台。将图片转换为 RGB565 二进制文件或 C 数组，预览转换效果，并按设备需要批量编号。

[**下载 Windows 版**](https://github.com/embedded-craft-dong/PixelSD/releases/latest) · [格式说明与验证](VALIDATION.zh-CN.md)

## 功能

- **批量转换：**添加图片或文件夹、拖放导入、自然排序、自定义输出编号范围。
- **显示参数：**分辨率预设与自定义宽高、RGB565 / BGR565、像素大小端设置。
- **画面处理：**完整显示、裁剪或拉伸，支持旋转、镜像和背景颜色。
- **灵活导出：**BIN / R56、`uint8_t` 或 `uint16_t` C 数组，支持单头文件或 `.h` / `.c` 分离。
- **预览与检查：**对比适配后的原图和 RGB565 还原效果，打开 BIN / R56 查看尺寸与像素。
- **批次管理：**逐项结果、存储量估算，以及保留原编号和参数的失败重试。
- **双语界面：**中英文即时切换，保留已选图片和参数。

## 快速开始

1. 在 [Releases](https://github.com/embedded-craft-dong/PixelSD/releases/latest) 下载 **`PixelSD-0.3.0-windows-x64.zip`**。
2. 解压并双击 **`PixelSD.exe`**，无需安装 Python。
3. 添加图片，在“常用设置”中选择尺寸、编号范围和导出类型。
4. 选择输出文件夹，点击“开始转换”。
5. 将生成的文件复制到 SD 卡，或将 C 文件加入固件工程。

默认配置为 **240 × 320、RGB565、小端像素**，完整显示图片并使用黑色背景。请根据显示屏固件选择对应参数。

图片处理全部在本机完成，无需账号或上传图片。

## 批量处理

导入文件夹时读取当前目录下支持的图片。“自然排序”会把 `2.png` 放在 `10.png` 前面，也可以逐项调整顺序。队列会提前显示对应的输出文件名。

原图保持不变。同一图片的任一输出文件已存在时，整组跳过。“重试失败项”沿用该图片原来的编号、输出目录和转换参数，已完成及已跳过的项目不受影响。

“高级设置”提供像素端序、颜色顺序、C 数组布局、旋转、镜像和背景颜色；“预览 / 检查”提供左右对比和二进制图片查看器。

## 如何选择导出格式

| 格式 | 典型用途 |
| --- | --- |
| BIN + R56 | 从 SD 卡读取图片 |
| C 数组 | 将图片数据嵌入固件 |
| 二进制 + C 数组 | 同一批图片同时生成两类结果 |

多个源文件需要引用图片时，建议选择“头文件 + 源文件”，将数组定义保留在一个 `.c` 文件中。把它加入工程编译，在需要的位置包含对应 `.h` 文件即可。

像素端序、文件头、索引与设备兼容性详见[技术说明](VALIDATION.zh-CN.md)。

## 从源码运行

使用 Windows x64 和带 Tcl/Tk 的 Python 3.14：

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-build.txt
.venv/Scripts/python app.py
```

测试与打包：

```powershell
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python build_release.py
.venv/Scripts/python package_release.py
```

可执行文件生成在 `dist/`，发行包生成在 `release/`。第三方许可声明位于 [`licenses/`](licenses/)。
