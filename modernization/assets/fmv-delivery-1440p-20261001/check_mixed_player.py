"""Final Celtic/Greek decode/playback compatibility, hidden/muted, no game launch."""
import json,subprocess,shutil
from pathlib import Path
from deliver import ROOT,sha
VC='C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat'
def main():
 source=(ROOT/'fmv_h264.cpp').read_text(encoding='utf-8')
 # Production source/DLL unchanged; test clone only forces audio silence.
 needle=' HRESULT hr=MFPCreateMediaPlayer(nullptr,FALSE,MFP_OPTION_FREE_THREADED_CALLBACK,cb,child,&view.player);'
 assert source.count(needle)==1
 (ROOT/'fmv_h264_validation.cpp').write_text(source.replace(needle,needle+'\n if(SUCCEEDED(hr))view.player->SetVolume(0.0f);'),encoding='utf-8')
 cmd='@echo off\ncall "'+VC+'" x86 >nul\nif errorlevel 1 exit /b 1\ncl /nologo /LD /MT /O2 /EHsc /std:c++17 fmv_h264_validation.cpp /link /OUT:fmv_h264_validation.dll mfplay.lib mfplat.lib mfuuid.lib ole32.lib bcrypt.lib user32.lib gdi32.lib\nif errorlevel 1 exit /b 1\ncl /nologo /MT /O2 /EHsc /std:c++17 playback_host.cpp /link /OUT:playback_host.exe user32.lib\n'
 (ROOT/'build-validation.cmd').write_text(cmd,encoding='utf-8');subprocess.run(['cmd.exe','/c','build-validation.cmd'],cwd=ROOT,check=True)
 rows=[]
 for name in ('Celtic','Greek'):
  out=ROOT/'playback-checks'/('component-'+name);out.mkdir(parents=True,exist_ok=True)
  raw=subprocess.check_output([str(ROOT/'playback_host.exe'),str(ROOT/'fmv_h264_validation.dll'),str(ROOT/(name+'.mp4'))],cwd=out,timeout=60)
  result=json.loads(raw);events=[json.loads(x) for x in (out/'fmv-h264-events.jsonl').read_text(encoding='utf-8').splitlines() if x]
  assert result['return']==1 and any(e['event']=='ended' for e in events)
  assert any(e['event']=='video_width' and e['value']==2560 for e in events)
  assert any(e['event']=='audio_selected' and e['value']==1 for e in events)
  assert not any(e['event'] in ('mf_error','mf_command_error') for e in events)
  row=dict(name=name,result=result,events=str(out/'fmv-h264-events.jsonl'),events_sha256=sha(out/'fmv-h264-events.jsonl'),production_player_source_sha256=sha(ROOT/'fmv_h264.cpp'),validation_difference='forced SetVolume(0) only; same decode, render-window setup, timing and return logic; no game instance/trigger tested')
  (out/'report.json').write_text(json.dumps(row,indent=2),encoding='utf-8');rows.append(row);print('MIXED_PLAYBACK_VERIFIED',name,flush=True)
 # Restore real filenames in isolated deliverable after temporary startup aliases.
 m=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
 for name,row in m['films'].items():
  target=ROOT/'playtest/runtime/FMV'/(name+'.mp4');shutil.copy2(row['mp4'],target);assert sha(target)==row['mp4_sha256']
 (ROOT/'mixed-player-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 print('FINAL_NAMES_RESTORED',flush=True)
if __name__=='__main__':main()
