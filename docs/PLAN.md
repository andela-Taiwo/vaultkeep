# Plan

Vaultkeep is built in sessions, each with a clear success test. Later sessions build on
earlier ones.

| # | Session | Success |
|---|---|---|
| 1 | Throwaway test clusters and base backups: start and stop scratch Postgres instances in tests, run `pg_basebackup`, checksum and record each backup in a catalogue | A backup of a seeded cluster restores to a scratch instance with identical data; a corrupted backup file is detected by its checksum |
| 2 | WAL archiving: an `archive_command` that writes each segment atomically and verifies it, gap detection, and archive status | Under a write load, every segment from a backup's start onwards is archived once and verified; a deleted segment is reported as a gap |
| 3 | Point-in-time restore to a time, a transaction ID or a restore point, choosing the base backup and following timeline history | Rows written before the target are present and rows after are absent, across a promotion that starts a new timeline |
| 4 | Retention: keep the last N backups and daily, weekly and monthly ones, and remove only WAL that no kept backup needs | Property tests show no policy ever deletes a segment a kept backup needs; a dry run lists what would be deleted |
| 5 | Storage backends: local directory and S3-compatible storage (MinIO in tests), encryption at rest, and resumable uploads | Backups and restores pass the same tests on both backends; an interrupted upload resumes; a wrong key fails clearly |
| 6 | Restore drills and operations: scheduled drills against a scratch instance with checks, metrics, alerts, and a status page | A drill on a deliberately broken backup fails and alerts; Playwright covers the status page showing the last good restore |
| 7 | Deployment and scale: container image, a compose file and a Kubernetes CronJob, and backups of a multi-gigabyte database within a set budget | Benchmarks fail the build on regression; a full restore of the large database is timed and documented |

## Rules

- Tests start their own throwaway Postgres instances. Nothing touches a developer's database.
- A backup counts as good only after a restore of it has been checked.
- No secrets in logs, errors, URLs or the command line. Passwords come from a file or the
  environment.
- Every destructive step (retention, restore over a data directory) has a dry run and refuses
  without an explicit flag.
