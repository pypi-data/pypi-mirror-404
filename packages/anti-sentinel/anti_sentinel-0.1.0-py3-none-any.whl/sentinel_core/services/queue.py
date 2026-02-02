import aiosqlite
import json
import uuid
import asyncio
from typing import Dict, Any, Optional

class QueueService:
    _instance = None
    DB_NAME = "sentinel_metrics.db" # Reusing the same DB file

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = QueueService()
        return cls._instance

    async def init_db(self):
        """Creates the jobs table."""
        async with aiosqlite.connect(self.DB_NAME) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT, -- PENDING, PROCESSING, COMPLETED, FAILED
                    input_data TEXT,
                    result TEXT,
                    created_at REAL
                )
            """)
            await db.commit()

    async def push(self, data: Dict[str, Any]) -> str:
        """Adds a job to the queue."""
        job_id = str(uuid.uuid4())
        async with aiosqlite.connect(self.DB_NAME) as db:
            await db.execute(
                "INSERT INTO jobs (job_id, status, input_data, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (job_id, "PENDING", json.dumps(data))
            )
            await db.commit()
        return job_id

    async def fetch_pending(self) -> Optional[Dict]:
        """Gets the next job to process."""
        async with aiosqlite.connect(self.DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM jobs WHERE status = 'PENDING' LIMIT 1")
            row = await cursor.fetchone()
            
            if row:
                # Mark as processing immediately so no other worker picks it up
                await db.execute("UPDATE jobs SET status = 'PROCESSING' WHERE job_id = ?", (row['job_id'],))
                await db.commit()
                return dict(row)
        return None

    async def complete(self, job_id: str, result: str):
        async with aiosqlite.connect(self.DB_NAME) as db:
            await db.execute("UPDATE jobs SET status = 'COMPLETED', result = ? WHERE job_id = ?", (result, job_id))
            await db.commit()

    async def get_status(self, job_id: str):
        async with aiosqlite.connect(self.DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None