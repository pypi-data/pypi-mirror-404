def validate_schema(primary_table, replica_table, column_mapping):
    for p_col, r_col in column_mapping.items():
        if p_col not in primary_table.columns:
            raise RuntimeError(f"Missing primary column: {p_col}")
        if r_col not in replica_table.columns:
            raise RuntimeError(f"Missing replica column: {r_col}")

        p_type = primary_table.columns[p_col].type
        r_type = replica_table.columns[r_col].type

        if p_type.__class__ != r_type.__class__:
            raise RuntimeError(
                f"Type mismatch {p_col}->{r_col}: {p_type} vs {r_type}"
            )
