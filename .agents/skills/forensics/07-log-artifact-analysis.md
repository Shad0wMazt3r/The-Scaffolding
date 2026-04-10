## Log & Artifact Analysis

- Primary Probe
  - * -> [Condition: Windows artifacts exist] -> Action: pull Event Logs from `%SystemRoot%\\System32\\winevt\\Logs\\`, Registry hives from `Windows\\System32\\config\\`, user hives from `NTUSER.DAT`/`UsrClass.dat`, Prefetch from `Windows\\Prefetch\\`, and browser data from Chromium/Edge/Firefox profiles.
  - * -> [Condition: Linux artifacts exist] -> Action: inspect `/var/log/`, `/var/log/journal/`, shell histories, cron/anacron, systemd units, SSH keys, `.bash_history`, `.zsh_history`, and package manager logs.
  - * -> [Condition: macOS artifacts exist] -> Action: inspect Unified Logs, `~/Library/Preferences/`, browser SQLite stores, LaunchAgents/Daemons, recent items, quarantine events, and FSEvents.

- Dead End Pivots
  - * -> [Condition: Event coverage is sparse or wiped] -> Action: recover `.evtx` from unallocated space, compare hive transaction logs, and use Prefetch/LNK/Jump Lists to backfill execution.
  - * -> [Condition: Browser history is cleared] -> Action: mine cache, session restore files, cookies, downloads DBs, favicons, and recovered SQLite freelists.
  - * -> [Condition: Registry or syslog evidence is partial] -> Action: correlate USB, network profile, MRU, Run/RunOnce, service, and SSH known_hosts artifacts to rebuild operator behavior.

- Data Chaining
  - * -> [Condition: Logon or service creation appears] -> Action: pivot to PCAP lateral-movement windows and memory-resident service processes.
  - * -> [Condition: Downloaded filename or URL is found] -> Action: search the disk image, then match network transfer and execution evidence.
  - * -> [Condition: Browser token, cookie, or form fill is recovered] -> Action: test it against web session replay, archive passwords, or challenge portals.

- Simple one-liners
  - `sqlite3 'History' 'select datetime(last_visit_time/1000000-11644473600,"unixepoch"),url,title from urls order by last_visit_time desc;'`
  - `find mount/ -iname '*.evtx' -o -iname 'NTUSER.DAT' -o -iname 'UsrClass.dat' > logs/artifact_paths.txt`
  - `grep -RinE 'flag\\{|ctf\\{|pass|token|key' mount/Users mount/home 2>/dev/null > logs/keyword_hits.txt`

