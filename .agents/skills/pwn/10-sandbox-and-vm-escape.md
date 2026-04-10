## Sandbox & VM Escape

- Primary Probe:
  - * -> [Condition: Target runs inside a browser, language sandbox, container, or guest VM] -> Action: split the problem into guest-side initial memory corruption, boundary-object discovery, and host-transition primitive rather than treating the escape as one bug.
- Dead End Pivots:
  - * -> [Condition: Direct host interface is hidden] -> Action: enumerate shared memory, paravirtual devices, clipboard channels, filesystem passthrough, RPC bridges, and hypercalls or broker IPC.
  - * -> [Condition: Browser/JIT target is too noisy] -> Action: separate memory corruption from JIT spraying / RWX transitions / type confusion and validate each in isolation.
  - * -> [Condition: Container target looks locked down] -> Action: inspect namespace joins, cgroup delegation, privileged helper binaries, mounted sockets, and kernel attack surface from inside the container.
- Data Chaining:
  - * -> [Condition: Guest arbitrary R/W exists] -> Action: target boundary-facing objects first, such as virtio descriptors, broker messages, shared-memory metadata, or serialization handlers.
  - * -> [Condition: Sandbox policy blocks syscalls] -> Action: switch from raw syscall goals to broker abuse, confused-deputy file access, or JIT/object corruption that stays within the policy until the final escape edge.
  - * -> [Condition: VM bug is reachable only from a device model] -> Action: drive it through a minimal harness under emulation to stabilize coverage before attempting a full chained escape.
- Mitigation branches:
  - * -> [Condition: seccomp/user namespace/AppArmor present] -> Action: treat policy as a routing constraint, not a stop sign; the exploit path becomes capability laundering, broker abuse, or kernel attack surface expansion.

