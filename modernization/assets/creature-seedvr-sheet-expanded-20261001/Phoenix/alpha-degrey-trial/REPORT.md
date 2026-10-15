# Phoenix grey-edge cleanup test

Eight saved SeedVR2 frames were processed on CPU, without new GPU submissions or runtime changes. Four arms share identical soft alpha and dimensions: raw RGB, previous outer-fringe repair, grey-matte inversion, interior-colour extension.

The white-background first-frame inspection shows interior-colour extension most clearly removes the grey outline around the wing and tail. Grey-matte inversion is less effective: 159–413 partial-alpha pixels per frame produce out-of-range colours before clipping, evidence that generated RGB cannot be exactly inverted using this source-derived alpha. Prior outer-fringe repair misses contaminated pixels inside the original mask.

Interior extension uses nearest donor colours from one output pixel inside the original opaque support, within four output pixels. It changes 2701–3471 partial pixels per frame; 4–33 per frame lack a nearby donor and remain unchanged. It may flatten narrow feather or colour details. This is a practical edge cleanup candidate, not proof of recovered original colour or full temporal acceptance. Opaque grey contamination is not handled by this variant.

View index.html for full-size grey/black/white APNG animations. frame-00-white.png illustrates the four arms, left to right. validation.json records counts and assumptions. Numbered RGBA outputs preserve actual alpha. Display images use integer nearest 3x enlargement. Model RGB was originally inferred against background (48,48,56); none of the methods is true transparent-background inference.
