# Book/chest state-family sidecar

UNSUITABLE FOR ADOPTION. The SPR is diagnostic only.

Normal and hover use the same generated book/chest designs. Hover is visibly brighter.

Pressed book and chest visibly retain the original bright flash after signed RGB delta transfer.

Exact offset alignment exposes 412 book and 516 chest pressed opaque pixels without opaque generated-normal coverage. These retain current state RGB for diagnostic completeness; they are not claimed to be generated-base art.

Pressed chest has doubled upper rim/lid lines and inconsistent lower rim highlights; pressed book has conflicting page-edge texture. These are geometric overlay failures, not rejection of readable art.

The six-state derivative must not be adopted. Exact metadata and alpha tests pass, but do not establish coherent artwork.

Alignment: All six frames use their unchanged offsets in a common family atlas, following existing spr_sequence convention. Native runtime placement was not tested. No frame resizing/recentering.

Tests: frames 3–8 replaced; 15 other frame payloads byte-identical; all 21 dimensions, offsets, names, flags and alpha exact. Decode/RGB565 bound passed. Pressflash visibly preserved in paired current/candidate sheet at existing 2x source size. No model call, game launch or runtime edit.
