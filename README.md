# Vaultkeep

Back up Postgres continuously, restore it to any point in time, and prove the backups work by
restoring them on a schedule.

> **Status: foundation only.** The project layout, tooling, LSN handling and WAL file naming
> exist and are tested. Base backups, crash-safe archiving, the fault harness, restore,
> the timeline planner, retention and drills are not built yet. See [the plan](docs/PLAN.md).

## What it will do

- **Base backups** with `pg_basebackup`, checksummed, verified with `pg_verifybackup`, and
  recorded in a catalogue with their start and end positions in the write-ahead log.
- **Crash-safe WAL archiving** from `archive_command`: atomic, verified and idempotent, so no
  crash at any point leaves a gap or a corrupt file under a final name. Gaps are detected
  long before a restore needs the missing segment.
- **Point-in-time restore** to a timestamp, a transaction or a named restore point, choosing
  the right base backup and timeline path across promotions.
- **Retention** that never deletes a WAL segment a kept backup still needs.
- **Restore drills** that restore the latest backup to a scratch instance on a schedule, run
  checks against it, and fail loudly when a drill fails.
- **Reports** from a CLI, as JSON and metrics in text format.

## How it is proven

- **Postgres is the referee**: names and positions against `pg_walfile_name`, archive
  continuity against `pg_waldump`, backups against `pg_controldata` and `pg_verifybackup`,
  restores against real recovery with a workload that records exactly what committed.
- **Crash-state coverage**: the archiver writes through a storage interface, and a simulated
  filesystem checks every on-disk state a crash could leave, at every crash point.
- **Planted bugs**: deliberately broken archivers must each fail a test.
- **Real faults**: processes killed at named points, Postgres stopped immediately under load,
  disk-full and I/O errors, in seeded campaigns that replay exactly.

Out of scope: object storage, container images, Kubernetes and a web UI. See
[the plan](docs/PLAN.md) for why.

Logical backups (`pg_dump`) are also out of scope. They remain the right tool for copying a
single database or moving data between major Postgres versions.

## What exists today

| Module | What it does |
|---|---|
| `vaultkeep.lsn` | Parses, formats, compares and subtracts log sequence numbers (`16/B374D848`) |
| `vaultkeep.walnames` | WAL segment and timeline history file names, for any segment size Postgres allows |

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12. Later sessions need PostgreSQL 14
or newer with its client tools.

```bash
make setup   # install locked dependencies
make check   # lint, format check, type check and tests
make help    # list every target
```

## Licence

MIT. See [LICENSE](LICENSE).
