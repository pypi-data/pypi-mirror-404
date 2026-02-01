from concurrent.futures import ThreadPoolExecutor
from core.syncer import sync_table

def run_parallel_sync(ctx, primary_engine, replica_engines, tables_cfg):
    futures = []
    with ThreadPoolExecutor(max_workers=len(replica_engines)) as executor:
        for replica in replica_engines:
            for table_name, cfg in tables_cfg.items():
                futures.append(
                    executor.submit(
                        sync_table,
                        ctx,
                        replica["name"],
                        primary_engine,
                        replica["engine"],
                        table_name,
                        cfg,
                    )
                )
    
    for future in futures:
        try:
            future.result()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Sync failed: {e}", exc_info=True)
