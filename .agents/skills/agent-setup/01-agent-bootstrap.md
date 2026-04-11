# Agent Bootstrap

Always validate this prerequisite block before activating any category skill:

- Create/confirm the target root folder for the current mission.
- Prepare required credentials and secrets out-of-band from shell history. 
- Verify outbound connectivity and proxy expectations.
- Confirm approved toolchain presence from the mission profile.
- If using local Docker targets, check host port collisions before launch and remap challenge ports early.
- Read AGENTS rules for non-retentive sequential phase activation.
- Note down any major breakthroughs or attempts you've tried in a folder called `Notes/`.
- Identify one-shot endpoints/stateful resets (password reveal-once, RNG-seeded state, single-use tokens) before spending attempts.
