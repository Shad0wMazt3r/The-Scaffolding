## Symbolic & Concolic Execution

- Primary Probe
  - * -> [Condition: Validation path is narrow and input-bound] -> Action: isolate the checker function, stub non-essential environment calls, symbolize only the true input bytes, and target success blocks directly.
  - * -> [Condition: Heavy unpacking or self-modifying front-end exists] -> Action: concretely execute to the post-unpack/post-decrypt checkpoint, then hand execution to angr or Triton from the simplified state.
  - * -> [Condition: Data-dependency clarity is low] -> Action: apply taint first to find which bytes truly influence rejection branches before full constraint solving.
- Dead End Pivots
  - * -> [Condition: Path explosion] -> Action: slice to the validator, merge equivalent states, concretize irrelevant bytes, and replace known library calls with summaries.
  - * -> [Condition: Indirect memory or VM noise breaks the model] -> Action: lift only the reduced checker or the recovered VM bytecode, not the full native wrapper.
  - * -> [Condition: Solver returns unstable models] -> Action: add domain constraints from observed runtime values, character classes, checksums, or length invariants.
- Data Chaining
  - * -> [Condition: Dynamic tracing identifies compare sinks] -> Action: use those PCs as find/avoid targets in the symbolic harness.
  - * -> [Condition: Deobfuscation recovers transform routines] -> Action: reimplement them faithfully and replace opaque native blocks with clean symbolic summaries.
  - * -> [Condition: Model produces candidate flag/key] -> Action: validate against a traced concrete run and preserve the accepted path constraints as proof.

angr’s published examples call out Unicorn-backed concrete execution as essential for some self-modifying challenges because symbolically simulating unpacking is too slow. [docs.angr](https://docs.angr.io/en/latest/examples.html)

Script Definition Block — symbolic harness planner
- Input Data: validator entry PC, success/fail PCs, initial memory/register snapshot, imported-function stubs, input buffer location.
- Core Processing Logic:
  - Build a minimal state from a post-unpack checkpoint.
  - Symbolize only user-controlled bytes that taint decision points.
  - Add library summaries and environment models.
  - Run directed exploration to success while recording blocking predicates.
- Dependencies: angr, Triton or PyVEX, Unicorn checkpoint, Z3.
- Expected Output Format: `solution.bin`, `constraints.smt2`, `path_report.json`.

