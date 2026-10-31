"""PixelSD desktop entry point."""
import os
import sys
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, colorchooser
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image
from jobs import Config, Job, run_jobs, retry_jobs
import customtkinter as ctk
from core import prepare, encode, write_outputs, output_extensions, write_index, validate_range, validate_size, decode, read_binary, collect_images, natural_key
from i18n import translate, canonical

BG, PANEL, FIELD, ACCENT = '#0d141d', '#17222e', '#101a25', '#75e0c2'
MUTED = '#96a9b9'
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.title('PixelSD 0.3.0 · 单片机图片工作台')
        icon=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'icon.ico'
        if icon.exists():self.after(250,lambda:self.iconbitmap(str(icon)))
        scale=self._get_window_scaling()
        width=min(1100,int(self.winfo_screenwidth()/scale)-60)
        height=min(790,int(self.winfo_screenheight()/scale)-100)
        self.geometry(f'{max(900,width)}x{max(620,height)}+20+20')
        self.minsize(900, 620)
        self.configure(fg_color=BG)
        self.files, self.rows, self.busy = [], [], False
        self.events, self.cancel = queue.Queue(), threading.Event()
        self.output = ''
        self.controls = []
        self.results={}
        self.retry_snapshot=[]
        self.inspector_path=None
        self.background='#000000'
        self.current_page='common'
        self.language='中文'
        self.translatable=[]
        self.option_widgets=[]
        self.status_text='就绪 · 原图保留，同名文件自动跳过'
        self.preview_index = 0
        self.preview_job = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.grid(row=0, column=0, sticky='ew', padx=28, pady=(14,10))
        language=ctk.CTkOptionMenu(header,values=['中文','English'],width=110,fg_color=PANEL,command=self.switch_language)
        language.pack(side='right',anchor='n')
        self.label(header, 'PIXELSD   /   IMAGE STUDIO', 12, ACCENT).pack(anchor='w')
        self.label(header, '让图片，点亮屏幕。', 28).pack(anchor='w', pady=(6,2))
        self.summary = self.label(header, '240 × 320  ·  RGB565  ·  离线批量转换', 13, MUTED)
        self.summary.pack(anchor='w')
        body = ctk.CTkFrame(self, fg_color='transparent')
        body.grid(row=1, column=0, sticky='nsew', padx=28)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=16)
        left.grid(row=0,column=0,sticky='nsew',padx=(0,16))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)
        bar = ctk.CTkFrame(left, fg_color='transparent')
        bar.grid(row=0,column=0,sticky='ew',padx=18,pady=16)
        self.label(bar,'01  图片队列',18).pack(side='left')
        self.button(bar,'添加图片',self.add,width=95).pack(side='right')
        self.button(bar,'清空',self.clear,width=60).pack(side='right',padx=8)
        self.count = self.label(left,'尚未添加图片 · 支持 JPG / PNG / BMP / WebP',12,MUTED)
        self.count.grid(row=1,column=0,sticky='w',padx=18)
        self.listbox = ctk.CTkScrollableFrame(left,fg_color=PANEL)
        self.listbox.grid(row=2,column=0,sticky='nsew',padx=10,pady=12)
        tools=ctk.CTkFrame(left,fg_color='transparent');tools.grid(row=3,column=0,sticky='ew',padx=12,pady=8)
        self.button(tools,'添加文件夹',self.add_folder,width=115).pack(side='left',padx=3)
        self.button(tools,'自然排序',self.sort_files,width=100).pack(side='left',padx=3)
        self.button(tools,'打开 BIN / R56',self.inspect_file,width=130).pack(side='right',padx=3)
        right = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=16)
        right.grid(row=0,column=1,sticky='nsew')
        right.grid_columnconfigure(0,weight=1);right.grid_rowconfigure(1,weight=1)
        tabs=ctk.CTkFrame(right,fg_color='transparent');tabs.grid(row=0,column=0,sticky='ew',padx=10,pady=10)
        self.pages={};self.tab_buttons={}
        for key,title in [('common','常用设置'),('advanced','高级设置'),('preview','预览 / 检查')]:
            btn=ctk.CTkButton(tabs,text=self.tr(title),width=100,fg_color='#263747',command=lambda key=key:self.show_page(key))
            btn.pack(side='left',expand=True,fill='x',padx=2);self.translatable.append((btn,title))
            self.tab_buttons[key]=btn
            self.pages[key]=ctk.CTkScrollableFrame(right,fg_color=PANEL)
        common=self.pages['common'];advanced=self.pages['advanced'];preview_page=self.pages['preview']
        self.show_page('common')
        self.preset=self.option(common,None,['240 × 320（默认）','320 × 240','240 × 240','320 × 480','480 × 320','800 × 480','自定义'])
        self.preset.configure(command=self.apply_preset)
        dims=ctk.CTkFrame(common,fg_color='transparent');dims.pack(fill='x',padx=12,pady=6)
        self.image_width=ctk.StringVar(value='240');self.image_height=ctk.StringVar(value='320')
        for text,var in [('宽度 / px',self.image_width),('高度 / px',self.image_height)]:
            box=ctk.CTkFrame(dims,fg_color='transparent');box.pack(side='left',expand=True,fill='x',padx=4)
            self.label(box,text,12,MUTED).pack(anchor='w')
            ent=ctk.CTkEntry(box,textvariable=var,width=100);ent.pack(fill='x',pady=4);self.controls.append(ent)
        self.preview_mode=self.option(preview_page,None,['适配后原图','RGB565 还原','左右对比'])
        self.preview_mode.configure(command=lambda _:self.show_preview())
        self.preview_mode.set(self.tr('左右对比'))
        self.preview = ctk.CTkLabel(preview_page,text=self.tr('添加图片后显示预览'),width=100,height=180,fg_color=FIELD,corner_radius=12,text_color=MUTED)
        self.preview.pack(fill='x',padx=10,pady=10)
        self.preview_info=self.label(preview_page,'',12,MUTED);self.preview_info.pack(fill='x',padx=10)
        self.label(preview_page,'左右对比：左侧原图，右侧 RGB565 还原',12,MUTED).pack(pady=6)
        self.inspector_order=self.option(preview_page,'读取字节顺序',['低字节在前 · 样本默认','高字节在前'])
        self.inspector_color=self.option(preview_page,'读取颜色顺序',['RGB565','BGR565'])
        self.button(preview_page,'返回图片预览',self.leave_inspector).pack(pady=10)
        nums = ctk.CTkFrame(common,fg_color='transparent')
        nums.pack(fill='x',padx=12,pady=8)
        self.start=ctk.StringVar(value='1'); self.end=ctk.StringVar(value='1')
        for text,var in [('起始序号',self.start),('结束序号',self.end)]:
            box=ctk.CTkFrame(nums,fg_color='transparent');box.pack(side='left',expand=True,fill='x',padx=4)
            self.label(box,text,12,MUTED).pack(anchor='w')
            ent=ctk.CTkEntry(box,textvariable=var,width=100);ent.pack(fill='x',pady=5);self.controls.append(ent)
        self.start.trace_add('write',lambda *_:(self.update_end(),self.refresh()))
        self.order=self.option(advanced,'像素字节顺序',['低字节在前 · 样本默认','高字节在前'])
        self.color=self.option(advanced,'颜色顺序',['RGB565','BGR565'])
        self.color.configure(command=lambda _:self.settings_changed())
        self.export=self.option(common,'导出类型',['BIN + R56（默认）','C 数组（.h）','二进制 + C 数组'])
        self.export.configure(command=lambda _:(self.refresh(),self.update_estimate()))
        self.fit=self.option(common,'画面适配',['完整显示 · 黑色留边','铺满画面 · 居中裁剪','拉伸到屏幕'])
        self.button(advanced,'恢复默认显示参数',self.reset_display).pack(fill='x',padx=16,pady=(14,4))
        self.ctype=self.option(advanced,'C 数组元素类型',['uint16_t','uint8_t'])
        self.layout=self.option(advanced,'C 文件布局',['单个头文件','头文件 + 源文件'])
        self.ctype.configure(command=lambda _:self.update_estimate())
        self.layout.configure(command=lambda _:(self.refresh(),self.update_estimate()))
        self.rotation=self.option(advanced,'顺时针旋转',['0°','90°','180°','270°'])
        self.mirror=self.option(advanced,'镜像',['无镜像','水平镜像','垂直镜像','水平 + 垂直'])
        self.bg_button=self.button(advanced,'选择留边颜色',self.choose_background)
        self.bg_button.pack(fill='x',padx=16,pady=12)
        self.bg_value=self.label(advanced,self.background,12,MUTED);self.bg_value.pack()
        self.image_width.trace_add('write',lambda *_:self.settings_changed())
        self.image_height.trace_add('write',lambda *_:self.settings_changed())
        self.index=ctk.CTkCheckBox(common,text='生成本批次索引（不含原图名称）',font=('Microsoft YaHei UI',12),fg_color=ACCENT,text_color='#edf5f7')
        self.index.pack(anchor='w',padx=16,pady=16);self.controls.append(self.index)
        self.translatable.append((self.index,'生成本批次索引（不含原图名称）'))
        footer=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=16)
        footer.grid(row=2,column=0,sticky='ew',padx=28,pady=20)
        dest=ctk.CTkFrame(footer,fg_color='transparent');dest.pack(fill='x',padx=18,pady=(14,4))
        self.button(dest,'选择输出目录',self.choose,width=130).pack(side='left')
        self.destination=self.label(dest,'请选择文件夹（建议使用空文件夹）',12,MUTED);self.destination.pack(side='left',padx=12)
        self.button(dest,'打开目录',self.open_folder,width=90).pack(side='right')
        self.progress=ctk.CTkProgressBar(footer,progress_color=ACCENT);self.progress.pack(fill='x',padx=18,pady=10);self.progress.set(0)
        actions=ctk.CTkFrame(footer,fg_color='transparent');actions.pack(fill='x',padx=18,pady=(0,16))
        self.status=self.label(actions,'就绪 · 原图保留，同名文件自动跳过',12,MUTED);self.status.configure(wraplength=440,anchor='w');self.status.pack(side='left')
        self.go=ctk.CTkButton(actions,text='开始转换  →',width=150,height=40,fg_color=ACCENT,hover_color='#99ecd4',text_color='#102923',command=self.run);self.go.pack(side='right')
        self.stop=ctk.CTkButton(actions,text='停止',width=65,fg_color='#263747',command=self.cancel.set,state='disabled');self.stop.pack(side='right',padx=10)
        self.translatable.extend([(self.go,'开始转换  →'),(self.stop,'停止')])
        self.retry=ctk.CTkButton(actions,text=self.tr('重试失败项'),width=105,fg_color='#263747',command=self.retry_failed,state='disabled')
        self.retry.pack(side='right',padx=6);self.translatable.append((self.retry,'重试失败项'))
        self.estimate=self.label(common,'',12,MUTED);self.estimate.configure(wraplength=330);self.estimate.pack(fill='x',padx=16,pady=10)
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.bind('<Control-o>',lambda e:self.add())
        self.refresh();self.update_estimate()
        self.TkdndVersion=TkinterDnD._require(self)
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>',self.on_drop)
        self.after(100,self.poll)

    def label(self,parent,text,size=14,color='#edf5f7'):
        w=ctk.CTkLabel(parent,text=self.tr(text),text_color=color,font=('Microsoft YaHei UI',size))
        self.translatable.append((w,text));return w
    def button(self,parent,text,command,**kw):
        b=ctk.CTkButton(parent,text=self.tr(text),command=command,fg_color='#263747',hover_color='#345064',**kw);self.controls.append(b);self.translatable.append((b,text));return b
    def option(self,parent,title,values):
        if title:self.label(parent,title,12,MUTED).pack(anchor='w',padx=16,pady=(8,4))
        w=ctk.CTkOptionMenu(parent,values=[self.tr(v) for v in values],fg_color=FIELD,button_color='#263747',command=lambda _:self.show_preview())
        self.option_widgets.append((w,values))
        w.pack(fill='x',padx=16);self.controls.append(w);return w
    def add(self):
        if self.busy:return
        paths=filedialog.askopenfilenames(title=self.tr('选择图片'),filetypes=[(self.tr('图片'),'*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff'),(self.tr('所有文件'),'*.*')])
        self.add_paths(paths)
    def add_paths(self,paths):
        if self.busy:return
        try:
            incoming=collect_images(paths)
            known={str(Path(p).resolve()).casefold() for p in self.files}
            for p in incoming:
                if p.casefold() not in known:self.files.append(p);known.add(p.casefold())
        except OSError:self.notice('检查设置','无法读取文件夹',True);return
        self.refresh();self.update_end();self.show_preview();self.update_estimate();self.update_estimate()
    def on_drop(self,event):
        if self.busy:return 'refuse_drop'
        paths=self.tk.splitlist(event.data)
        binaries=[p for p in paths if Path(p).suffix.lower() in ('.bin','.r56')]
        self.add_paths(paths)
        if binaries:self.inspect_file(binaries[0])
        return 'copy'
    def add_folder(self):
        if self.busy:return
        path=filedialog.askdirectory(title=self.tr('添加文件夹'))
        if path:self.add_paths([path])
    def sort_files(self):
        if self.busy:return
        self.files.sort(key=natural_key);self.refresh()
    def show_page(self,key):
        self.current_page=key
        for page in self.pages.values():page.grid_forget()
        for name,button in self.tab_buttons.items():button.configure(fg_color=ACCENT if name==key else '#263747',text_color='#102923' if name==key else '#edf5f7')
        self.pages[key].grid(row=1,column=0,sticky='nsew',padx=6,pady=(0,6))
    def clear(self):
        if self.busy:return
        self.files=[];self.results={};self.retry_snapshot=[];self.retry.configure(state='disabled');self.refresh();self.update_end();self.show_preview();self.update_estimate();self.update_estimate()
    def update_end(self):
        try:self.end.set(str(int(self.start.get())+max(1,len(self.files))-1))
        except ValueError:pass
    def change(self,i,delta):
        if self.busy:return
        if delta==0:self.files.pop(i)
        elif 0<=i+delta<len(self.files):self.files[i],self.files[i+delta]=self.files[i+delta],self.files[i]
        self.refresh();self.update_end();self.show_preview();self.update_estimate()
    def refresh(self):
        for w in self.listbox.winfo_children():w.destroy()
        self.translatable=[(w,t) for w,t in self.translatable if w.winfo_exists()]
        self.rows=[]
        if not self.files:
            self.label(self.listbox,'准备好下一组画面',20).pack(pady=(20,8))
            self.label(self.listbox,'拖入图片或文件夹\n也可点击添加图片 / Ctrl + O',13,MUTED).pack(pady=8)
        try:start=int(self.start.get())
        except ValueError:start=0
        self.row_status={}
        for i,p in enumerate(self.files):
            row=ctk.CTkFrame(self.listbox,fg_color=FIELD);row.pack(fill='x',pady=4)
            text=ctk.CTkFrame(row,fg_color='transparent');text.pack(side='left',fill='x',expand=True,padx=8,pady=6)
            ctk.CTkButton(text,text=f'{Path(p).name[:26]}  →  IMG{start+i:04}',anchor='w',fg_color='transparent',command=lambda i=i:self.select_preview(i)).pack(fill='x')
            result=self.results.get(p)
            status=self.result_text(result) if result else self.tr('待转换')
            label=ctk.CTkLabel(text,text=status,text_color=MUTED,anchor='w',font=('Microsoft YaHei UI',11),wraplength=340)
            label.pack(fill='x');self.row_status[p]=label
            for name,d in [('↑',-1),('↓',1),('×',0)]:ctk.CTkButton(row,text=name,width=28,fg_color='#263747',command=lambda i=i,d=d:self.change(i,d)).pack(side='left',padx=2)
        mode=self.export_mode() if hasattr(self,'export') else 'binary'
        fmt={'binary':'BIN + R56','c':'C (.h)','both':'BIN + R56 + C (.h)'}[mode]
        self.count.configure(text=self.tr(f'已添加 {len(self.files)} 张图片 · 每张输出 {fmt}'))
    def tr(self,text):return translate(text,self.language)
    def notice(self,title,text,warning=False):
        (messagebox.showwarning if warning else messagebox.showinfo)(self.tr(title),self.tr(text))
    def switch_language(self,language):
        if language==self.language:return
        selected=[(w,values,canonical(w.get())) for w,values in self.option_widgets]
        self.language=language
        self.title('PixelSD 0.3.0 · '+('单片机图片工作台' if language=='中文' else 'Embedded Image Studio'))
        self.translatable=[(w,t) for w,t in self.translatable if w.winfo_exists()]
        for w,text in self.translatable:w.configure(text=self.tr(text))
        for w,values,value in selected:
            w.configure(values=[self.tr(v) for v in values]);w.set(self.tr(value))
        self.destination.configure(text=Path(self.output).name if self.output else self.tr('请选择文件夹（建议使用空文件夹）'))
        self.status.configure(text=self.tr(self.status_text))
        self.refresh();self.settings_changed();self.show_preview();self.update_estimate()
    def export_mode(self):
        return {'BIN + R56（默认）':'binary','C 数组（.h）':'c','二进制 + C 数组':'both'}[canonical(self.export.get())]
    def output_size(self):
        try:size=(int(self.image_width.get()),int(self.image_height.get()))
        except ValueError:raise ValueError('宽度和高度必须是 1–2047 之间的整数。') from None
        return validate_size(size)
    def apply_preset(self,value):
        value=canonical(value)
        if value=='自定义':return
        w,h=value.replace('（默认）','').split(' × ')
        self.image_width.set(w);self.image_height.set(h)
    def reset_display(self):
        self.image_width.set('240');self.image_height.set('320')
        self.color.set('RGB565');self.order.set(self.tr('低字节在前 · 样本默认'))
        self.fit.set(self.tr('完整显示 · 黑色留边'));self.rotation.set('0°');self.mirror.set(self.tr('无镜像'));self.background='#000000';self.bg_value.configure(text=self.background);self.settings_changed()
    def settings_changed(self):
        text=f'{self.image_width.get()} × {self.image_height.get()}'
        options=['240 × 320（默认）','320 × 240','240 × 240','320 × 480','480 × 320','800 × 480']
        self.preset.set(self.tr(next((v for v in options if v.replace('（默认）','')==text),'自定义')))
        try:
            self.output_size()
            self.summary.configure(text=self.tr(f'{text}  ·  {self.color.get()}  ·  离线批量转换'))
        except ValueError:self.summary.configure(text=self.tr('请输入有效尺寸（1–2047 px）  ·  离线批量转换'))
        if self.preview_job:self.after_cancel(self.preview_job)
        self.preview_job=self.after(250,self.show_preview)
        self.update_estimate()
    def select_preview(self,i):
        self.inspector_path=None;self.show_page('preview');self.show_preview(i)
    def leave_inspector(self):
        self.inspector_path=None;self.show_preview()
    def choose_background(self):
        color=colorchooser.askcolor(self.background,title=self.tr('选择留边颜色'))[1]
        if color:self.background=color;self.bg_value.configure(text=color);self.show_preview()
    def inspect_file(self,path=None):
        if path is None:path=filedialog.askopenfilename(title=self.tr('打开 BIN / R56'),filetypes=[('BIN / R56','*.bin *.r56')])
        if path:self.inspector_path=str(path);self.show_page('preview');self.show_preview()
    def show_preview(self,i=None):
        self.preview_job=None
        if not hasattr(self,'rotation'):return
        if i is not None:self.preview_index=i
        try:
            if self.inspector_path:
                endian='little' if canonical(self.inspector_order.get()).startswith('低') else 'big'
                im,meta=read_binary(self.inspector_path,endian,'RGB' if self.inspector_color.get()=='RGB565' else 'BGR')
                info=f"{Path(self.inspector_path).name}\n{meta['width']} × {meta['height']} · {meta['bytes']:,} B · {meta['format']}"
            else:
                if not self.files:self.preview.configure(image=None,text=self.tr('添加图片后显示预览'));self.preview_info.configure(text='');return
                self.preview_index=min(self.preview_index,len(self.files)-1)
                c=self.config()
                original=prepare(self.files[self.preview_index],c.fit,c.size,c.rotation,c.mirror,c.background)
                restored=decode(encode(original,c.endian,c.color),c.size,c.endian,c.color)
                mode=canonical(self.preview_mode.get())
                im=original if mode=='适配后原图' else restored
                if mode=='左右对比':
                    im=Image.new('RGB',(c.size[0]*2+4,c.size[1]),'#75e0c2');im.paste(original,(0,0));im.paste(restored,(c.size[0]+4,0))
                info=f'{Path(self.files[self.preview_index]).name}\n{c.size[0]} × {c.size[1]} · {c.color}565'
            factor=min(350/im.width,180/im.height)
            self.preview_image=ctk.CTkImage(im,im,size=(max(1,round(im.width*factor)),max(1,round(im.height*factor))))
            self.preview.configure(image=self.preview_image,text='')
            self.preview_info.configure(text=info)
        except Exception as e:
            self.preview.configure(image=None,text=self.tr('无法预览此文件'))
            self.preview_info.configure(text=self.tr(str(e)) if isinstance(e,ValueError) else type(e).__name__)
    def config(self):
        return Config(size=self.output_size(),fit=self.fit_value(),endian='little' if canonical(self.order.get()).startswith('低') else 'big',color='RGB' if self.color.get()=='RGB565' else 'BGR',mode=self.export_mode(),ctype=self.ctype.get(),layout='header' if canonical(self.layout.get())=='单个头文件' else 'split',rotation=int(self.rotation.get().replace('°','')),mirror={'无镜像':'none','水平镜像':'horizontal','垂直镜像':'vertical','水平 + 垂直':'both'}[canonical(self.mirror.get())],background=self.background)
    def update_estimate(self):
        if not hasattr(self,'estimate'):return
        try:
            c=self.config();pixels=c.size[0]*c.size[1];memory=pixels*2
            disk=(memory*2+16 if c.mode in ('binary','both') else 0)
            if c.mode in ('c','both'):disk+=round((pixels if c.ctype=='uint16_t' else memory)*(8.42 if c.ctype=='uint16_t' else 6.42)+650)
            self.estimate.configure(text=self.tr('每张像素存储')+f': {memory/1024:.1f} KiB\n'+self.tr('预计输出总量（约）')+f': {disk*len(self.files)/1024:.1f} KiB')
        except ValueError:self.estimate.configure(text='')
    def result_text(self,result):
        if not result:return self.tr('待转换')
        names={'done':'完成','failed':'失败','skipped':'跳过','cancelled':'已停止'}
        return f'IMG{result.job.number:04} · '+self.tr(names[result.status])+(' · '+self.tr(result.reason) if result.reason else '')
    def fit_value(self):return {'完整显示 · 黑色留边':'contain','铺满画面 · 居中裁剪':'cover','拉伸到屏幕':'stretch'}[canonical(self.fit.get())]
    def choose(self):
        p=filedialog.askdirectory(title=self.tr('选择输出文件夹'))
        if p:self.output=p;self.destination.configure(text=Path(p).name or p)
    def open_folder(self):
        if self.output and Path(self.output).is_dir():os.startfile(self.output)
    def run(self):
        if self.busy:return
        try:
            if not self.files:raise ValueError('请先添加图片。')
            try:start,end=int(self.start.get()),int(self.end.get())
            except ValueError:raise ValueError('请输入有效序号') from None
            validate_range(start,end,len(self.files))
            if not self.output:raise ValueError('请选择输出目录。')
            config=self.config()
            if self.index.get() and (config.mode=='c' or config.endian!='little' or config.color!='RGB'):
                raise ValueError('索引需要二进制输出、RGB565 和小端像素')
        except ValueError as e:self.notice('检查设置',str(e),True);return
        jobs=[Job(path,start+i,self.output,config) for i,path in enumerate(self.files)]
        self.launch_jobs(jobs,bool(self.index.get()))
    def retry_failed(self):
        jobs=[job for job in self.retry_snapshot if job.path in self.files]
        if not self.busy and jobs:self.launch_jobs(jobs,self.last_index)
    def launch_jobs(self,jobs,index):
        self.last_index=index;self.busy=True;self.cancel.clear();self.go.configure(state='disabled');self.retry.configure(state='disabled');self.stop.configure(state='normal')
        for widget in self.controls:widget.configure(state='disabled')
        for job in jobs:self.results.pop(job.path,None)
        self.refresh();self.progress.set(0)
        threading.Thread(target=self.process_jobs,args=(jobs,index),daemon=True).start()
    def process_jobs(self,jobs,index):
        results=run_jobs(jobs,self.cancel,self.events.put)
        notes=[]
        done=[r.job.number for r in results if r.status=='done']
        if index and done:
            first=jobs[0]
            try:write_index(first.folder,done,first.config.fit,first.config.size)
            except Exception as e:notes.append('索引未生成：'+type(e).__name__)
        self.events.put(('done',results,notes))
    def worker(self,files,start,folder,fit,endian,color,index,size=(240,320),mode='binary'):
        config=Config(size=size,fit=fit,endian=endian,color=color,mode=mode)
        self.process_jobs([Job(path,start+i,folder,config) for i,path in enumerate(files)],index)
    def poll(self):
        try:
            while True:
                event=self.events.get_nowait()
                if event[0]=='result':
                    result=event[1];self.results[result.job.path]=result
                    widget=self.row_status.get(result.job.path)
                    if widget:widget.configure(text=self.result_text(result))
                elif event[0]=='progress':
                    self.progress.set(event[1]);self.status_text=event[2];self.status.configure(text=self.status_text)
                elif event[0]=='done':
                    self.busy=False;self.go.configure(state='normal');self.stop.configure(state='disabled')
                    for widget in self.controls:widget.configure(state='normal')
                    self.retry_snapshot=retry_jobs(list(self.results.values()))
                    self.retry.configure(state='normal' if self.retry_snapshot else 'disabled')
                    success=sum(r.status=='done' for r in event[1]);fail=sum(r.status=='failed' for r in event[1]);skip=sum(r.status=='skipped' for r in event[1])
                    self.status_text=f'完成 {success} · 失败 {fail} · 跳过 {skip}'
                    if self.cancel.is_set():self.status_text='已停止 · '+self.status_text
                    self.status.configure(text=self.tr(self.status_text))
                    if event[2]:self.notice('检查设置','\n'.join(event[2]),True)
        except queue.Empty:pass
        self.after(100,self.poll)
    def close(self):
        if self.busy:self.cancel.set();self.notice('正在停止','请等待当前图片处理完成后再关闭。')
        else:self.destroy()
    def destroy(self):
        for timer in self.tk.splitlist(self.tk.call('after','info')):
            try:self.after_cancel(timer)
            except Exception:pass
        super().destroy()

if __name__=='__main__':
    app=App()
    if '--smoke-test' in sys.argv:app.after(2000,app.destroy)
    app.mainloop()
