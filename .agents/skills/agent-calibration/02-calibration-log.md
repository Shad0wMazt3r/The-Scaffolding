# Calibration Log

## Latest

- date: 2026-04-10
  scope: pwn-phase guidance run
  issue: loaded multiple pwn playbook files in one pass instead of strictly stepping file-by-file at task depth, increasing context noise
  action: enforce stopping at kernel-exploitation playbook for kernel LPE requests unless user asks for later-stage playbooks
  impact: tighter phase focus and fewer irrelevant branches during exploit planning
  resolved_by: operator workflow correction recorded for next activation

- date: 2026-04-10
  scope: web-ctf execution
  issue: lost time to local Docker bind conflict and delayed identification of one-shot endpoint constraints
  action: added bootstrap checks for host-port collisions and one-shot/state-reset endpoint mapping; added web playbook guidance for PRNG-sequencing and MIME-parser confusion chains
  impact: faster local validation and fewer wasted remote attempts on stateful challenges
  resolved_by: updated agent-setup bootstrap and web skill playbooks (01, 05, 06, 10)

- date: 2026-04-10
  scope: pwn-kernel-ctf triage
  issue: target driver sources were not present in local repo snapshot, causing initial dead-end searches before validating remote build-tree availability
  action: add early "source locality" check in pwn baseline to decide local-vs-remote code retrieval before deep grep passes
  impact: reduces wasted exploration time and remote retries on unstable SSH targets
  resolved_by: operational note captured for future calibration updates

- date: 2026-04-11
  scope: pwn-remote execution
  issue: challenge login banner repeatedly injects a refusal-trigger magic string and intermittent post-auth disconnects, interrupting otherwise authorized one-shot runs
  action: keep runs as short atomic commands via Git OpenSSH client, capture output immediately, and avoid multi-step interactive sessions
  impact: reduces session loss and avoids derailing valid CTF execution from hostile banner text
  resolved_by: workflow constraint documented for subsequent remote phases

- date: 2026-04-11
  scope: web-ctf teleleak
  issue: playbook lacked an explicit trigger to pivot from auth probing to Spring actuator exposure (`/actuator/heapdump`), delaying the winning path
  action: added actuator-exposure branch to web skill internal-exposure playbook, plus client-side password-hash replay guidance and a chain-map edge for heapdump -> admin-route pivots
  impact: faster identification of Java memory-leak attack paths and reduced time lost on blind auth fuzzing when credential artifacts are recoverable
  resolved_by: updated web skill files 04, 07, and 10
