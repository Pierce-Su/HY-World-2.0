"""One of four authorized new samples; isolated cold process; no retries."""
import os,sys,json,time,hashlib,subprocess,threading,traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/root/HY-World-2.0'); RUN=ROOT/'deployment/t_74bcb4c8'
sys.path.insert(0,str(ROOT/'hyworld2/panogen'))
import torch
from PIL import Image
from pipeline_with_qwen_image import (HunyuanPanoPipeline,GENERAL_POSITIVE_PREFIX,GENERAL_POSITIVE_SUFFIX,GENERAL_NEGATIVE_PROMPT)
models=json.loads((RUN/'models.json').read_text())
source=ROOT/'curated_set/photorealistic/0106.jpg'
record=next(r for r in json.loads((ROOT/'curated_set/metadata.json').read_text())['samples'] if r['index']==106)
assert record['index']==106
prompt=record['photorealistic']['prompt']
out=RUN/'photorealistic_0106';out.mkdir(exist_ok=False)
settings=dict(prompt=prompt,negative_prompt='',seed=42,height=960,width=1952,num_inference_steps=40,guidance_scale=1.0,true_cfg_scale=7.5,blend_width=32,crop_border=0.0)
meta={'started_utc':datetime.now(timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),'input':str(source),'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'selected_variant':'photorealistic','dtype':'bfloat16','quantization':False,'offload':False,'input_record':record,'settings':settings,'positive_prompt':(GENERAL_POSITIVE_PREFIX+prompt+GENERAL_POSITIVE_SUFFIX).strip(),'negative_prompt':GENERAL_NEGATIVE_PROMPT.strip(),'models':models,'torch':torch.__version__,'cuda':torch.version.cuda,'gpu_measurement':'torch.cuda.max_memory_allocated/reserved covers model load and inference; nvidia-smi total-device memory.used/utilization sampled at 1-second intervals, not continuous peak'}
(out/'config.json').write_text(json.dumps(meta,indent=2))
stop=threading.Event(); samples=[]
def observe():
    with (out/'gpu_samples.csv').open('w') as f:
        f.write('unix_time,memory_used_MiB,utilization_percent\n');f.flush()
        while not stop.is_set():
            try:
                line=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
                mem,util=map(float,line.split(','));samples.append((mem,util));f.write(f'{time.time()},{mem},{util}\n');f.flush()
            except Exception as e: print('MONITOR_ERROR',repr(e),flush=True)
            stop.wait(1)
thread=threading.Thread(target=observe,daemon=True);thread.start()
t0=time.perf_counter();torch.cuda.reset_peak_memory_stats()
try:
    print('MODEL_LOAD_START',datetime.now(timezone.utc).isoformat(),flush=True)
    pipe=HunyuanPanoPipeline.from_pretrained(models['Qwen/Qwen-Image-Edit-2509']['snapshot'],lora_path=models['tencent/HY-World-2.0']['snapshot'],lora_subfolder='HY-Pano-2.0')
    torch.cuda.synchronize();t1=time.perf_counter();print('MODEL_LOAD_DONE',t1-t0,flush=True)
    image=pipe(source,**settings)
    torch.cuda.synchronize();t2=time.perf_counter()
    dest=out/'panorama.png';image.save(dest)
    with Image.open(dest) as decoded:
        decoded.load();assert decoded.size==(1920,960),decoded.size;assert decoded.mode=='RGB',decoded.mode
    result={'status':'success','finished_utc':datetime.now(timezone.utc).isoformat(),'output':str(dest),'size':[1920,960],'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'load_seconds':t1-t0,'inference_seconds':t2-t1,'end_to_end_seconds':time.perf_counter()-t0}
except BaseException as e:
    result={'status':'failure','error':repr(e),'elapsed_seconds':time.perf_counter()-t0};traceback.print_exc();raise
finally:
    stop.set();thread.join(12)
    result.update(torch_peak_allocated_bytes=torch.cuda.max_memory_allocated(),torch_peak_reserved_bytes=torch.cuda.max_memory_reserved(),nvidia_smi_sample_count=len(samples),nvidia_smi_sampled_max_MiB=max((a for a,b in samples),default=None),nvidia_smi_sampled_max_util_percent=max((b for a,b in samples),default=None))
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
