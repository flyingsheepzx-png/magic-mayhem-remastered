"""CPU-only full-resolution map comparisons and interactive selected-state preview."""
from qwen_fullreadable_realms_11 import OUT,RT,ROOT,sha,save
from PIL import Image
import json
worlds={}
for world in ['Medieval','Greek']:
    dest=OUT/world
    v=json.loads((dest/'verification.json').read_text(encoding='utf-8'))
    old=RT/f'Interface/RealmViewer/800x600/{world}_Map.PNG'
    assert sha(old)==json.loads((dest/'job.json').read_text(encoding='utf-8'))['installed_before_sha256']
    previous=Image.open(old).convert('RGB');previous.save(dest/'previous.png')
    Image.open(ROOT/f'modernization/assets/hd/source-original/Interface/RealmViewer/800x600/{world}_Map.bmp').convert('RGB').resize((1920,1440),Image.Resampling.LANCZOS).save(dest/'original-lanczos.png')
    new=Image.open(dest/'target-1920x1440.png');old_content=previous.crop((320,0,2240,1440))
    # Full-size central crops for detail review; no sharpening/resizing.
    crop=(640,480,1280,960);pair=Image.new('RGB',(1280,480));pair.paste(old_content.crop(crop));pair.paste(new.crop(crop),(640,0));pair.save(dest/'detail-1to1.png')
    worlds[world]=v['selected_states']
html='''<!doctype html><meta charset="utf-8"><title>FullReadable 地图对比</title>
<style>body{background:#191c21;color:#eee;font:16px system-ui;margin:24px}select,button,input{font:inherit;margin:8px}img{max-width:100%;height:auto}#stage{position:relative;max-width:1400px}#stage img{display:block;width:100%}#over{position:absolute;inset:0;clip-path:inset(0 50% 0 0)}a{color:#a8d1ff}</style>
<h1>第二、三章 · Qwen Image 2.1 FullReadable</h1>
<p>左侧为新图，右侧为旧图。拖动滑块对比；选择区域查看从同一新底图派生的悬浮态。</p>
<select id="world"><option value="Medieval">第三章 Medieval</option><option value="Greek">第二章 Greek</option></select>
<select id="region"></select><label>对比位置 <input id="slider" type="range" value="50" min="0" max="100"></label>
<div id="stage"><img id="old"><img id="over"></div><p id="links"></p>
<p>40 steps · seed 26093012 · 2400×1792 生成 → 1920×1440 原生 UI 内容 → 2560×1440 画布。未叠加锐化或旧图纹理。</p>
<p>选中态使用原始 PCX 遮罩、抗锯齿边缘与内侧描边；跨章节传送门保留原有旋涡。道路和地标的生成位置仍需游戏验收。</p>
<script>const counts=COUNTS;const $=id=>document.getElementById(id);function update(){let w=$('world').value,r=$('region').value;$('old').src=w+'/previous.png';$('over').src=w+'/runtime/Interface/RealmViewer/'+(r==='0'?'800x600/'+w+'_Map.PNG':'hd-selected/'+w+'_'+r.padStart(2,'0')+'.PNG');$('links').innerHTML='<a href="'+w+'/comparison.png">全图对比</a> · <a href="'+w+'/detail-1to1.png">1:1 细节对比</a> · <a href="'+w+'/target-1920x1440.png">1920×1440 新底图</a>';}function chapter(){let w=$('world').value;$('region').innerHTML='<option value="0">底图</option>'+Array.from({length:counts[w]},(_,i)=>'<option value="'+(i+1)+'">区域 '+(i+1)+'</option>').join('');update();}$('world').onchange=chapter;$('region').onchange=update;$('slider').oninput=()=>{$('over').style.clipPath='inset(0 '+(100-$('slider').value)+'% 0 0)';};chapter();</script>'''
(OUT/'index.html').write_text(html.replace('COUNTS',json.dumps(worlds)),encoding='utf-8')
print('Preview saved',OUT/'index.html')
