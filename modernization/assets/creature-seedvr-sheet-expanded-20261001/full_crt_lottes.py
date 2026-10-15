"""Full CRT-Lottes algorithm CPU port (Tri, Bloom, VGA Mask, gamma).
No model/GPU submission, no gameplay. Explicit source-row phase for 2x sampling.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from run_expanded import OUT,write,sha
dest=OUT/'Phoenix/full-crt-lottes';dest.mkdir(exist_ok=True)
source=OUT/'Phoenix/PBLD/source-frames/00.png';sprite=Image.open(source).convert('RGBA')
# Fixed composited scene region, not a per-sprite alpha shader.
im=Image.new('RGB',(144,112),(58,78,44));im.paste(sprite,(28,20),sprite)
a=np.array(im).astype(float)/255
def linear(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def srgb(c):return np.where(c<.0031308,c*12.92,1.055*np.maximum(c,0)**.41666-.055)
def render(scale,phase,mask=True):
 h,w=a.shape[:2];xx=(np.arange(w*scale)+.5)/scale;yy=(np.arange(h*scale)+.5)/scale+phase;ix=np.floor(xx).astype(int);iy=np.floor(yy).astype(int);dx=.5-xx%1;dy=.5-yy%1
 pixels=linear(a*1.08)
 def horz(off,taps,hard):
  result=np.zeros((h*scale,w*scale,3));norm=np.zeros(w*scale)
  for k in range(-taps//2+1,taps//2+1):
   wt=2**(hard*np.abs(dx+k)**2);result+=pixels[np.clip(iy+off,0,h-1)[:,None],np.clip(ix+k,0,w-1)[None,:]]*wt[None,:,None];norm+=wt
  return result/norm[None,:,None]
 tri=sum(horz(off,taps,-3)*((2**(-8*np.abs(dy+off)**2))[:,None,None]) for off,taps in [(-1,3),(0,5),(1,3)])
 bloom=sum(horz(off,taps,-1.5)*((2**(-2*np.abs(dy+off)**2))[:,None,None]) for off,taps in [(-2,5),(-1,7),(0,7),(1,7),(2,5)])
 color=tri+bloom*.08
 if mask:
  # Original Lottes shadowMask4 VGA formula, output-pixel anchored.
  gx,gy=np.meshgrid(np.arange(w*scale)+.5,np.arange(h*scale)+.5);posx=np.floor(gx)+np.floor(gy*.5)*3;phase_mask=(posx*.166666666)%1
  m=np.full(color.shape,.55);m[:,:,0][phase_mask<.333]=1.5;m[:,:,1][(phase_mask>=.333)&(phase_mask<.666)]=1.5;m[:,:,2][phase_mask>=.666]=1.5;color*=m
 return Image.fromarray(np.rint(srgb(color).clip(0,1)*255).astype('uint8'))
results=[('Original nearest 2x',im.resize((288,224),Image.Resampling.NEAREST)),('Lottes 2x / phase 0',render(2,0)),('Lottes 2x / phase .25',render(2,.25)),('Original nearest 4x',im.resize((576,448),Image.Resampling.NEAREST)),('Lottes 4x / phase 0',render(4,0))]
for label,r in results:r.save(dest/(label.replace(' / ','-').replace(' ','_')+'.png'))
def compare(indices,name):
 panels=[]
 for k in indices:
  label,r=results[k];show=r.resize((576,448),Image.Resampling.NEAREST);panel=Image.new('RGB',(576,488),(24,24,30));panel.paste(show,(0,40));ImageDraw.Draw(panel).text((10,12),label,fill='white');panels.append(panel)
 sheet=Image.new('RGB',(576*len(panels),488))
 for i,p in enumerate(panels):sheet.paste(p,(576*i,0))
 sheet.save(dest/name)
compare([0,1,2],'comparison-2x.png');compare([3,4],'comparison-4x.png')
# Flat field verifies shader effect independent of sprite anatomy.
write(dest/'parameters.json',{'implementation':'Complete CPU port of CRT-Lottes Tri/Bloom/VGA Mask/sRGB algorithm, not GPU GLSL execution','source_url':'https://github.com/libretro/slang-shaders/blob/master/crt/shaders/crt-lottes.slang','source_snapshot_sha256':sha(OUT.parents[0]/'creature-crt-community-research-20261001/crt-lottes.txt'),'hardScan':-8,'hardPix':-3,'brightBoost':1.08,'hardBloomPix':-1.5,'hardBloomScan':-2,'bloomAmount':.08,'maskDark':.55,'maskLight':1.5,'shadowMask':4,'shape':2,'warp':0,'phase_native_rows':[0,.25],'scale':[2,4],'original_sprite_sha256':sha(source),'runtime_unchanged':True})
(dest/'REPORT.md').write_text('''# CRT-Lottes full algorithm offline trial

This implements the full community CRT-Lottes colour pipeline on CPU: original 3/5-tap Tri beam reconstruction, 5/7-tap Bloom, VGA output-pixel mask, gamma conversion. No GPU GLSL shader was executed; this is a CPU port, not the earlier normalized Gaussian approximation. Geometry warp is intentionally zero. Saved source snapshot/hash and all parameters are in parameters.json. No GPU/model job, game launch or runtime change.

comparison-2x.png: original nearest / full Lottes at 2x / full Lottes at 2x with a .25 source-row phase shift. At phase0, both output rows sample beam symmetrically: mask is visible, but scanline contrast is restricted. The explicit phase shift makes scanline bands visible, at the cost of shifting vertical sampling by a quarter native pixel. It is a sampling experiment, not an invisible free quality fix.

comparison-4x.png: original nearest 4x / full Lottes4x. 4x has enough samples for both scanline structure and VGA phosphor mask to read clearly without phase shift. This is a diagnostic view and does not change battle's accepted 1280x720 to 2560x1440 policy.

The Phoenix is composited on an illustrative green backdrop before CRT, preserving screen-anchored mask semantics within that fixed region. This is not a real battle screenshot, and full-frame motion, UI readability and performance are untested. CRT can make low-resolution textures integrate, but darkens the picture and adds mask/scanline structure, not missing anatomy or detail.
''',encoding='utf-8')
print('Full CRT algorithm comparison generated')
