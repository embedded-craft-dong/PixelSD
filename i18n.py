"""UI translations only; switching language never changes conversion state."""
import re

EN = {
 '常用设置':'Basic','高级设置':'Advanced','预览 / 检查':'Preview / Inspect',
 '添加文件夹':'Add folder','自然排序':'Natural sort','打开 BIN / R56':'Open BIN / R56',
 '拖入图片或文件夹\n也可点击添加图片 / Ctrl + O':'Drop images or folders here\nor use Add images / Ctrl + O',
 '预览内容':'Preview mode','适配后原图':'Fitted original','RGB565 还原':'Decoded RGB565','左右对比':'Side by side',
 '左右对比：左侧原图，右侧 RGB565 还原':'Side by side: original left, decoded 565 right',
 '读取字节顺序':'Reader byte order','读取颜色顺序':'Reader color order','返回图片预览':'Return to image preview',
 'C 数组元素类型':'C element type','C 文件布局':'C file layout',
 '单个头文件':'Header only','头文件 + 源文件':'Header + source',
 '顺时针旋转':'Clockwise rotation','镜像':'Mirror','无镜像':'None','水平镜像':'Horizontal','垂直镜像':'Vertical','水平 + 垂直':'Both axes',
 '选择留边颜色':'Choose background color','重试失败项':'Retry failed',
 '无法读取文件夹':'Cannot read folder','每张像素存储':'Pixel storage per image','预计输出总量（约）':'Approximate total output',
 '待转换':'Pending','完成':'Done','失败':'Failed','跳过':'Skipped','未处理':'Not processed',
 '同名文件已存在':'Output already exists','源文件或输出目录不存在':'Source or output folder not found',
 '无法读取或写入，请检查权限':'Cannot read or write; check permissions',
 '图片损坏或格式不受支持':'Image corrupt or format unsupported','磁盘空间不足':'Disk is full','文件读取或写入失败':'File read or write failed',
 '请输入有效序号':'Enter valid whole-number indices',
 '索引需要二进制输出、RGB565 和小端像素':'Index requires binary output, RGB565 and little-endian pixels',
 '让图片，点亮屏幕。':'Bring your images to the screen.',
 '离线批量转换':'Offline batch conversion',
 '01  图片队列':'01  IMAGE QUEUE', '02  预览与设置':'02  PREVIEW & SETTINGS',
 '添加图片':'Add images', '清空':'Clear', '准备好下一组画面':'Ready for your next frame',
 '点击右上角「添加图片」\n或按 Ctrl + O 批量选择':'Choose Add images above\nor press Ctrl + O to select files',
 '点击文件预览  ·  ↑ ↓ 调整顺序  ·  × 移除':'Click to preview  ·  ↑ ↓ Reorder  ·  × Remove',
 '尚未添加图片 · 支持 JPG / PNG / BMP / WebP':'No images yet · JPG / PNG / BMP / WebP',
 '添加图片后显示预览':'Add an image to preview', '无法预览此文件':'Preview unavailable',
 '屏幕尺寸 · 默认 240 × 320':'Display size · default 240 × 320', '240 × 320（默认）':'240 × 320 (default)',
 '自定义':'Custom', '宽度 / px':'Width / px','高度 / px':'Height / px',
 '起始序号':'Start number','结束序号':'End number',
 '画面适配':'Image fit', '完整显示 · 黑色留边':'Contain · black borders',
 '铺满画面 · 居中裁剪':'Cover · center crop', '拉伸到屏幕':'Stretch to display',
 '像素字节顺序':'Pixel byte order','低字节在前 · 样本默认':'Little-endian · default','高字节在前':'Big-endian',
 '颜色顺序':'Color order','恢复默认显示参数':'Reset display defaults',
 '导出类型':'Export format','BIN + R56（默认）':'BIN + R56 (default)',
 'C 数组（.h）':'C array (.h)','二进制 + C 数组':'Binary + C array',
 '生成本批次索引（不含原图名称）':'Batch index (no source filenames)',
 '选择输出目录':'Choose output folder','打开目录':'Open folder',
 '请选择文件夹（建议使用空文件夹）':'Choose a folder (an empty one is recommended)',
 '就绪 · 原图保留，同名文件自动跳过':'Ready · Originals preserved; existing files skipped',
 '开始转换  →':'Convert  →','停止':'Stop','选择图片':'Select images','图片':'Images','所有文件':'All files',
 '选择输出文件夹':'Select output folder','检查设置':'Check settings',
 '请先添加图片。':'Please add images first.','请选择输出目录。':'Please select an output folder.',
 '请输入有效尺寸（1–2047 px）  ·  离线批量转换':'Enter valid dimensions (1–2047 px) · Offline conversion',
 '宽度和高度必须是 1–2047 之间的整数。':'Width and height must be integers between 1 and 2047.',
 '序号必须在 1–9999 之间，结束序号不能小于起始序号。':'Numbers must be between 1 and 9999; the end must not precede the start.',
 '索引格式':'Index format','生成 LVGL8 索引时请使用 RGB565、低字节在前。':'Use RGB565 and little-endian pixels when generating an LVGL8 index.',
 'C 数组模式不生成二进制索引。请取消索引选项，或选择同时导出二进制文件。':'C-only output does not generate a binary index. Uncheck the index option or choose Binary + C array.',
 '已停止':'Stopped','转换完成':'Conversion complete','正在停止':'Stopping',
 '请等待当前图片处理完成后再关闭。':'Please wait for the current image to finish before closing.',
}

PATTERNS = [
 (r'完成 (\d+) · 失败 (\d+) · 跳过 (\d+)',r'Done \1 · Failed \2 · Skipped \3'),
 (r'已停止 · 完成 (\d+) · 失败 (\d+) · 跳过 (\d+)',r'Stopped · Done \1 · Failed \2 · Skipped \3'),
 (r'索引未生成：(.+)',r'Index not generated: \1'),
 (r'转换失败：(.+)',r'Conversion failed: \1'),
 (r'已添加 (\d+) 张图片 · 每张输出 (.+)',r'\1 images · Output: \2'),
 (r'已选择 (\d+) 张图片，序号范围需要 (\d+) 张。',r'\1 images selected; the number range requires \2.'),
 (r'正在处理 (\d+) / (\d+) · 成功 (\d+)',r'Processing \1 / \2 · Converted \3'),
 (r'(已停止|转换完成) · 成功 (\d+) 张 · 提示 (\d+) 项',None),
 (r'成功生成 (\d+) 组图片文件。',r'Created \1 sets of output files.'),
 (r'(IMG\d+)：同名文件已存在，跳过',r'\1: output already exists; skipped'),
 (r'(IMG\d+)：转换失败（(.+)）',r'\1: conversion failed (\2)'),
 (r'索引未生成（(.+)）',r'Index was not generated (\1)'),
]

def translate(text, language):
    if language=='中文':return text
    if text in EN:return EN[text]
    for pattern,replacement in PATTERNS:
        match=re.fullmatch(pattern,text)
        if match:
            if replacement is None:return f'{EN[match[1]]} · Converted {match[2]} · Notices {match[3]}'
            return match.expand(replacement)
    if '\n' in text:return '\n'.join(translate(line,language) for line in text.split('\n'))
    return text.replace('离线批量转换','Offline batch conversion')

def canonical(text):
    return next((zh for zh,en in EN.items() if text==en),text)
