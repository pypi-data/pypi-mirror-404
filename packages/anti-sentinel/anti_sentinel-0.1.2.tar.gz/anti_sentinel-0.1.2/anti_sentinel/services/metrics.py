import aiosqlite
import time
import json
from pathlib import Path

class MetricsService:
    _instance = None
    DB_NAME = "sentinel_metrics.db"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MetricsService()
        return cls._instance

    async def init_db(self):
        """Creates the metrics table if it doesn't exist."""
        async with aiosqlite.connect(self.DB_NAME) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT,
                    method TEXT,
                    status_code INTEGER,
                    latency_ms REAL,
                    timestamp REAL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT,
                    tool_used TEXT,
                    input TEXT,
                    output TEXT,
                    timestamp REAL
                )
            """)
            await db.commit()

    async def log_request(self, endpoint: str, method: str, status: int, latency: float):
        """Logs an API request."""
        async with aiosqlite.connect(self.DB_NAME) as db:
            await db.execute(
                "INSERT INTO requests (endpoint, method, status_code, latency_ms, timestamp) VALUES (?, ?, ?, ?, ?)",
                (endpoint, method, status, latency, time.time())
            )
            await db.commit()

    async def get_stats(self):
        """Fetches raw stats for the dashboard."""
        async with aiosqlite.connect(self.DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            
            # Get last 10 requests
            cursor = await db.execute("SELECT * FROM requests ORDER BY id DESC LIMIT 10")
            recent_requests = [dict(row) for row in await cursor.fetchall()]
            
            # Get average latency
            cursor = await db.execute("SELECT AVG(latency_ms) as avg_lat FROM requests")
            avg_latency = (await cursor.fetchone())[0] or 0
            
            return {
                "recent_requests": recent_requests,
                "avg_latency": round(avg_latency, 2),
                "total_requests": len(recent_requests) # simplistic count
            }