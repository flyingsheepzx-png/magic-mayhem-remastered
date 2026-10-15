# Bounded Portmanteau icon ART review

Decision: selectively retain generated normal book (3) and chest (6) as a sidecar SPR candidate for main UI cases. Do not adopt the full generated sheet.

Nearest enlargement has visibly stepped page edges and character faces. Lanczos smooths edges without changing source alpha. Current preserves all 21 exact nearest-source silhouettes; it combines plain normal frames 0,3,9 with sharpened/redrawn other frames.

Generated normal book 3 has clearly separated cover, page planes, green emblem and clasp at 94x82. Generated normal chest 6 has a clearer lid, interior compartments, hinge and bronze/gold metal planes at 94x82. These are useful readable redesigns, not rejected merely for departing from original shading.

Generated faces are individually more readable but reinterpret expressions and introduce background or neck fragments inside the locked original mask. Full-sheet frames 2,8,14,17,20 show visible edge clipping because generated content did not exactly follow the state-specific silhouette.

Raw generated three-state rows largely lost the original white pressed glint and normal/highlighted differences. Preserve existing highlighted and pressed payloads in the selective derivative; the change of art across states still requires main UI tests and user acceptance.

All generation crops are fixed reference coordinates, with no invented position corrections. The original nearest alpha is restored after extraction; exact alpha alone does not prove the generated painted object follows its silhouette.

Port-icons (234 frames) and Grimoire page icon collections have different counts and content; they are not alternate 21-frame toolbar replacements. They remain untouched. No runtime page transition or interaction claim is made.

Tests: 21-frame count, dimensions, offsets, names, flags and alpha exact; 19 non-target frame payloads byte-identical. Full trial RGB565 error <=9. Source/current/page variant input hashes unchanged. Runtime acceptance pending user testing.

Source / nearest / Lanczos / current / generated images and per-frame exports are in this folder. Request, seed, status, owned job ID, observations and output hash are in qwen-call.json and qwen-status.json. No model substitution, game launch, installation or outside-scope write.
