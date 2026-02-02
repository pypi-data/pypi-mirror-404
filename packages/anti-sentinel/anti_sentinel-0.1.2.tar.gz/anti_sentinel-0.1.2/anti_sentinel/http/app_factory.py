from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from anti_sentinel.container import ServiceContainer
from typing import Callable, Optional
from fastapi.staticfiles import StaticFiles
import os

class AppFactory:
    """
    Creates and configures the FastAPI application.
    """

    @staticmethod
    def create_app(settings: dict, lifespan: Optional[Callable] = None) -> FastAPI:
        # 1. Create the FastAPI instance with LIFESPAN support
        app = FastAPI(
            title=settings.get("app_name", "Sentinel App"),
            version=settings.get("version", "0.1.0"),
            debug=settings.get("debug", False),
            lifespan=lifespan # <--- PASSING THE LIFESPAN HERE
        )

        # 2. Setup CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        docs_path = os.path.join(os.getcwd(), "framework-docs")

        print(f"🔎 Checking for docs at: {docs_path}")

        if os.path.exists(docs_path):
            app.mount("/framework-docs", StaticFiles(directory=docs_path, html=True), name="framework-docs")
            print("📚 Framework Manual available at: /framework-docs/")
        else:
            print("⚠️ Framework docs not found in project root.")

        # 3. Inject Container
        app.state.container = ServiceContainer.get_instance()

        @app.get("/health")
        async def health_check():
            return {"status": "active", "system": "Sentinel Framework"}

        return app
    