from fastapi import FastAPI

from bodyos_api import __version__


def create_app() -> FastAPI:
    app = FastAPI(title="FitCrew BodyOS API", version=__version__)

    @app.get("/healthz", tags=["operations"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok", "version": f"v{__version__}"}

    return app


app = create_app()
