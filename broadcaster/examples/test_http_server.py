from fastapi import FastAPI

app = FastAPI()


@app.post("/webhook")
async def webhook(data: dict):
    print("Received:", data)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
