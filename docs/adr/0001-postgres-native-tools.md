# 0001: Build on Postgres's own backup tools

## Status

Accepted

## Context

Postgres ships everything needed for physical backup and point-in-time recovery:
`pg_basebackup` for base backups, `archive_command` for shipping write-ahead log segments,
and `restore_command` with recovery targets for replay. Tools such as pgBackRest and WAL-G
build on the same pieces. Writing a new backup format would be a large risk with no benefit,
and a backup tool's worst failure is a restore that silently stops early.

## Decision

- Base backups come from `pg_basebackup`; WAL comes from `archive_command`; restore uses
  Postgres's own recovery with a generated `restore_command`.
- Vaultkeep owns the catalogue, verification, retention, storage, scheduling and drills.
- WAL positions and file names are computed exactly as Postgres does (`vaultkeep.lsn`,
  `vaultkeep.walnames`) and checked against a real server in tests.

## Consequences

- Restores are as reliable as Postgres's own recovery, and an operator can restore by hand
  with standard tools if Vaultkeep is unavailable.
- Tests need the Postgres server binaries (`initdb`, `pg_ctl`, `pg_basebackup`) on the path.
- Logical backups (`pg_dump`) are out of scope; the README says where they are still the
  right tool.
