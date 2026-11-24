# Vaultkeep

Back up Postgres continuously, restore it to any point in time, and prove the backups work by
restoring them on a schedule.

> **Status: foundation only.** The project layout, tooling, LSN handling and WAL file naming
> exist and are tested. Base backups, WAL archiving, restore, retention, drills and
> deployment are not built yet. See [the plan](docs/PLAN.md).

## What it will do

- **Base backups** with `pg_basebackup`, checksummed, compressed, and recorded in a catalogue
  with their start and end positions in the write-ahead log.
- **WAL archiving** from `archive_command`, with no gaps: a missing segment is detected and
  reported before a restore needs it.
- **Point-in-time restore** to a timestamp, a transaction or a named restore point, choosing the
  right base backup and timeline.
- **Retention** that never deletes a WAL segment a kept backup still needs.
- **Restore drills** that restore the latest backup to a scratch instance on a schedule, run
  checks against it, and alert when a drill fails.
- **Storage** on a local directory or S3-compatible object storage, with encryption at rest.

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
