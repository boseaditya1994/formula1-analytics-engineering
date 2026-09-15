"""Transactional current-state upsert and partition reconciliation."""

from pathlib import Path

from snowflake.connector.util_text import split_statements

from f1_pipeline.records import encode

SOURCE = """
SELECT value:business_key::VARCHAR AS business_key,
       value:season::NUMBER AS season, value:round_number::NUMBER AS round_number,
       value:payload AS payload, value:payload_hash::VARCHAR AS payload_hash
FROM TABLE(FLATTEN(INPUT => PARSE_JSON(%s)))
"""


def initialize(connection, sql_path: Path) -> None:
    with connection.cursor() as cursor, sql_path.open(encoding="utf-8-sig") as stream:
        for statement, _ in split_statements(stream):
            if any(
                line.strip() and not line.lstrip().startswith("--")
                for line in statement.splitlines()
            ):
                cursor.execute(statement)


def start(connection, run_id: str, dataset: str, season: int, race: int | None) -> None:
    endpoint = f"{season}/" + (f"{race}/" if race is not None else "") + f"{dataset}/"
    with connection.cursor() as q:
        q.execute(
            """INSERT INTO F1_ANALYTICS.AUDIT.INGESTION_RUNS
            (RUN_ID, DATASET, SEASON, ROUND_NUMBER, ENDPOINT, STARTED_AT, STATUS)
            VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP(),'RUNNING')""",
            (run_id, dataset, season, race, endpoint),
        )


def fail(connection, run_id: str, error_type: str) -> None:
    with connection.cursor() as q:
        q.execute(
            """UPDATE F1_ANALYTICS.AUDIT.INGESTION_RUNS
            SET STATUS='FAILED', COMPLETED_AT=CURRENT_TIMESTAMP(), ERROR_TYPE=%s
            WHERE RUN_ID=%s""",
            (error_type, run_id),
        )


def load(
    connection, run_id: str, dataset: str, season: int, race: int | None, records: list[dict]
) -> dict:
    data = encode(records)
    with connection.cursor() as q:
        q.execute("BEGIN")
        try:
            q.execute(
                """SELECT COUNT(*)-COUNT(DISTINCT BUSINESS_KEY)
                FROM F1_ANALYTICS.RAW.SOURCE_RECORDS
                WHERE DATASET=%s AND SEASON=%s""",
                (dataset, season),
            )
            if q.fetchone()[0]:
                raise ValueError("Existing RAW duplicate keys")
            q.execute(
                f"""MERGE INTO F1_ANALYTICS.RAW.SOURCE_RECORDS t
                USING ({SOURCE}) s ON t.DATASET=%s AND t.BUSINESS_KEY=s.business_key
                WHEN MATCHED AND t.PAYLOAD_HASH<>s.payload_hash THEN UPDATE SET
                    PAYLOAD=s.payload, PAYLOAD_HASH=s.payload_hash,
                    UPDATED_AT=CURRENT_TIMESTAMP(), RUN_ID=%s
                WHEN NOT MATCHED THEN INSERT
                    (DATASET,BUSINESS_KEY,SEASON,ROUND_NUMBER,PAYLOAD,PAYLOAD_HASH,
                     FIRST_INGESTED_AT,UPDATED_AT,RUN_ID)
                    VALUES (%s,s.business_key,s.season,s.round_number,s.payload,s.payload_hash,
                            CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP(),%s)""",
                (data, dataset, run_id, dataset, run_id),
            )
            inserted, updated = map(int, q.fetchone()[:2])
            # Compare the complete requested partition, including unexpected retained keys.
            q.execute(
                """SELECT COUNT(*) FROM F1_ANALYTICS.RAW.SOURCE_RECORDS
                WHERE DATASET=%s AND SEASON=%s AND (%s IS NULL OR ROUND_NUMBER=%s)""",
                (dataset, season, race, race),
            )
            raw_count = int(q.fetchone()[0])
            if raw_count != len(records):
                raise ValueError("Source-to-RAW partition count mismatch; no deletion is automatic")
            q.execute(
                f"""SELECT COUNT(*) FROM ({SOURCE}) s
                JOIN F1_ANALYTICS.RAW.SOURCE_RECORDS t
                  ON t.DATASET=%s AND t.BUSINESS_KEY=s.business_key
                 AND t.PAYLOAD_HASH=s.payload_hash""",
                (data, dataset),
            )
            if int(q.fetchone()[0]) != len(records):
                raise ValueError("Source-to-RAW hash mismatch")
            unchanged = len(records) - inserted - updated
            q.execute(
                """UPDATE F1_ANALYTICS.AUDIT.INGESTION_RUNS SET
                STATUS='SUCCESS', COMPLETED_AT=CURRENT_TIMESTAMP(), RECORDS_RECEIVED=%s,
                RECORDS_INSERTED=%s, RECORDS_UPDATED=%s, RECORDS_UNCHANGED=%s, RAW_COUNT=%s
                WHERE RUN_ID=%s""",
                (len(records), inserted, updated, unchanged, raw_count, run_id),
            )
            q.execute("COMMIT")
            return {
                "received": len(records),
                "inserted": inserted,
                "updated": updated,
                "unchanged": unchanged,
                "raw_count": raw_count,
            }
        except Exception:
            q.execute("ROLLBACK")
            raise
