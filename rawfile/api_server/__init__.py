from consts import PROVISIONER_VERSION
from fastapi import FastAPI
from api_server.v1.routes import router as v1_router

app = FastAPI(
    debug=False, title="RawFile LocalPV API Server", version=PROVISIONER_VERSION
)
app.include_router(v1_router, prefix="/v1", tags=["v1"])


def start_server(host, workers, port):
    import uvicorn

    uvicorn.run("api_server:app", host=host, port=port, workers=workers)
