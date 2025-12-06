import os
import json
import logging
from aiohttp import web

# --- CONFIGURATION ---
PORT = int(os.environ.get("PORT", 5050))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("P2P_Transfer_100GB")

# --- FRONTEND ---
HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>100GB Secure P2P Transfer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/web-streams-polyfill@2.0.2/dist/polyfill.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/streamsaver@2.0.5/StreamSaver.min.js"></script>
    <style>
        body { background: #121212; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
        .card { background: #1e1e1e; border: 1px solid #333; }
        .btn-primary { background-color: #0d6efd; }
        #dropZone { border: 2px dashed #444; padding: 40px; text-align: center; cursor: pointer; transition: 0.2s; }
        #dropZone:hover { background-color: #252525; border-color: #0d6efd; }
        .log-box { font-family: monospace; font-size: 0.8em; color: #0f0; background: #000; padding: 10px; height: 150px; overflow-y: auto; border-radius: 5px; }
    </style>
</head>
<body>

<div class="container mt-4">
    <div class="card p-4">
        <h2 class="text-center mb-3">⚡ 100GB P2P Transfer</h2>
        
        <div id="step1">
            <div class="d-grid gap-3">
                <button class="btn btn-primary btn-lg" onclick="startSender()">I am the SENDER (Upload)</button>
                <button class="btn btn-outline-light btn-lg" onclick="startReceiver()">I am the RECEIVER (Download)</button>
            </div>
            <p class="mt-3 text-center text-muted small">
                <span id="wakeLockStatus">😴 Screen Sleep Allowed</span> | 
                <span id="fsStatus">Checking File System Support...</span>
            </p>
        </div>

        <div id="step2" style="display:none;">
            <div class="alert alert-dark text-center">
                <h4 id="roomIdDisplay"></h4>
                <div id="receiverInput" style="display:none;">
                    <input type="text" id="joinInput" class="form-control text-center mb-2" placeholder="Enter Room ID">
                    <button class="btn btn-success w-100" onclick="joinRoom()">Connect</button>
                </div>
                <div id="senderWaiting" style="display:none;">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p>Waiting for receiver...</p>
                </div>
            </div>
        </div>

        <div id="step3" style="display:none;">
            <div id="senderUI" style="display:none;">
                <div id="dropZone" onclick="document.getElementById('fileInput').click()">
                    <h3>Select File</h3>
                    <p>Click or Drag 100GB+ File Here</p>
                    <input type="file" id="fileInput" style="display: none;" onchange="handleFileSelect(this.files)">
                </div>
                <div id="fileActions" class="mt-3" style="display:none;">
                    <h5 id="fileName"></h5>
                    <p class="text-muted" id="fileSize"></p>
                    <button class="btn btn-success w-100" onclick="initiateTransfer()">Start / Resume Transfer</button>
                </div>
            </div>

            <div id="receiverUI" style="display:none;">
                <p id="receiverStatus">Waiting for sender...</p>
                <div id="resumeControl" style="display:none;" class="alert alert-warning">
                    <strong>Resumable!</strong> Sender has <span id="remoteFileName"></span>.
                    <br>
                    Current progress: <span id="currentReceived">0</span> bytes.
                    <button class="btn btn-sm btn-warning mt-2" onclick="requestResume()">Resume Download</button>
                    <button class="btn btn-sm btn-danger mt-2" onclick="requestNew()">Start New</button>
                </div>
                <!-- NEW: explicit user gesture button for save picker -->
                <button id="saveAndStartBtn" class="btn btn-success mt-3" style="display:none;" onclick="prepareSaveAndStart()">
                    Choose Save Location & Start
                </button>
            </div>

            <div class="mt-4">
                <div class="progress" style="height: 30px;">
                    <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-success" role="progressbar" style="width: 0%">0%</div>
                </div>
                <div class="d-flex justify-content-between mt-2">
                    <span id="speedDisplay">0 MB/s</span>
                    <span id="timeDisplay">--:-- left</span>
                </div>
            </div>
            
            <div id="logs" class="log-box mt-3"></div>
        </div>
    </div>
</div>

<script>
    // --- CORE VARIABLES ---
    let socket, peerConnection, dataChannel;
    let roomId;
    let selectedFile;

    let transferState = {
        offset: 0,
        fileSize: 0,
        fileName: '',
        startTime: 0,
        lastChunkTime: 0,
        lastOffset: 0   // for speed calculation
    };

    let pendingMeta = null;   // store metadata until user clicks "Choose Save Location"

    // WebRTC Configuration
    const rtcConfig = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };

    // --- WAKE LOCK (Keep Mobile Screen On) ---
    async function requestWakeLock() {
        try {
            if ('wakeLock' in navigator) {
                const lock = await navigator.wakeLock.request('screen');
                document.getElementById('wakeLockStatus').innerText = "☀️ Screen Kept Awake";
                log("Screen Wake Lock active");
            }
        } catch (err) { log("Wake Lock Error: " + err.message); }
    }

    // --- FILE SYSTEM SUPPORT CHECK ---
    const useNativeFS = ('showSaveFilePicker' in window);
    document.getElementById('fsStatus').innerText = useNativeFS ? "💾 Native Direct-Write Ready" : "💾 Using StreamSaver Polyfill";

    // --- LOGGING ---
    function log(msg) {
        const box = document.getElementById('logs');
        box.innerHTML += `<div>&gt; ${msg}</div>`;
        box.scrollTop = box.scrollHeight;
        console.log("[LOG]", msg);
    }

    function logError(msg, err) {
        const box = document.getElementById('logs');
        box.innerHTML += `<div style="color:#f55;">! ${msg}: ${err?.message || err}</div>`;
        box.scrollTop = box.scrollHeight;
        console.error("[ERROR]", msg, err);
    }

    // --- WEBSOCKET SIGNALING ---
    function connectSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${protocol}//${location.host}/ws`);

        socket.onopen = () => {
            log("Signaling socket connected");
        };

        socket.onmessage = async (e) => {
            const msg = JSON.parse(e.data);
            if (msg.type === 'peer_joined') startPeerConnection(true);
            if (msg.type === 'offer') handleOffer(msg.data);
            if (msg.type === 'answer') handleAnswer(msg.data);
            if (msg.type === 'candidate') handleCandidate(msg.data);
        };

        socket.onerror = (e) => {
            logError("WebSocket error", e);
        };

        socket.onclose = () => {
            log("WebSocket closed");
        };
    }
    connectSocket();

    // --- NAVIGATION ---
    function startSender() {
        roomId = Math.random().toString(36).substring(2, 7).toUpperCase();
        document.getElementById('step1').style.display = 'none';
        document.getElementById('step2').style.display = 'block';
        document.getElementById('senderWaiting').style.display = 'block';
        document.getElementById('roomIdDisplay').innerText = `Room ID: ${roomId}`;
        socket.send(JSON.stringify({ type: 'join', room: roomId }));
        requestWakeLock();
    }

    function startReceiver() {
        document.getElementById('step1').style.display = 'none';
        document.getElementById('step2').style.display = 'block';
        document.getElementById('receiverInput').style.display = 'block';
        requestWakeLock();
    }

    function joinRoom() {
        roomId = document.getElementById('joinInput').value.toUpperCase();
        socket.send(JSON.stringify({ type: 'join', room: roomId }));
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step3').style.display = 'block';
        document.getElementById('receiverUI').style.display = 'block';
    }

    // --- WEBRTC CONNECTION ---
    function startPeerConnection(isInitiator) {
        if (isInitiator) {
            document.getElementById('step2').style.display = 'none';
            document.getElementById('step3').style.display = 'block';
            document.getElementById('senderUI').style.display = 'block';
        }
        
        peerConnection = new RTCPeerConnection(rtcConfig);
        
        peerConnection.onicecandidate = e => {
            if (e.candidate) {
                socket.send(JSON.stringify({ type: 'candidate', room: roomId, data: e.candidate }));
            }
        };

        peerConnection.onconnectionstatechange = () => {
            log("PeerConnection state: " + peerConnection.connectionState);
        };

        if (isInitiator) {
            dataChannel = peerConnection.createDataChannel("transfer");
            setupDataChannel(dataChannel);
            peerConnection.createOffer().then(offer => {
                peerConnection.setLocalDescription(offer);
                socket.send(JSON.stringify({ type: 'offer', room: roomId, data: offer }));
            }).catch(err => logError("Create offer failed", err));
        } else {
            peerConnection.ondatachannel = e => {
                dataChannel = e.channel;
                setupDataChannel(dataChannel);
            };
        }
    }

    async function handleOffer(offer) {
        startPeerConnection(false);
        await peerConnection.setRemoteDescription(offer);
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        socket.send(JSON.stringify({ type: 'answer', room: roomId, data: answer }));
    }

    async function handleAnswer(answer) {
        await peerConnection.setRemoteDescription(answer);
    }

    async function handleCandidate(candidate) {
        try {
            await peerConnection.addIceCandidate(candidate);
        } catch (err) {
            logError("Error adding ICE candidate", err);
        }
    }

    // --- DATA CHANNEL & TRANSFER LOGIC ---
    function setupDataChannel(channel) {
        channel.binaryType = 'arraybuffer';

        channel.onopen = () => {
            log("P2P DataChannel Open!");
        };

        channel.onclose = () => {
            log("P2P DataChannel Closed");
        };

        channel.onerror = (err) => {
            logError("DataChannel error", err);
        };
        
        channel.onmessage = async (e) => {
            const data = e.data;
            if (typeof data === 'string') {
                let msg;
                try {
                    msg = JSON.parse(data);
                } catch {
                    log("Received non-JSON string: " + data);
                    return;
                }

                if (msg.type === 'request_offset') {
                    // SENDER receives offset to start from
                    startSendingChunks(msg.offset || 0);
                }
                
                if (msg.type === 'file_meta') {
                    // RECEIVER gets metadata
                    handleFileMeta(msg);
                }
            } else {
                // RECEIVER receives Binary Chunk
                await handleIncomingChunk(data);
            }
        };
    }

    // ================= SENDER LOGIC =================
    function handleFileSelect(files) {
        selectedFile = files[0];
        if (!selectedFile) return;
        document.getElementById('fileName').innerText = selectedFile.name;
        document.getElementById('fileSize').innerText = (selectedFile.size / (1024*1024*1024)).toFixed(2) + " GB";
        document.getElementById('fileActions').style.display = 'block';
        log("Selected file: " + selectedFile.name + " (" + selectedFile.size + " bytes)");
    }

    function initiateTransfer() {
        if (!selectedFile) {
            log("No file selected");
            return;
        }
        if (!dataChannel || dataChannel.readyState !== 'open') {
            log("DataChannel not ready yet. Wait for P2P connection.");
            return;
        }
        dataChannel.send(JSON.stringify({
            type: 'file_meta',
            name: selectedFile.name,
            size: selectedFile.size
        }));
        log("Metadata sent. Waiting for receiver to choose save location...");
    }

    async function startSendingChunks(offset) {
        if (!selectedFile) {
            log("No file selected on sender side.");
            return;
        }
        if (!dataChannel || dataChannel.readyState !== 'open') {
            log("DataChannel not open. Cannot start sending.");
            return;
        }

        log(`Starting transfer from offset: ${offset}`);
        transferState.offset = offset;
        transferState.startTime = Date.now();
        transferState.lastChunkTime = Date.now();
        transferState.lastOffset = offset;
        
        const CHUNK_SIZE = 64 * 1024; // 64KB

        const fileReader = new FileReader();
        
        function readNext() {
            if (transferState.offset >= selectedFile.size) {
                log("Transfer Complete!");
                return;
            }
            
            if (dataChannel.bufferedAmount > 10 * 1024 * 1024) { // 10MB backpressure
                setTimeout(readNext, 50);
                return;
            }

            const slice = selectedFile.slice(transferState.offset, transferState.offset + CHUNK_SIZE);
            fileReader.readAsArrayBuffer(slice);
        }

        fileReader.onload = (e) => {
            try {
                dataChannel.send(e.target.result);
            } catch (err) {
                logError("Error sending chunk", err);
                return;
            }
            transferState.offset += e.target.result.byteLength;
            updateProgress(transferState.offset, selectedFile.size);
            readNext();
        };

        fileReader.onerror = (e) => {
            logError("FileReader error", e);
        };

        readNext();
    }

    // ================= RECEIVER LOGIC =================
    let receivedBytes = 0;
    let writer = null;
    let usingNativeFS = useNativeFS;

    function handleFileMeta(meta) {
        // Just store metadata and show UI. DO NOT call showSaveFilePicker here.
        pendingMeta = meta;
        transferState.fileName = meta.name;
        transferState.fileSize = meta.size;
        document.getElementById('receiverStatus').innerText =
            "Incoming file: " + meta.name + " (" + meta.size + " bytes)";
        log("Received metadata: " + meta.name + " (" + meta.size + " bytes)");

        const btn = document.getElementById('saveAndStartBtn');
        btn.style.display = 'inline-block';
        btn.disabled = false;
    }

    async function prepareSaveAndStart() {
        const btn = document.getElementById('saveAndStartBtn');
        if (!pendingMeta) {
            log("No file metadata received yet.");
            return;
        }
        const meta = pendingMeta;
        btn.disabled = true;

        try {
            if (useNativeFS) {
                // IMPORTANT: this is directly triggered by user click (gesture), so it's allowed
                const handle = await window.showSaveFilePicker({ suggestedName: meta.name });
                const writable = await handle.createWritable();
                writer = writable;
                usingNativeFS = true;
                log("Save location selected (Native FS).");
            } else {
                if (window.streamSaver) {
                    const fileStream = streamSaver.createWriteStream(meta.name, { size: meta.size });
                    writer = fileStream.getWriter();
                    usingNativeFS = false;
                    log("Save location using StreamSaver fallback.");
                } else {
                    throw new Error("StreamSaver not available and Native FS not supported.");
                }
            }

            receivedBytes = 0;
            transferState.offset = 0;
            transferState.startTime = Date.now();
            transferState.lastChunkTime = Date.now();
            transferState.lastOffset = 0;
            pendingMeta = null;

            requestResume();   // now tell sender to start
        } catch (e) {
            btn.disabled = false;
            logError("File save cancelled or failed", e);
            alert("Failed to open save file dialog. Check browser permissions / context (use Chrome on https:// or localhost).");
        }
    }

    function requestResume() {
        if (!dataChannel || dataChannel.readyState !== 'open') {
            log("Cannot request resume: DataChannel not open yet.");
            return;
        }
        log("Requesting resume from offset " + receivedBytes);
        dataChannel.send(JSON.stringify({ type: 'request_offset', offset: receivedBytes }));
    }

    function requestNew() {
        receivedBytes = 0;
        transferState.offset = 0;
        updateProgress(0, transferState.fileSize || 1);
        requestResume();
    }

    async function handleIncomingChunk(buffer) {
        if (!writer) {
            logError("Writer not initialized on receiver side yet", "");
            return;
        }

        try {
            if (usingNativeFS) {
                await writer.write(buffer);  // sequential write
            } else {
                await writer.write(new Uint8Array(buffer));
            }
        } catch (err) {
            logError("Write failed (receiver). This is likely the 'failed save' you saw", err);
            alert("Write failed while saving file. See logs for details.");
            return;
        }
        
        receivedBytes += buffer.byteLength;
        document.getElementById('currentReceived').innerText = receivedBytes;
        updateProgress(receivedBytes, transferState.fileSize);

        if (receivedBytes >= transferState.fileSize) {
            log("Download Finished.");
            try {
                if (usingNativeFS) {
                    await writer.close();
                } else {
                    writer.close();
                }
                log("File stream closed successfully.");
            } catch (err) {
                logError("Error closing writer", err);
            }
        }
    }

    // --- UTILS ---
    function updateProgress(current, total) {
        total = total || 1;
        const percent = ((current / total) * 100).toFixed(2);
        const bar = document.getElementById('progressBar');
        bar.style.width = percent + '%';
        bar.innerText = percent + '%';
        
        const now = Date.now();
        if (!transferState.lastChunkTime) {
            transferState.lastChunkTime = now;
            transferState.lastOffset = current;
        }

        const dt = (now - transferState.lastChunkTime) / 1000;
        const dBytes = current - transferState.lastOffset;

        if (dt > 0.5) {
            const speedMB = dBytes / (1024 * 1024) / dt;
            if (!isNaN(speedMB) && isFinite(speedMB)) {
                document.getElementById('speedDisplay').innerText = speedMB.toFixed(2) + " MB/s";
            }
            transferState.lastChunkTime = now;
            transferState.lastOffset = current;

            const remainingBytes = total - current;
            if (speedMB > 0) {
                const remainingSec = remainingBytes / (1024 * 1024) / speedMB;
                const minutes = Math.floor(remainingSec / 60);
                const seconds = Math.floor(remainingSec % 60);
                document.getElementById('timeDisplay').innerText =
                    `${minutes}:${seconds.toString().padStart(2, '0')} left`;
            } else {
                document.getElementById('timeDisplay').innerText = "--:-- left";
            }
        }
    }

    // --- Drag & Drop Support for Sender ---
    const dropZone = document.getElementById('dropZone');
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-primary');
    });
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary');
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files);
        }
    });

