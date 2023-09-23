"""This module contains the principal class to collect the results of the tests.
"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/v1/execution-tasks/{execution_id}")
def post_results(execution_id: str):
    print("Received results for execution task:", execution_id)
    return {"item_id": execution_id}

# uvicorn main:app --reload


def start_server(http_host: str = "127.0.0.1", http_port: int = 8000):
    import uvicorn
    uvicorn.run(app=app, host=http_host, port=http_port)


if __name__ == '__main__':
    start_server()
