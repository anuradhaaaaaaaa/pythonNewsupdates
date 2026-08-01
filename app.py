import os
import json
import logging
from aiohttp import web

# --- CONFIGURATION ---
PORT = int(os.environ.get("PORT", 5050))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("P2P_ShinChan_Transfer")

# --- FRONTEND ---
HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shin-Chan's Super Transfer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&display=swap" rel="stylesheet">
    
    <script src="https://cdn.jsdelivr.net/npm/web-streams-polyfill@2.0.2/dist/polyfill.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/streamsaver@2.0.5/StreamSaver.min.js"></script>

    
</head>
<body>

<div style="position:absolute; top: 10px; left: 10px; font-size: 4rem;">⭐</div>
<div style="position:absolute; bottom: 10px; right: 10px; font-size: 4rem;">🦕</div>

<div class="app-shell">
    <div class="main-stage">
        <header class="shin-header">
            <div class="app-title">
                <h1>⚡ SHIN-CHAN TRANSFER</h1>
                <p>Oho! Send Big Files P2P! No Servers!</p>
            </div>
            <div class="d-flex align-items-center gap-3">
                 <div id="connectionBadge" class="conn-status" style="display:none;">Offline</div>
            </div>
        </header>

        <div class="stage-content">
            
            <div id="step1">
                <h2 class="text-center" style="font-weight: 800; color: var(--outline); margin-bottom: 20px;">Hey! Who are you today?</h2>
                <div class="role-buttons">
                    <div class="role-card" style="background: #ffcccc;">
                        <div style="font-size: 4rem;">📤</div>
                        <h3>I am Sender</h3>
                        <p>I have the files!</p>
                        <button class="btn btn-primary w-100 mt-2" onclick="startSender()">Start Upload</button>
                    </div>
                    <div class="role-card" style="background: #c7ecee;">
                        <div style="font-size: 4rem;">📥</div>
                        <h3>I am Receiver</h3>
                        <p>Give me files!</p>
                        <button class="btn btn-outline-light w-100 mt-2" onclick="startReceiver()">Start Download</button>
                    </div>
                </div>
            </div>

            <div id="step2" style="display:none;" class="text-center">
                <div class="panel" style="max-width: 600px; margin: 0 auto;">
                    <h3>Room Secret Code</h3>
                    <p>Tell this to your friend, quick!</p>
                    <div id="roomIdDisplay" class="mb-4"></div>
                    
                    <div id="receiverInput" style="display:none;">
                        <input type="text" id="joinInput" class="form-control mb-3" placeholder="ENTER CODE HERE">
                        <button class="btn btn-success w-100" onclick="joinRoom()">JOIN ROOM & CONNECT!</button>
                    </div>

                    <div id="senderWaiting" style="display:none;">
                        <div class="spinner-border text-danger" style="width: 3rem; height: 3rem;" role="status"></div>
                        <h4 class="mt-3">Waiting for friend to join...</h4>
                    </div>
                </div>
            </div>

            <div id="step3" style="display:none;">
                <div class="alert alert-danger" id="connectionError" style="display:none; border:3px solid black;">
                    <strong>OH NO! Connection Failed!</strong><br>
                    Firewalls might be blocking us. 
                    <button class="btn btn-sm btn-warning mt-2" onclick="retryConnection()">TRY AGAIN</button>
                </div>

                <div class="row">
                    <div class="col-md-6" id="senderUI" style="display:none;">
                        <div class="panel">
                            <div class="d-flex justify-content-between">
                                <span class="panel-title">SENDER ZONE</span>
                                <span class="panel-badge" style="background: var(--shin-yellow);">UPLOAD</span>
                            </div>
                            
                            <div id="dropZone" class="mt-3">
                                <div style="font-size: 3rem; margin-bottom: 10px;">📂</div>
                                <h3>Pick a File</h3>
                                <p>Click here or drag a file</p>
                                <input type="file" id="fileInput" style="display: none;" onchange="handleFileSelect(this.files)">
                            </div>

                            <div id="fileActions" class="mt-3 p-3" style="display:none; background: #dfe6e9; border-radius: 15px;">
                                <h4 id="fileName" style="word-break: break-all;"></h4>
                                <p class="text-muted" id="fileSize"></p>
                                <button id="sendBtn" class="btn btn-success w-100" onclick="initiateTransfer()" disabled>
                                    ⏳ WAITING FOR CONNECTION...
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-6" id="receiverUI" style="display:none;">
                        <div class="panel">
                             <div class="d-flex justify-content-between">
                                <span class="panel-title">RECEIVER ZONE</span>
                                <span class="panel-badge" style="background: var(--chocobi-green); color:white;">DOWNLOAD</span>
                            </div>

                            <div class="text-center mt-4">
                                <h4 id="receiverStatus">Waiting for sender...</h4>
                                
                                <button id="saveAndStartBtn" class="btn btn-success mt-3 w-100" style="display:none;" onclick="prepareSaveAndStart()">
                                    💾 SAVE & START DOWNLOAD
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="progress-wrapper">
                    <div class="d-flex justify-content-between mb-2">
                        <strong>TRANSFER PROGRESS</strong>
                        <span id="p2pStatusLabel" style="color: var(--action-blue);">Initializing...</span>
                    </div>
                    <div class="progress">
                        <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%">0%</div>
                    </div>
                    <div class="d-flex justify-content-between mt-2" style="font-weight: 700;">
                        <span>Speed: <span id="speedDisplay" style="color: var(--shin-red);">0 MB/s</span></span>
                        <span>Time Left: <span id="timeDisplay">--:--</span></span>
                    </div>
                </div>

                <div class="log-container">
                    <div class="log-header">SYSTEM DIARY</div>
                    <div id="logs"></div>
                </div>
            </div>

        </div>
    </div>
