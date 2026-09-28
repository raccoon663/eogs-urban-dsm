"""Measure an unchanged EOGS entry point in-process."""
import sys, time, json, runpy, threading, subprocess, traceback
from pathlib import Path
import torch
entry, report, *args = sys.argv[1:]
entry=Path(entry).resolve(); report=Path(report).resolve()
sys.path.insert(0,str(entry.parent)); sys.argv=[str(entry),*args]
stop=threading.Event(); samples=[]
def monitor():
    while not stop.is_set():
        try:
            line=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).splitlines()[0]
            samples.append({'elapsed_s':time.perf_counter()-start,'whole_gpu_mib':float(line)})
        except Exception:
            pass
        stop.wait(1)
torch.cuda.init(); torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
start=time.perf_counter(); thread=threading.Thread(target=monitor,daemon=True); thread.start()
status='failed'; error=None
try:
    runpy.run_path(str(entry),run_name='__main__')
    torch.cuda.synchronize(); status='success'
except BaseException as exc:
    error=repr(exc); raise
finally:
    elapsed=time.perf_counter()-start; stop.set(); thread.join(timeout=3)
    result=dict(status=status,error=error,command=sys.argv,wall_seconds=elapsed,
        peak_torch_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
        peak_torch_reserved_mib=torch.cuda.max_memory_reserved()/2**20,
        sampled_peak_whole_gpu_mib=max((s['whole_gpu_mib'] for s in samples),default=None),
        gpu_samples=samples)
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n')
