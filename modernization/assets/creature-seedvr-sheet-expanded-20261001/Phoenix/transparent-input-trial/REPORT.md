# Actual transparent RGBA input rerun

New authenticated Manager FIFO job: 4686a192e7014cc1a4840f84a3061bea. Eight Phoenix PBLD source frames, same packing, input 768x320 RGBA, output 1536x640 RGBA. Input is alpha-zero background with hidden RGB zero, no grey matte. Native source opaque RGB and alpha are copied directly without compositing. Profile remains SeedVR2 7B Sharp, default seed42/noise0, Lab, batch1, tiled VAE and CPU tensor offload.

Returned output has 256 alpha values, 926771 zero-alpha pixels, 35797 partial-alpha pixels and 20472 opaque pixels. Returned alpha is used unchanged; no source-mask replacement, unmatting or colour-donor repair is applied. Dimensions match exactly. Inputs and results are hashed in manifest.json. Runtime remains untouched.

Important architecture limit: installed generation_phases.py separates video[:,:3] from alpha before the RGB model, and alpha_upscaling.py performs edge-guided alpha upscaling and concatenates RGB and alpha afterwards. Thus the RGBA pipeline supports transparent inputs/outputs, but the diffusion model does not jointly infer RGBA; it still sees RGB zero (black) in transparent pixels. This is not the old grey-matte workflow and not true alpha-conditioned diffusion.

Compare frame-00-white.png / frame-00-black.png and animation-white.png / animation-black.png. Old arm uses original grey-input result with binary source alpha; new arm uses newly inferred RGBA and returned native soft alpha. This A/B changes both RGB background and alpha method, so it is not a single-variable alpha comparison. Replacing grey with transparent RGBA may reduce grey contamination but can retain dark outlines from hidden black RGB and original dark sprite edges; no halo-free claim is made.
