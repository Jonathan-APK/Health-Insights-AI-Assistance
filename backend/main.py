# Load application settings early; this reads from the environment (or
# .env in local development).
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from api.routes import chat, health
from config.settings import settings
from core.session import SessionManager

# Configure logging globally
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s\n",
)
logger = logging.getLogger("main")


def create_app(include_chat_routes: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        if not settings.is_production:
            load_dotenv(override=True)

        if include_chat_routes:
            # make sure the OpenAI key is available to downstream libraries
            os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)

            # Create a Redis client using whatever URL the environment provides.
            redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            app.state.session_manager = SessionManager(
                redis_client, ttl=settings.SESSION_TTL_SECONDS
            )

            # Build graph once
            app.state.graph = chat.build_graph()
            print(app.state.graph.get_graph().draw_ascii())

        yield  # <-- app running after startup

        # Shutdown
        if include_chat_routes:
            await app.state.session_manager.redis.close()

    # Create FastAPI app with production-safe defaults. Swagger/OpenAPI
    # endpoints and documentation are disabled when ENV=production so the
    # exposed attack surface is minimal.
    app = FastAPI(
        title="Health Insights AI",
        description="AI-powered medical document analysis and health Q&A",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.FRONTEND_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Session-ID"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "details": str(exc)},
        )

    app.include_router(
        health.router,
        prefix="/v1",
        tags=["health"],
    )

    # Include chat routes only when full backend behavior is requested.
    if include_chat_routes:
        app.include_router(
            chat.router,
            prefix="/v1",
            tags=["chat"],
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
