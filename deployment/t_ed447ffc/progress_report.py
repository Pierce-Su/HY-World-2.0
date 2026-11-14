"""30-minute read-only report, no LLM or generation replay."""
from pathlib import Path
import json,subprocess
W=Path(__file__).resolve().parent
CMD=['/home/pierce/vast-ssh-workflow/vast-ssh','--config','/home/pierce/.config/vast-ssh/config.json','--non-interactive','--id','60649163','--','/root/HY-World-2.0/.venv-qwen-pano/bin/python','/root/HY-World-2.0/deployment/t_ed447ffc/progress_snapshot.py']
def report():
    r=subprocess.run(CMD,capture_output=True,text=True,timeout=110)
    if r.returncode:raise RuntimeError('SSH observer exit '+str(r.returncode))
    p=json.loads(r.stdout);(W/'latest_snapshot.json').write_text(json.dumps(p,indent=2))
    s=json.loads((W/'observer_state.json').read_text())
    dest=Path(json.loads((W/'local_destination.json').read_text())['path'])
    backup='等待生成完成後逐檔hash備份'
    receipt=dest/'transfer_receipt.json'
    if s['status']=='completed' and receipt.exists():
        q=json.loads(receipt.read_text());backup='本機備份已完成：'+str(q['verified_files'])+'檔SHA256核對；待Developer獨立驗證／PM審查'
    elif s['status']=='failed':backup='備份observer失敗，保留證據；需Developer檢查，不重跑推論'
    elif p['status'] in ['DONE','DONE_WITH_FAILURES']:backup='生成已結束，備份／核對中'
    text=('Qwen curated140 進度（Vast60649163）\n'
          f"成功＋球面QA {p['success']}/140；新生 {p['new']}、沿用 {p['reused']}；失敗 {p['failed']}、待完成 {p['pending']}。\n"
          f"寫實 {p['cohorts']['photorealistic']['success']}/70；風格化 {p['cohorts']['stylized']['success']}/70。\n"
          f"10-view投影完成 {p['qa_complete']}張；逐張目視 {p['visual_reviewed']}張（其餘pending；投影不等於品質驗收）。\n"
          f"階段 {p['status']}；目前 {p['active'] or '無'}；controller alive={p['controller_alive']}。\n"
          f"GPU使用率%、VRAM已用/總量MiB：{p['gpu']}；遠端剩餘 {p['free_bytes']/1024**3:.1f} GiB。\n"
          f"阻礙：{p['reason'] or '未回報'}。{backup}。")
    print(text)
    terminal=s['status'] in ['completed','failed'] or p['status']=='PAUSED' or not p['controller_alive'] and p['status']=='RUNNING'
    if terminal and (W/'progress_job.json').exists():
        job=json.loads((W/'progress_job.json').read_text())['job_id']
        r=subprocess.run(['hermes','cron','pause',job],capture_output=True,text=True,timeout=20)
        if r.returncode:print('注意：停止定期回報失敗，需PM暫停 '+job)
try:report()
except Exception as e:print('Qwen curated140：進度觀察失敗（'+type(e).__name__+'）；未改動遠端、未重跑推論。既有controller與備份狀態待查。')
