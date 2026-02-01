from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.batching import batched
from core.schema import reflect_table, resolve_common_columns
from core.schema_diff import validate_schema
from core.checksum import row_checksum
from core.metrics import SyncMetrics
from core.state import load_state, save_state
import logging

logger = logging.getLogger(__name__)

def sync_table(
    ctx,
    replica_name,
    primary_engine,
    replica_engine,
    table_name,
    table_cfg,
):
    pk = table_cfg["primary_key"]
    mode = table_cfg["mode"]
    batch_size = table_cfg["batch_size"]
    mapping = table_cfg.get("column_mapping") or {}
    conflict = table_cfg.get("conflict_resolution") or {}
    checksum_cfg = table_cfg.get("checksum") or {}

    p_table = reflect_table(primary_engine, table_name)
    r_table = reflect_table(replica_engine, table_name, must_exist=False)

    cols_to_sync = set()
    cols_to_sync.add(pk)
    
    if table_cfg.get("columns_to_sync"):
        cols_to_sync.update(table_cfg["columns_to_sync"])
        
    if mapping:
        cols_to_sync.update(mapping.keys())
    if conflict.get("update_columns"):
        cols_to_sync.update(conflict["update_columns"])
    if checksum_cfg.get("enabled") and checksum_cfg.get("columns"):
        cols_to_sync.update(checksum_cfg["columns"])
    
    # If nothing specific configured, sync all columns
    if len(cols_to_sync) == 1 and not mapping and not table_cfg.get("columns_to_sync"): 
        cols_to_sync.update(p_table.columns.keys())

    # Check for schema evolution (missing columns)
    if r_table is not None:
        try:
            validate_schema(p_table, r_table, mapping)
            # Also check if all columns we WANT to sync exist in the replica
            r_cols = set(r_table.columns.keys())
            for col in cols_to_sync:
                r_col = mapping.get(col, col)
                if r_col not in r_cols:
                    raise RuntimeError(f"Missing replica column: {r_col}")
        except RuntimeError as e:
            logger.warning(f"Schema mismatch detected for {table_name}: {e}")
            if not ctx.dry_run:
                from core.schema import sync_columns
                sync_columns(replica_engine, p_table, r_table, cols_to_sync, mapping)
                # Re-reflect to get new columns
                r_table = reflect_table(replica_engine, table_name)
            else:
                logger.info(f"[DRY-RUN] Would add missing columns to table {table_name}")

    if r_table is None:
        if ctx.dry_run:
            logger.info(f"[DRY-RUN] Would create table {table_name} on {replica_name}")
            common_cols = list(cols_to_sync)
        else:
            from core.schema import create_replica_table
            r_table = create_replica_table(
                replica_engine, 
                p_table, 
                table_name, 
                list(cols_to_sync), 
                mapping
            )
            common_cols = resolve_common_columns(p_table, r_table, mapping)
    else:
        common_cols = resolve_common_columns(p_table, r_table, mapping)

    state = load_state()
    last_pk = state.get(replica_name, {}).get(table_name)

    metrics = SyncMetrics()

    with primary_engine.connect().execution_options(
        stream_results=True
    ) as p_conn, replica_engine.connect() as r_conn:

        query = select(p_table).order_by(p_table.c[pk])
        if last_pk is not None:
            query = query.where(p_table.c[pk] > last_pk)

        rows = p_conn.execute(query).mappings()

        for batch in batched(rows, batch_size):
            metrics.seen(len(batch))
            ids = [row[pk] for row in batch]

            if r_table is not None:
                existing = {
                    r[pk]: r
                    for r in r_conn.execute(
                        select(r_table).where(r_table.c[pk].in_(ids))
                    ).mappings()
                }
            else:
                existing = {}

            records = []

            for row in batch:
                record = {
                    mapping.get(col, col): row[col]
                    for col in common_cols
                }

                if checksum_cfg.get("enabled") and row[pk] in existing:
                    src = row_checksum(row, checksum_cfg["columns"])
                    dst = row_checksum(existing[row[pk]], checksum_cfg["columns"])
                    if src == dst:
                        continue

                records.append(record)

            if not records:
                continue

            if ctx.dry_run:
                logger.info(
                    f"[DRY-RUN] {table_name}: "
                    f"{len(records)} rows ({mode})"
                )
                continue

            if mode == "insert":
                r_conn.execute(r_table.insert(), records)

            elif mode == "upsert":
                # Ensure we are using the actual column names in the replica table
                stmt = pg_insert(r_table).values(records)
                
                # Resolve conflict columns to replica column names
                update_cols = [mapping.get(c, c) for c in conflict.get("update_columns", [])]
                
                stmt = stmt.on_conflict_do_update(
                    index_elements=[pk],
                    set_={
                        col: getattr(stmt.excluded, col)
                        for col in update_cols
                    }
                )
                r_conn.execute(stmt)

            metrics.written(len(records))
            r_conn.commit()

            state.setdefault(replica_name, {})[table_name] = max(ids)
            save_state(state)

    logger.info(metrics.report(table_name))
