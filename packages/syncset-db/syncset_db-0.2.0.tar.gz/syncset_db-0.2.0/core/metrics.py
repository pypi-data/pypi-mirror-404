import time

class SyncMetrics:
    def __init__(self):
        self.start = time.time()
        self.rows_seen = 0
        self.rows_written = 0

    def seen(self, n: int):
        self.rows_seen += n

    def written(self, n: int):
        self.rows_written += n

    def report(self, table: str):
        elapsed = time.time() - self.start
        rps = self.rows_seen / elapsed if elapsed else 0
        return {
            "table": table,
            "rows_seen": self.rows_seen,
            "rows_written": self.rows_written,
            "elapsed_sec": round(elapsed, 2),
            "rows_per_sec": round(rps, 2),
        }
