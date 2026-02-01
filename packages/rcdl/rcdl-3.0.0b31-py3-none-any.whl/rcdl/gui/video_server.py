# gui/video_server.py

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# FIX: Allow the browser to load videos from a different port (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (safe for local/homelab use)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/video")
async def get_video(path: str = Query(...)):
    real_path = path

    if not os.path.isfile(real_path):
        return {"error": "File not found"}, 404

    return FileResponse(
        real_path,
        media_type="video/mp4",
        # FileResponse automatically handles Range headers,
        # but explicit Accept-Ranges is good practice.
        headers={
            "Accept-Ranges": "bytes",
        },
    )
