# Static analysis tools

These tools import a hash-identified copy into a new Ghidra project. They do not
launch or patch the target. Keep that separation when extending them.

- Never infer patch authorization from a hash supplied for static inspection.
- Never reuse a Ghidra database from another binary version without explicit
  version tracking. Keep projects exclusive to one writer; refuse overwrites.
- Record analysis timeout, failed decompilation, export limits and unresolved
  indirect calls. Pseudocode and discovered types are hypotheses until validated.
- Use synthetic x86 input for tool smoke tests; game fixtures are unnecessary.
- Generated databases, binaries and exports belong outside Git. Preserve useful
  named-function/type evidence in the project's documentation with exact hashes.
