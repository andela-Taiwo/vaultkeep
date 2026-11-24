# 0002: Crash-safe archiving, proven on a simulated filesystem

## Status

Accepted

## Context

When `archive_command` returns success, Postgres marks the segment done and may recycle it.
If the archived copy was not durable, or a half-written file sits under its final name, the
loss is silent until a restore stops early at the gap.

Archiving code is a "looks right" trap. An archiver that forgets one fsync passes every test
that kills the process, because a killed process's writes survive in the page cache. Only a
power loss shows the bug, and that cannot be tested on this machine.

## Decision

- **Protocol.** Write to a temporary name in the archive directory, fsync the file, rename it
  to the final name, then fsync the directory. Report success only after all four.
- **Idempotency.** Postgres may archive a segment again after a crash. If the existing file
  is byte-identical, succeed without writing. If it differs, fail loudly and never overwrite.
- **Storage interface.** All archive I/O goes through an interface with two backends: the real
  local filesystem, and a simulated filesystem used in tests.
- **Simulated filesystem.** It records every write, fsync, rename and directory fsync, and
  tracks what is durable. At any crash point it produces every on-disk state the conservative
  POSIX model allows: unsynced data lost or partly kept, and a rename present or absent until
  its directory is synced. The archive invariants are checked in every state.
- **Planted bugs.** Broken archivers live in the test suite and must each fail. The simulation
  is trusted only because it catches them.
- **Real-system tests** (session 3) check what the model assumes: that the code really issues
  the fsyncs, and that Postgres retries the way the model expects.

## Consequences

- Durability claims rest on the model and on planted bugs, and the docs say so.
- Postgres's own writes are not modelled; they are covered by real recovery against the
  ground-truth workload.
- Crash-state enumeration grows with the number of unsynced operations, so the protocol keeps
  that number small, which is also good design.
