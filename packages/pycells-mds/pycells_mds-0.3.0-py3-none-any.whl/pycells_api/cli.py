# pycells_api/cli.py

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(prog="pycells_api", description="Run PyCells FastAPI server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    args = parser.parse_args()

    uvicorn.run(
        "pycells_api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
