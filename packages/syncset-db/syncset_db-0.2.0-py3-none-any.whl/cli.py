import argparse
import yaml
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from core.engine import create_db_engine
from core.context import SyncContext
from core.worker import run_parallel_sync

def main():
    parser = argparse.ArgumentParser(description="SyncSet Database Replication Tool")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making actual changes")
    parser.add_argument("--file", "-f", default="config/sync.yaml", help="Path to the sync configuration file (default: config/sync.yaml)")
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        import sys
        print(f"Error: Configuration file not found at '{args.file}'.")
        print("Please provide a valid file using the --file flag or ensure 'config/sync.yaml' exists.")
        sys.exit(1)

    ctx = SyncContext(dry_run=args.dry_run)

    primary_engine = create_db_engine(cfg["primary_db"]["url"])

    replica_engines = [
        {
            "name": r["name"],
            "engine": create_db_engine(r["url"]),
        }
        for r in cfg["replica_dbs"]
    ]

    run_parallel_sync(
        ctx,
        primary_engine,
        replica_engines,
        cfg["tables"],
    )

if __name__ == "__main__":
    main()
