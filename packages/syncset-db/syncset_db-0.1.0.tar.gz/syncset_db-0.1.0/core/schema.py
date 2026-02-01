from sqlalchemy import MetaData, Table, inspect, Column
import logging

logger = logging.getLogger(__name__)

def reflect_table(engine, table_name: str, must_exist: bool = True) -> Table:
    metadata = MetaData()
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        if must_exist:
            raise RuntimeError(f"Table {table_name} does not exist in {engine.url}")
        return None
    return Table(table_name, metadata, autoload_with=engine)

def drop_table(engine, table_name: str):
    metadata = MetaData()
    table = Table(table_name, metadata)
    logger.info(f"Dropping table {table_name}")
    table.drop(engine, checkfirst=True)

def sync_columns(engine, p_table, r_table, cols_to_sync, column_mapping):
    """Adds missing columns and indexes to the replica table using ALTER TABLE."""
    r_cols = set(r_table.columns.keys())
    
    with engine.connect() as conn:
        for p_col_name in cols_to_sync:
            r_col_name = column_mapping.get(p_col_name, p_col_name)
            if r_col_name not in r_cols:
                p_col = p_table.c[p_col_name]
                type_str = p_col.type.compile(engine.dialect)
                
                constraints = []
                if not p_col.nullable:
                    constraints.append("NOT NULL")
                
                if p_col.server_default is not None:
                    default_val = p_col.server_default.arg
                    if hasattr(default_val, "text"):
                        default_str = f"DEFAULT {default_val.text}"
                    else:
                        default_str = f"DEFAULT {default_val}"
                    constraints.append(default_str)
                
                constraint_str = " ".join(constraints)
                query = f'ALTER TABLE "{r_table.name}" ADD COLUMN "{r_col_name}" {type_str} {constraint_str}'.strip()
                
                logger.info(f"Executing: {query}")
                from sqlalchemy import text
                conn.execute(text(query))
        
        # Sync indexes
        for idx in p_table.indexes:
            # Check if all columns in the index are being synced
            p_idx_cols = [c.name for c in idx.columns]
            if all(c in cols_to_sync for c in p_idx_cols):
                r_idx_cols = [column_mapping.get(c, c) for c in p_idx_cols]
                r_idx_name = f"idx_{r_table.name}_{'_'.join(r_idx_cols)}"
                
                # Check if index exists on replica
                inspector = inspect(engine)
                existing_indexes = [i["name"] for i in inspector.get_indexes(r_table.name)]
                
                if r_idx_name not in existing_indexes:
                    col_list = ", ".join([f'"{c}"' for c in r_idx_cols])
                    unique = "UNIQUE" if idx.unique else ""
                    query = f'CREATE {unique} INDEX "{r_idx_name}" ON "{r_table.name}" ({col_list})'.replace("  ", " ")
                    logger.info(f"Executing: {query}")
                    from sqlalchemy import text
                    conn.execute(text(query))

        conn.commit()

def create_replica_table(replica_engine, primary_table, table_name, columns_to_sync, column_mapping):
    metadata = MetaData()
    
    table_cols = []
    # copy cols
    for col_name in columns_to_sync:
        p_col = primary_table.c[col_name]
        r_col_name = column_mapping.get(col_name, col_name)
        
        new_col = Column(
            r_col_name, 
            p_col.type, 
            primary_key=p_col.primary_key,
            nullable=p_col.nullable,
            server_default=p_col.server_default,
            unique=p_col.unique,
            index=p_col.index
        )
        table_cols.append(new_col)
    
    r_table = Table(table_name, metadata, *table_cols)
    
    # copy indexes
    for idx in primary_table.indexes:
        p_idx_cols = [c.name for c in idx.columns]
        if all(c in columns_to_sync for c in p_idx_cols):
            r_idx_cols = [r_table.c[column_mapping.get(c, c)] for c in p_idx_cols]
            from sqlalchemy import Index
            Index(f"idx_{table_name}_{'_'.join([c.name for c in r_idx_cols])}", *r_idx_cols, unique=idx.unique)

    logger.info(f"Creating table {table_name} on replica")
    metadata.create_all(replica_engine)
    return r_table

def resolve_common_columns(primary_table, replica_table, column_mapping):
    p_cols = set(primary_table.columns.keys())
    r_cols = set(replica_table.columns.keys())

    # If replica_table not yet created, we use mapped columns or all primary columns
    if replica_table is None:
        if column_mapping:
            return set(column_mapping.keys())
        return p_cols

    inferred = p_cols & r_cols
    mapped = set(column_mapping.keys())

    return inferred | mapped
