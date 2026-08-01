import asyncio
import os
import json
import logging
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SendWitchServer")

app = FastAPI(title="SendWitch P2P Signaling Server")

# In-memory session store
# code -> { "sender": WebSocket, "receiver": WebSocket }
sessions: Dict[str, Dict[str, Optional[WebSocket]]] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    assigned_code: Optional[str] = None
    role: Optional[str] = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON message")
                continue

            action = msg.get("action")
            code = msg.get("code")

            if action == "register_sender":
                if not code:
                    await websocket.send_json({"type": "error", "message": "No transfer code provided."})
                    continue

                code = code.strip().lower()

                # Cleanup previous session if any with same code
                if code in sessions:
                    old_sess = sessions[code]
                    if old_sess.get("sender") and old_sess["sender"] != websocket:
                        try:
                            await old_sess["sender"].send_json({"type": "error", "message": "Code re-registered elsewhere."})
                        except Exception:
                            pass
                
                sessions[code] = {
                    "sender": websocket,
                    "receiver": None
                }
                assigned_code = code
                role = "sender"
                logger.info(f"Registered SENDER for code: {code}")
                await websocket.send_json({"type": "registered", "code": code})

            elif action == "connect_receiver":
                if not code:
                    await websocket.send_json({"type": "error", "message": "No transfer code provided."})
                    continue

                code = code.strip().lower()

                if code not in sessions or not sessions[code].get("sender"):
                    await websocket.send_json({"type": "error", "message": "Invalid or expired transfer code. Sender not found."})
                    continue

                session = sessions[code]
                session["receiver"] = websocket
                assigned_code = code
                role = "receiver"
                logger.info(f"Connected RECEIVER for code: {code}")

                # Notify both peers
                await session["receiver"].send_json({"type": "peer_connected", "role": "sender"})
                await session["sender"].send_json({"type": "peer_connected", "role": "receiver"})

            elif action == "signal":
                if not assigned_code or assigned_code not in sessions:
                    await websocket.send_json({"type": "error", "message": "Not in an active session."})
                    continue

                session = sessions[assigned_code]
                target_ws = session["receiver"] if role == "sender" else session["sender"]

                if target_ws:
                    try:
                        await target_ws.send_json({
                            "type": "signal",
                            "data": msg.get("data")
                        })
                    except Exception as e:
                        logger.error(f"Error relaying signal: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: role={role}, code={assigned_code}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
    finally:
        if assigned_code and assigned_code in sessions:
            session = sessions[assigned_code]
            if role == "sender" and session.get("sender") == websocket:
                session["sender"] = None
                if session.get("receiver"):
                    try:
                        await session["receiver"].send_json({"type": "peer_disconnected", "role": "sender"})
                    except Exception:
                        pass
            elif role == "receiver" and session.get("receiver") == websocket:
                session["receiver"] = None
                if session.get("sender"):
                    try:
                        await session["sender"].send_json({"type": "peer_disconnected", "role": "receiver"})
                    except Exception:
                        pass

            # If both disconnected, clean up session
            if not session.get("sender") and not session.get("receiver"):
                del sessions[assigned_code]
                logger.info(f"Cleaned up session for code: {assigned_code}")

@app.get("/")
async def get_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
