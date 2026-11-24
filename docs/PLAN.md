# Plan

Vaultkeep is built in sessions, each with a clear success test. Later sessions build on
earlier ones. Crash-safe archiving comes first, because an archive with a silent gap cannot
be rescued by anything built on top of it.

## How correctness is proven

Green unit tests are necessary but not enough. Three things must hold:

- **Postgres is the referee.** LSN and segment names are checked against `pg_walfile_name`,
  archive continuity against `pg_waldump`, backups against `pg_controldata` and
  `pg_verifybackup`, and restores against real recovery with a ground-truth workload that
  records exactly what committed and when.
- **Crash-state coverage.** The archiver writes through a storage interface. A simulated
  filesystem records every operation, models what is durable and what is only cached, and at
  every crash point enumerates every on-disk state a crash could leave. The invariants are
  checked in each one:
  - nothing Postgres considers archived is missing or different;
  - no partial file sits under a final name;
  - a retry after the crash is idempotent.
- **Planted bugs.** Deliberately broken archivers (fsync dropped before rename, success
  returned before the write, directory fsync skipped, overwrite on mismatch) must each fail a
  test. Each planted bug stays as a permanent test. A harness that has never caught one proves
  nothing.

Every claim says which layer proved it: the simulation (the protocol is right under the
durability model) or the real system (the code does what the model assumes).

## Sessions

| # | Session | Success |
|---|---|---|
| 1 | Test clusters and base backups: throwaway Postgres clusters that tests always clean up; a workload generator that records what committed and when; base backups with a catalogue, checksums and `pg_verifybackup` | A backup restores with identical data; a corrupted file is caught; `pg_controldata` agrees with the catalogue |
| 2 | Crash-safe archiving on a simulated filesystem: temporary name, fsync file, rename, fsync directory; idempotent retries; `.partial` segments and history files; gap detection | Full crash-state coverage passes at every crash point; every planted bug is caught; archive continuity matches `pg_waldump` on real segments |
| 3 | Fault harness on the real system: SIGKILL at named fault points, `pg_ctl stop -m immediate` under load, injected disk-full and I/O errors, seeded campaigns that replay from their seed, longer randomised runs | After every fault, every segment Postgres marked done is in the archive byte for byte, no partial file has a final name, and a full recovery matches the ground truth |
| 4 | Restore: latest point first, then to a time, a transaction or a named restore point | On real recovery, the restored rows are exactly those committed before the target, including targets on segment boundaries |
| 5 | Timeline-aware restore planner: promotions, history files, choosing the base backup and timeline path, targets on an old timeline after a promotion | Tested on real promotions; unreachable targets are refused with the reason |
| 6 | Retention and drills: keep-last-N plus daily, weekly and monthly policies; scheduled restore drills against scratch clusters with checks | Property tests show no policy deletes a segment a kept backup needs; a dry run lists what would go; a drill on a damaged backup fails and reports it |
| 7 | Corruption and hardening: damaged backups and segments detected before a restore needs them; a database as large as the disk allows; an operator's runbook | Every kind of planted damage is reported with its location; backup and restore times are measured and documented; benchmarks fail the build on regression |

## Out of scope

Object storage (S3), container images, Kubernetes and a web status page. None could be
verified here, and none is the hard part. The storage interface leaves room for object
storage later. Status and reports are a CLI with JSON output and metrics in text format.

## Rules

- Tests start their own throwaway Postgres instances. Nothing touches a developer's database.
- A backup counts as good only after a restore of it has been checked.
- The simulated filesystem models conservative POSIX durability: nothing is durable until
  fsynced, and a rename is not durable until its directory is. No reliance on one
  filesystem's ordering.
- SIGKILL is not power loss. Power-loss durability is claimed only from crash-state coverage.
- No secrets in logs, errors, URLs or the command line.
- Every destructive step (retention, restore over a data directory) has a dry run and refuses
  without an explicit flag.
