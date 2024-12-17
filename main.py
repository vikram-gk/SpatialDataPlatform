import uvicorn
from fastapi import FastAPI
from TalkingLandAPIs.pointAPIs import rout
from TalkingLandAPIs.multiPointAPIs import router
from TalkingLandAPIs.multiPolygonAPIs import rout1

app = FastAPI()
app.include_router(rout)
app.include_router(router)
app.include_router(rout1)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

