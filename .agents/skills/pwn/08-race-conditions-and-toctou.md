## Race Conditions & TOCTOU

- Primary Probe:
  - * -> [Condition: Separate check and use phases touch a file, path, FD, permission, or shared object] -> Action: map the exact race window and amplify it with CPU affinity, I/O delay, FUSE-backed latency, or competing worker floods.
- Dead End Pivots:
  - * -> [Condition: Window is too narrow locally] -> Action: move the checked resource onto FUSE or a slow network mount to widen the gap deterministically.
  - * -> [Condition: Path race is patched] -> Action: pivot to descriptor reuse, directory replacement, symlink farming, or namespace boundary confusion.
  - * -> [Condition: Timing remains inconsistent] -> Action: instrument with `strace`/`perf`/scheduler pinning and treat the race as a probabilistic exploit needing an orchestrator rather than a single-shot payload.
- Data Chaining:
  - * -> [Condition: TOCTOU grants write into a privileged path] -> Action: replace config, loader path, cron target, plugin, or script body, then trigger the privileged consumer.
  - * -> [Condition: Race grants arbitrary file read] -> Action: harvest secrets, tokens, or library paths that unlock a later memory-corruption exploit.
  - * -> [Condition: Race reaches a memory object] -> Action: reinterpret it as an object-lifetime/UAF problem and route into the UAF playbook.
- Script Definition Block:
  - **Input Data:** target path set, candidate symlinks, scheduler topology, observed race window in microseconds.
  - **Core Processing Logic:** create producer and consumer workers; pin them to selected CPUs; insert latency amplifier; rotate symlink/rename targets; log success probability by iteration bucket; snapshot winning filesystem state.
  - **Dependencies:** Python asyncio or Bash + `taskset`, optional FUSE filesystem.
  - **Expected Output Format:** CSV with `attempt`, `window_us`, `cpu_pair`, `target_variant`, `success`, `artifact_path`.