</div>

<script>
    // --- CORE VARIABLES ---
    let socket, peerConnection, dataChannel;
    let roomId;
    let selectedFile;
    let isInitiator = false;

    let transferState = { offset: 0, fileSize: 0, fileName: '', startTime: 0, lastChunkTime: 0, lastOffset: 0 };
    let pendingMeta = null;

    // IMPROVED CONFIG: More STUN servers to fix connection issues
    const rtcConfig = { 
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' },
            { urls: 'stun:stun3.l.google.com:19302' },
            { urls: 'stun:stun4.l.google.com:19302' }
        ] 
    };

    // WAKE LOCK
    async function requestWakeLock() {
        try {
            if ('wakeLock' in navigator) await navigator.wakeLock.request('screen');
        } catch (err) { console.log(err); }
    }

    // LOGGING
    function log(msg) {
        const box = document.getElementById('logs');
        box.innerHTML += `<div>&gt; ${msg}</div>`;
        box.scrollTop = box.scrollHeight;
        console.log("[LOG]", msg);
    }

    function logError(msg, err) {
        const box = document.getElementById('logs');
        box.innerHTML += `<div class="text-red">! ${msg}: ${err?.message || err}</div>`;
        box.scrollTop = box.scrollHeight;
        console.error("[ERROR]", msg, err);
    }

    function updateStatus(status, type) {
        const badge = document.getElementById('connectionBadge');
        badge.style.display = 'block';
        badge.innerText = status;
        badge.className = 'conn-status ' + type;
        
        const statusLabel = document.getElementById('p2pStatusLabel');
        statusLabel.innerText = status;

        if(type === 'connected') {
            document.getElementById('connectionError').style.display = 'none';
            const btn = document.getElementById('sendBtn');
            btn.disabled = false;
            btn.innerText = "🚀 ACTION BEAM! (Send)";
            log("System Ready: P2P Tunnel Established.");
        } else if (type === 'failed') {
             document.getElementById('connectionError').style.display = 'block';
             logError("Connection Failed. Firewalls might be blocking.", "");
        }
    }

    // WEBSOCKET
    function connectSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${protocol}//${location.host}/ws`);

        socket.onopen = () => log("Server connected.");
        socket.onmessage = (e) => {
            const msg = JSON.parse(e.data);
            if (msg.type === 'peer_joined') startPeerConnection(true);
            if (msg.type === 'offer') handleOffer(msg.data);
            if (msg.type === 'answer') handleAnswer(msg.data);
            if (msg.type === 'candidate') handleCandidate(msg.data);
        };
        socket.onerror = (e) => logError("WebSocket error", e);
    }
    connectSocket();

    // NAVIGATION
    function startSender() {
        roomId = Math.random().toString(36).substring(2, 7).toUpperCase();
        document.getElementById('step1').style.display = 'none';
        document.getElementById('step2').style.display = 'block';
        document.getElementById('senderWaiting').style.display = 'block';
        document.getElementById('roomIdDisplay').innerText = roomId;
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
        updateStatus("Connecting...", "connecting");
    }

    function retryConnection() {
        log("Retrying connection...");
        document.getElementById('connectionError').style.display = 'none';
        if(peerConnection) peerConnection.close();
        // Re-initiate based on role
        if(isInitiator) startPeerConnection(true);
        else log("Waiting for sender to retry...");
    }

    // WEBRTC
    function startPeerConnection(initiator) {
        isInitiator = initiator;
        if (initiator) {
            document.getElementById('step2').style.display = 'none';
            document.getElementById('step3').style.display = 'block';
            document.getElementById('senderUI').style.display = 'block';
            updateStatus("Connecting...", "connecting");
        }

        peerConnection = new RTCPeerConnection(rtcConfig);

        peerConnection.onicecandidate = e => {
            if (e.candidate) {
                socket.send(JSON.stringify({ type: 'candidate', room: roomId, data: e.candidate }));
            }
        };

        peerConnection.onconnectionstatechange = () => {
            const state = peerConnection.connectionState;
            log("Connection State: " + state);
            if(state === 'connected') updateStatus("Connected!", "connected");
            if(state === 'failed' || state === 'disconnected') updateStatus("Failed/Disconnected", "failed");
        };

        if (initiator) {
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
        if(!peerConnection) startPeerConnection(false);
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
            if(peerConnection) await peerConnection.addIceCandidate(candidate);
        } catch (err) { console.error(err); }
    }

    // DATA CHANNEL
    function setupDataChannel(channel) {
        channel.binaryType = 'arraybuffer';
        channel.onopen = () => {
            log("P2P Pipe OPEN!");
            updateStatus("Connected!", "connected");
        };
        channel.onclose = () => updateStatus("Closed", "failed");
        
        channel.onmessage = async (e) => {
            const data = e.data;
            if (typeof data === 'string') {
                const msg = JSON.parse(data);
                if (msg.type === 'request_offset') startSendingChunks(msg.offset || 0);
                if (msg.type === 'file_meta') handleFileMeta(msg);
            } else {
                await handleIncomingChunk(data);
            }
        };
    }

    // SENDER LOGIC
    function handleFileSelect(files) {
        selectedFile = files[0];
        if (!selectedFile) return;
        document.getElementById('fileName').innerText = selectedFile.name;
        document.getElementById('fileSize').innerText = (selectedFile.size / (1024*1024*1024)).toFixed(2) + " GB";
        document.getElementById('fileActions').style.display = 'block';
    }

    function initiateTransfer() {
        if (!dataChannel || dataChannel.readyState !== 'open') {
            alert("Connection not ready! Please wait for the green 'Connected' status.");
            return;
        }
        dataChannel.send(JSON.stringify({ type: 'file_meta', name: selectedFile.name, size: selectedFile.size }));
        log("Metadata sent. Waiting for receiver...");
    }

    async function startSendingChunks(offset) {
        const CHUNK_SIZE = 64 * 1024; 
        const fileReader = new FileReader();
        transferState.offset = offset;
        transferState.startTime = Date.now();
        transferState.lastChunkTime = Date.now();
        transferState.lastOffset = offset;

        function readNext() {
            if (transferState.offset >= selectedFile.size) { log("Transfer Finished!"); return; }
            if (dataChannel.bufferedAmount > 10 * 1024 * 1024) { setTimeout(readNext, 50); return; }
            const slice = selectedFile.slice(transferState.offset, transferState.offset + CHUNK_SIZE);
            fileReader.readAsArrayBuffer(slice);
        }

        fileReader.onload = (e) => {
            try { dataChannel.send(e.target.result); } catch (err) { logError("Send Error", err); return; }
            transferState.offset += e.target.result.byteLength;
            updateProgress(transferState.offset, selectedFile.size);
            readNext();
        };
        readNext();
    }

    // RECEIVER LOGIC
    let writer = null;
    let receivedBytes = 0;
    const useNativeFS = ('showSaveFilePicker' in window);

    function handleFileMeta(meta) {
        pendingMeta = meta;
        transferState.fileSize = meta.size;
        document.getElementById('receiverStatus').innerText = "Ready: " + meta.name + "\n(" + (meta.size/(1024*1024)).toFixed(1) + " MB)";
        const btn = document.getElementById('saveAndStartBtn');
        btn.style.display = 'inline-block';
        btn.disabled = false;
    }

    async function prepareSaveAndStart() {
        document.getElementById('saveAndStartBtn').disabled = true;
        try {
            if (useNativeFS) {
                const handle = await window.showSaveFilePicker({ suggestedName: pendingMeta.name });
                writer = await handle.createWritable();
            } else {
                writer = streamSaver.createWriteStream(pendingMeta.name, { size: pendingMeta.size }).getWriter();
            }
            receivedBytes = 0;
            transferState.startTime = Date.now();
            requestResume();
        } catch (e) {
            logError("Save cancelled", e);
            document.getElementById('saveAndStartBtn').disabled = false;
        }
    }

    function requestResume() {
        dataChannel.send(JSON.stringify({ type: 'request_offset', offset: receivedBytes }));
    }

    async function handleIncomingChunk(buffer) {
        if (useNativeFS) await writer.write(buffer);
        else await writer.write(new Uint8Array(buffer));
        receivedBytes += buffer.byteLength;
        updateProgress(receivedBytes, transferState.fileSize);
        if (receivedBytes >= transferState.fileSize) {
            log("Download Complete!");
            if(useNativeFS) await writer.close(); else writer.close();
        }
    }

    // PROGRESS & UTILS
    function updateProgress(current, total) {
        total = total || 1;
        const percent = ((current / total) * 100).toFixed(2);
        document.getElementById('progressBar').style.width = percent + '%';
        document.getElementById('progressBar').innerText = percent + '%';

        const now = Date.now();
        const dt = (now - transferState.lastChunkTime) / 1000;
        if (dt > 0.5) {
            const speed = (current - transferState.lastOffset) / (1024 * 1024) / dt;
            document.getElementById('speedDisplay').innerText = speed.toFixed(2) + " MB/s";
            if (speed > 0) {
                const rem = (total - current) / (1024 * 1024) / speed;
                document.getElementById('timeDisplay').innerText = Math.floor(rem/60) + ":" + Math.floor(rem%60).toString().padStart(2,'0');
            }
            transferState.lastChunkTime = now;
            transferState.lastOffset = current;
        }
    }

    // DRAG DROP
    const dz = document.getElementById('dropZone');
    dz.addEventListener('click', () => document.getElementById('fileInput').click());
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.style.background = "#fab1a0"; });
    dz.addEventListener('dragleave', e => { e.preventDefault(); dz.style.background = "#f1f2f6"; });
    dz.addEventListener('drop', e => {
        e.preventDefault(); dz.style.background = "#f1f2f6";
        if(e.dataTransfer.files.length) handleFileSelect(e.dataTransfer.files);
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

