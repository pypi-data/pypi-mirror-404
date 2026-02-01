from dataclasses import dataclass

@dataclass(frozen=True)
class SyncContext:
    dry_run: bool
