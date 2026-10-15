# CRT-Lottes full algorithm offline trial

This implements the full community CRT-Lottes colour pipeline on CPU: original 3/5-tap Tri beam reconstruction, 5/7-tap Bloom, VGA output-pixel mask, gamma conversion. No GPU GLSL shader was executed; this is a CPU port, not the earlier normalized Gaussian approximation. Geometry warp is intentionally zero. Saved source snapshot/hash and all parameters are in parameters.json. No GPU/model job, game launch or runtime change.

comparison-2x.png: original nearest / full Lottes at 2x / full Lottes at 2x with a .25 source-row phase shift. At phase0, both output rows sample beam symmetrically: mask is visible, but scanline contrast is restricted. The explicit phase shift makes scanline bands visible, at the cost of shifting vertical sampling by a quarter native pixel. It is a sampling experiment, not an invisible free quality fix.

comparison-4x.png: original nearest 4x / full Lottes4x. 4x has enough samples for both scanline structure and VGA phosphor mask to read clearly without phase shift. This is a diagnostic view and does not change battle's accepted 1280x720 to 2560x1440 policy.

The Phoenix is composited on an illustrative green backdrop before CRT, preserving screen-anchored mask semantics within that fixed region. This is not a real battle screenshot, and full-frame motion, UI readability and performance are untested. CRT can make low-resolution textures integrate, but darkens the picture and adds mask/scanline structure, not missing anatomy or detail.
