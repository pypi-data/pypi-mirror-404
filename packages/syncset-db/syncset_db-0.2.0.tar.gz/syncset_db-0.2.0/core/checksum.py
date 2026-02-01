import hashlib

def row_checksum(row: dict, columns: list[str]) -> str:
    payload = "|".join(str(row[col]) for col in columns)
    return hashlib.sha256(payload.encode()).hexdigest()
