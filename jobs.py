"""Immutable batch requests and per-file outcomes. No persistence or logging."""
from dataclasses import dataclass
from pathlib import Path
from PIL import UnidentifiedImageError
from core import prepare,encode,write_outputs,output_extensions

@dataclass(frozen=True)
class Config:
    size:tuple=(240,320)
    fit:str='contain'
    endian:str='little'
    color:str='RGB'
    mode:str='binary'
    ctype:str='uint16_t'
    layout:str='header'
    rotation:int=0
    mirror:str='none'
    background:str='#000000'

@dataclass(frozen=True)
class Job:
    path:str
    number:int
    folder:str
    config:Config

@dataclass(frozen=True)
class Result:
    job:Job
    status:str
    reason:str=''

def run_jobs(jobs,cancel,emit=lambda event:None):
    results=[]
    for i,job in enumerate(jobs):
        if cancel.is_set():
            result=Result(job,'cancelled','未处理')
        else:
            c=job.config
            try:
                if any((Path(job.folder)/f'IMG{job.number:04}{ext}').exists() for ext in output_extensions(c.mode,c.layout)):
                    raise FileExistsError()
                pixels=encode(prepare(job.path,c.fit,c.size,c.rotation,c.mirror,c.background),c.endian,c.color)
                if cancel.is_set():result=Result(job,'cancelled','未处理')
                else:
                    write_outputs(job.folder,job.number,pixels,c.size,c.mode,c.endian,c.ctype,c.layout)
                    result=Result(job,'done','')
            except FileExistsError:result=Result(job,'skipped','同名文件已存在')
            except FileNotFoundError:result=Result(job,'failed','源文件或输出目录不存在')
            except PermissionError:result=Result(job,'failed','无法读取或写入，请检查权限')
            except UnidentifiedImageError:result=Result(job,'failed','图片损坏或格式不受支持')
            except OSError as e:result=Result(job,'failed','磁盘空间不足' if getattr(e,'errno',None)==28 else '文件读取或写入失败')
            except Exception as e:result=Result(job,'failed',f'转换失败：{type(e).__name__}')
        results.append(result)
        emit(('result',result))
        emit(('progress',(i+1)/len(jobs),f'{i+1} / {len(jobs)}'))
    return results

def retry_jobs(results):
    return [r.job for r in results if r.status=='failed']
