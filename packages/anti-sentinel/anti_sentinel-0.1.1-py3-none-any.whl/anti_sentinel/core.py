# Copyright 2026 Sentinel Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uvicorn
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI

from .config import ConfigLoader
from .container import ServiceContainer
from .http.app_factory import AppFactory
from .http.router import register_routes
from .services.metrics import MetricsService
from .http.middleware import SentinelMetricsMiddleware
from .http.dashboard import router as dashboard_router

class SentinelApp:
    def __init__(self, config_file: str = "sentinel.yaml"):
        # 1. Force load environment variables
        from pathlib import Path
        env_path = Path.cwd() / ".env"
        load_dotenv(dotenv_path=env_path)

        print(f"🛡️  Initializing Sentinel (Env Path: {env_path})...")
        
        # 2. Load Config & Container
        self.config_loader = ConfigLoader(config_file)
        self.settings = self.config_loader.load()
        self.container = ServiceContainer.get_instance()
        
        # 3. Register Providers
        self.container.register_provider_by_config(self.settings)
        self.container.register_memory_by_config(self.settings)

        # 4. Initialize Services (FIXES ATTRIBUTE ERROR)
        self.metrics_service = MetricsService.get_instance()
        
        # 5. Create FastAPI App using the Lifespan Context Manager
        self.http_app = AppFactory.create_app(self.settings, lifespan=self.lifespan)
        
        # 6. Register Middleware & Routes
        self.http_app.add_middleware(SentinelMetricsMiddleware)
        self.http_app.include_router(dashboard_router)
        register_routes(self.http_app, package_name="app.http")
        
        print(f"✅ Sentinel Loaded. App: {self.config_loader.get('app_name')}")

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        # --- STARTUP ---
        print("📊 Initializing Databases...")
        
        # Init Metrics DB
        await self.metrics_service.init_db()
        
        # Init Queue DB
        from .services.queue import QueueService
        self.queue_service = QueueService.get_instance()
        await self.queue_service.init_db()
        
        # START WORKER (Run as a background task)
        import asyncio
        from .worker import start_worker
        # We store the task so we can cancel it later if needed
        worker_task = asyncio.create_task(start_worker())
        
        print("✅ Sentinel System Ready.")
        
        yield
        
        # --- SHUTDOWN ---
        print("🛑 Sentinel is shutting down...")
        worker_task.cancel()

    def boot(self):
        print("🚀 Sentinel is booting up components...")
        
        host = self.settings.get("server", {}).get("host", "127.0.0.1")
        port = self.settings.get("server", {}).get("port", 8000)
        
        print(f"🌍 Server starting at http://{host}:{port}")
        uvicorn.run(self.http_app, host=host, port=port)