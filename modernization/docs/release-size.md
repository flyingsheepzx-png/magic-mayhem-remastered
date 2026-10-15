# Release size comparison — 2026-09-30

Compared actual extracted files (no junction traversal):
- Original: `D:/BaiduNetdiskDownload/魔法师传奇中文版1.10 (2)` — 4,871 files,
  370,768,403 bytes (370.77 decimal MB / 353.59 MiB).
- Release after entry/layout refinement: `D:/Games/Magic&Mayham_Remastered_1.0`
  — 5,066 files including manifest, 704,204,287 bytes (704.20 MB / 671.58 MiB).
- Difference: 333,435,884 bytes. These are file-content totals, not allocated
  disk-cluster sizes and not compressed download archive sizes.

The entire difference is explained by interface assets: Interface increases
from 69,442,109 to 403,813,615 bytes (+334,371,506). Other categories combined
are 935,622 bytes smaller. Music, Realms, Creatures, Sounds, Portraits, Sprites,
Bitmaps and SpeechBox totals are unchanged. FMV decreases from 65,618,974 to
64,359,212 bytes (-1,259,762) following recorded compatible-video conversion.
The extra launcher itself is only 502,784 bytes; it does not account for size.

190 new Grimoire BMPs account for 262,666,260 bytes (262.67 MB). Each is a
640x720 RGB 24-bit BMP, 1,382,454 bytes including header. A representative
original `C0S00P1_PrefaceContents.JPG` is 400x600, 46,066 bytes; release JPG is
640x720, 150,128 bytes and its lossless BMP is 1,382,454 bytes. The content page
is 480x720 within a 640x720 compositor half; unused area has exact blue keys.
This is expanded widescreen compositing, not native 1920x1440 UI rendering.

The engine's recorded loader tries BMP before legacy JPEG fallback for keyed
pages (`docs/hd-integration.md`). Exact blue outside-parchment and magenta text
window keys require lossless values; JPEG compression corrupts those boundaries.
`tools/wide169_build.py` writes keyed BMPs and retains JPEGs at quality=100,
subsampling=0, so disk footprint grows from both lossless copies and enlarged
high-quality backgrounds. 285 changed interface files add another 71,705,246
bytes. All 190 BMPs have corresponding retained JPGs totalling 50,065,513 bytes.
Those fallback JPGs are a potential later packaging reduction, but removal
requires auditing every native loader use; this comparison did not delete them
or change image quality/format and does not claim them proven redundant.

This package carries runtime UI derivatives, not development logs, screenshots,
source trees or historical game copies. Future meaningful reduction would need
an audited lossless compressed format/decoder, validated palette/RLE support,
or removal of proven unused fallback assets. It is a separate compatibility
change; simply replacing BMP with JPEG risks restoring colour-key defects.

Detailed raw inventories and changed/extra file lists:
`releases/remastered-1.0/size-comparison.json`,
`releases/remastered-1.0/interface-size-comparison.json`.