</script>
</body>
</html>
"""

# --- BACKEND ---
async def index(request):
    return web.Response(text=HTML_CONTENT, content_type='text/html')

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    room_id = None
    app = request.app

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)

                if data.get('type') == 'join':
                    room_id = data.get('room')
                    if room_id not in app['rooms']:
                        app['rooms'][room_id] = []
                    app['rooms'][room_id].append(ws)
                    logger.info("Client joined room %s (total %d)", room_id, len(app['rooms'][room_id]))

                    if len(app['rooms'][room_id]) == 2:
                        for c in app['rooms'][room_id]:
                            if c != ws:
                                await c.send_json({'type': 'peer_joined'})
                else:
                    if room_id and room_id in app['rooms']:
                        for c in app['rooms'][room_id]:
                            if c != ws:
                                await c.send_json(data)

    finally:
        if room_id and room_id in app['rooms']:
            if ws in app['rooms'][room_id]:
                app['rooms'][room_id].remove(ws)
                logger.info("Client left room %s (remaining %d)", room_id, len(app['rooms'][room_id]))
            if not app['rooms'][room_id]:
                del app['rooms'][room_id]

    return ws

app = web.Application()
app['rooms'] = {}
app.add_routes([web.get('/', index), web.get('/ws', websocket_handler)])

if __name__ == '__main__':
    web.run_app(app, host="0.0.0.0", port=PORT)

