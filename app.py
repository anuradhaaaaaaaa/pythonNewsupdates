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

    <style>
        :root {
            --shin-red: #ff4757;
            --shin-yellow: #f1c40f;
            --shin-skin: #ffeaa7;
            --action-blue: #3742fa;
            --chocobi-green: #2ed573;
            --chocobi-pink: #ff7f50;
            --outline: #2f3542;
            --white: #ffffff;
        }

        body {
            margin: 0;
            padding: 0;
            height: 100vh;
            width: 100vw;
            background-color: #70a1ff;
            /* Polka dot background like Shin Chan transitions */
            background-image: radial-gradient(var(--white) 15%, transparent 16%),
                              radial-gradient(var(--white) 15%, transparent 16%);
            background-size: 60px 60px;
            background-position: 0 0, 30px 30px;
            font-family: 'Fredoka', cursive;
            overflow: hidden; /* PC only, no scroll on main body */
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* --- CARTOON CONTAINERS --- */
        .app-shell {
            width: 90%;
            height: 90%;
            max-width: 1400px;
            display: flex;
            gap: 20px;
        }

        .main-stage {
            flex: 1;
            background: var(--white);
            border: 4px solid var(--outline);
            border-radius: 30px;
            box-shadow: 15px 15px 0px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        /* Decorative Header (Action Kamen Style) */
        .shin-header {
            background: var(--shin-red);
            padding: 20px;
            border-bottom: 4px solid var(--outline);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .app-title h1 {
            color: var(--shin-yellow);
            font-weight: 700;
            font-size: 2.5rem;
            text-shadow: 3px 3px 0px var(--outline);
            margin: 0;
            -webkit-text-stroke: 1.5px var(--outline);
        }

        .app-title p {
            color: var(--white);
            font-weight: 600;
            margin: 0;
            font-size: 1.1rem;
        }

        /* Status badges */
        .status-chips {
            display: flex;
            gap: 10px;
        }
        .chip {
            background: var(--white);
            border: 3px solid var(--outline);
            border-radius: 15px;
            padding: 5px 15px;
            font-weight: 700;
            box-shadow: 3px 3px 0px rgba(0,0,0,0.1);
        }

        /* --- CONTENT AREA --- */
        .stage-content {
            padding: 40px;
            flex: 1;
            overflow-y: auto;
            background: linear-gradient(180deg, #fff 0%, #f1f2f6 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        /* --- BUTTONS (BOUNCY) --- */
        .btn {
            border: 3px solid var(--outline) !important;
            font-weight: 700;
            font-size: 1.2rem;
            text-transform: uppercase;
            padding: 15px 30px;
            border-radius: 50px;
            box-shadow: 0 6px 0 var(--outline);
            transition: all 0.1s;
            position: relative;
            top: 0;
        }

        .btn:active {
            top: 6px;
            box-shadow: 0 0 0 var(--outline);
        }

        .btn-primary {
            background-color: var(--shin-red);
            color: var(--shin-yellow);
        }
        .btn-primary:hover {
            background-color: #ff6b81;
            color: var(--white);
            transform: scale(1.05);
        }

        .btn-outline-light {
            background-color: var(--action-blue);
            color: var(--white);
        }
        .btn-outline-light:hover {
            background-color: #5352ed;
            color: var(--white);
            transform: scale(1.05);
        }

        .btn-success {
            background-color: var(--chocobi-green);
            color: var(--white);
        }

        /* --- INPUTS --- */
        input[type="text"] {
            border: 3px solid var(--outline);
            border-radius: 20px;
            padding: 15px;
            font-size: 1.5rem;
            text-align: center;
            font-weight: 700;
            color: var(--action-blue);
            background: #f1f2f6;
            box-shadow: inset 4px 4px 0px rgba(0,0,0,0.1);
        }

        /* --- PANELS (Chocobi Box Style) --- */
        .panel {
            background: var(--white);
            border: 3px solid var(--outline);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 8px 8px 0px var(--chocobi-green); /* Green Shadow */
            margin-bottom: 20px;
            position: relative;
        }

        .panel-title {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--outline);
            margin-bottom: 5px;
        }
        
        .panel-badge {
            background: var(--shin-yellow);
            border: 2px solid var(--outline);
            padding: 5px 10px;
            border-radius: 10px;
            font-weight: 700;
            display: inline-block;
            margin-bottom: 10px;
        }

        /* --- DROP ZONE --- */
        #dropZone {
            border: 4px dashed var(--action-blue);
            border-radius: 20px;
            background: #f1f2f6;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: 0.3s;
        }

        #dropZone:hover {
            background: #dfe4ea;
            transform: rotate(-1deg) scale(1.02);
        }

        #dropZone h3 {
            font-weight: 800;
            color: var(--action-blue);
        }

        /* --- PROGRESS BAR --- */
        .progress-wrapper {
            margin-top: 20px;
            border: 3px solid var(--outline);
            border-radius: 20px;
            padding: 15px;
            background: var(--shin-skin);
            box-shadow: 6px 6px 0px var(--shin-red);
        }

        .progress {
            height: 30px;
            border: 2px solid var(--outline);
            border-radius: 15px;
            background: var(--white);
            overflow: hidden;
        }

        .progress-bar {
            background-color: var(--chocobi-green);
            background-image: linear-gradient(45deg,rgba(255,255,255,.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,.15) 50%,rgba(255,255,255,.15) 75%,transparent 75%,transparent);
            background-size: 1rem 1rem;
        }

        /* --- LOGS (Comic Speech Bubble) --- */
        .log-container {
            margin-top: 20px;
            background: var(--white);
            border: 3px solid var(--outline);
            border-radius: 20px;
            padding: 0;
            position: relative;
        }
        
        .log-header {
            background: var(--outline);
            color: var(--white);
            padding: 10px 20px;
            font-weight: 700;
            border-radius: 16px 16px 0 0;
        }

        #logs {
            height: 120px;
            overflow-y: auto;
            padding: 15px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: 600;
            color: var(--outline);
        }

        .text-red { color: var(--shin-red); font-weight: bold; }

        /* --- DECORATIONS --- */
        .star-decoration {
            font-size: 50px;
            position: absolute;
            z-index: 0;
            animation: spin 10s linear infinite;
            opacity: 0.2;
            pointer-events: none;
        }

        @keyframes spin { 100% { transform: rotate(360deg); } }

        /* Step Visibility Utilities */
        #step1, #step2, #step3 { width: 100%; max-width: 900px; margin: 0 auto; }
        
        .role-buttons {
            display: flex;
            gap: 30px;
            justify-content: center;
            margin-top: 40px;
        }

        .role-card {
            flex: 1;
            padding: 30px;
            border: 3px solid var(--outline);
            border-radius: 25px;
            text-align: center;
            background: var(--white);
            box-shadow: 10px 10px 0px rgba(0,0,0,0.1);
            transition: 0.3s;
        }
        .role-card:hover {
            transform: translateY(-10px);
        }

        /* Step 2 Room ID Styling */
        #roomIdDisplay {
            font-size: 3rem;
            color: var(--shin-red);
            font-weight: 900;
            letter-spacing: 5px;
            text-shadow: 2px 2px 0px var(--outline);
        }

    </style>
</head>
<body>

<div style="position:absolute; top: 10px; left: 10px; font-size: 4rem;">⭐</div>
<div style="position:absolute; bottom: 10px; right: 10px; font-size: 4rem;">🦕</div>
<div style="position:absolute; top: 40%; left: 5%; font-size: 3rem; opacity: 0.5;">🍪</div>
<div style="position:absolute; top: 20%; right: 10%; font-size: 3rem; opacity: 0.5;">👽</div>

<div class="app-shell">
    <div class="main-stage">
        <header class="shin-header">
            <div class="app-title">
                <h1>
                    ⚡ SHIN-CHAN TRANSFER
                </h1>
                <p>Oho! Send Big Files P2P! No Servers!</p>
            </div>
            <div class="status-chips">
                <div class="chip" style="color: var(--chocobi-green);">
                    <span id="fsStatus">Checking File System...</span>
                </div>
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
                <div class="text-center mt-4">
                     <span id="wakeLockStatus" class="chip" style="background:var(--shin-skin);">😴 Screen might sleep</span>
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
                        <p class="text-muted">Don't close this window!</p>
                    </div>
                </div>
            </div>

            <div id="step3" style="display:none;">
                <div class="row">
                    <div class="col-md-6" id="senderUI" style="display:none;">
                        <div class="panel">
                            <div class="d-flex justify-content-between">
                                <span class="panel-title">SENDER ZONE</span>
                                <span class="panel-badge">UPLOAD</span>
                            </div>
                            
                            <div id="dropZone" class="mt-3">
                                <div style="font-size: 3rem; margin-bottom: 10px;">📂</div>
                                <h3>Pick a File</h3>
                                <p>Click here or drag a file (Even 100GB is okay!)</p>
                                <input type="file" id="fileInput" style="display: none;" onchange="handleFileSelect(this.files)">
                            </div>

                            <div id="fileActions" class="mt-3 p-3" style="display:none; background: #dfe6e9; border-radius: 15px;">
                                <h4 id="fileName" style="word-break: break-all;"></h4>
                                <p class="text-muted" id="fileSize"></p>
                                <button class="btn btn-success w-100" onclick="initiateTransfer()">🚀 ACTION BEAM! (Send)</button>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-6" id="receiverUI" style="display:none;">
                        <div class="panel">
                             <div class="d-flex justify-content-between">
                                <span class="panel-title">RECEIVER ZONE</span>
                                <span class="panel-badge">DOWNLOAD</span>
                            </div>

                            <div class="text-center mt-4">
                                <h4 id="receiverStatus">Waiting for sender... <br> (Is he eating Chocobi?)</h4>
                                
                                <div id="resumeControl" style="display:none;" class="alert alert-warning mt-3">
                                    <strong>File found!</strong>
                                    Sender has <span id="remoteFileName"></span>.
                                    <div class="mt-2 d-flex gap-2">
                                        <button class="btn btn-sm btn-warning flex-grow-1" onclick="requestResume()">Resume</button>
                                        <button class="btn btn-sm btn-outline-danger flex-grow-1" onclick="requestNew()">Restart</button>
                                    </div>
                                </div>

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
                        <span style="color: var(--action-blue);">Direct P2P Link Active</span>
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

    let transferState = {
        offset: 0,
        fileSize: 0,
        fileName: '',
        startTime: 0,
        lastChunkTime: 0,
        lastOffset: 0
    };

    let pendingMeta = null;

    const rtcConfig = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };

    // WAKE LOCK
    async function requestWakeLock() {
        try {
            if ('wakeLock' in navigator) {
                const lock = await navigator.wakeLock.request('screen');
                document.getElementById('wakeLockStatus').innerText = "☀️ Screen Awake!";
                document.getElementById('wakeLockStatus').style.background = "#2ed573";
                document.getElementById('wakeLockStatus').style.color = "white";
                log("Screen Wake Lock active");
            }
        } catch (err) {
            log("Wake Lock Error: " + err.message);
        }
    }

    // FILE SYSTEM SUPPORT
    const useNativeFS = ('showSaveFilePicker' in window);
    document.getElementById('fsStatus').innerText =
        useNativeFS ? "💾 Direct Save Ready" : "💾 StreamSaver Mode";

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

    // WEBSOCKET SIGNALING
    function connectSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${protocol}//${location.host}/ws`);

        socket.onopen = () => log("Signaling socket connected");
        socket.onmessage = (e) => {
            const msg = JSON.parse(e.data);
            if (msg.type === 'peer_joined') startPeerConnection(true);
            if (msg.type === 'offer') handleOffer(msg.data);
            if (msg.type === 'answer') handleAnswer(msg.data);
            if (msg.type === 'candidate') handleCandidate(msg.data);
        };
        socket.onerror = (e) => logError("WebSocket error", e);
        socket.onclose = () => log("WebSocket closed");
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
        document.getElementById('senderUI').style.display = 'none'; // Ensure sender UI is hidden
    }

    // WEBRTC
    function startPeerConnection(isInitiator) {
        if (isInitiator) {
            document.getElementById('step2').style.display = 'none';
            document.getElementById('step3').style.display = 'block';
            document.getElementById('senderUI').style.display = 'block';
            document.getElementById('receiverUI').style.display = 'none';
        }

        peerConnection = new RTCPeerConnection(rtcConfig);

        peerConnection.onicecandidate = e => {
            if (e.candidate) {
                socket.send(JSON.stringify({ type: 'candidate', room: roomId, data: e.candidate }));
            }
        };

        peerConnection.onconnectionstatechange = () => {
            log("Connection state: " + peerConnection.connectionState);
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

    // DATA CHANNEL
    function setupDataChannel(channel) {
        channel.binaryType = 'arraybuffer';

        channel.onopen = () => log("P2P Pipe is OPEN!");
        channel.onclose = () => log("P2P Pipe closed");
        channel.onerror = (err) => logError("DataChannel error", err);

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
                    startSendingChunks(msg.offset || 0);
                }

                if (msg.type === 'file_meta') {
                    handleFileMeta(msg);
                }
            } else {
                await handleIncomingChunk(data);
            }
        };
    }

    // SENDER
    function handleFileSelect(files) {
        selectedFile = files[0];
        if (!selectedFile) return;
        document.getElementById('fileName').innerText = selectedFile.name;
        document.getElementById('fileSize').innerText =
            (selectedFile.size / (1024*1024*1024)).toFixed(2) + " GB";
        document.getElementById('fileActions').style.display = 'block';
        log("File ready: " + selectedFile.name);
    }

    function initiateTransfer() {
        if (!selectedFile) {
            log("No file selected");
            return;
        }
        if (!dataChannel || dataChannel.readyState !== 'open') {
            log("Wait! Connection not ready yet.");
            return;
        }
        dataChannel.send(JSON.stringify({
            type: 'file_meta',
            name: selectedFile.name,
            size: selectedFile.size
        }));
        log("Sent file details. Waiting for receiver...");
    }

    async function startSendingChunks(offset) {
        if (!selectedFile) return;
        if (!dataChannel || dataChannel.readyState !== 'open') return;

        log(`Starting transfer from: ${offset}`);
        transferState.offset = offset;
        transferState.startTime = Date.now();
        transferState.lastChunkTime = Date.now();
        transferState.lastOffset = offset;

        const CHUNK_SIZE = 64 * 1024;
        const fileReader = new FileReader();

        function readNext() {
            if (transferState.offset >= selectedFile.size) {
                log("Transfer Finished!");
                return;
            }

            if (dataChannel.bufferedAmount > 10 * 1024 * 1024) {
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

    // RECEIVER
    let receivedBytes = 0;
    let writer = null;
    let usingNativeFS = useNativeFS;

    function handleFileMeta(meta) {
        pendingMeta = meta;
        transferState.fileName = meta.name;
        transferState.fileSize = meta.size;
        document.getElementById('receiverStatus').innerText =
            "Ready to download: " + meta.name + "\n(" + (meta.size/(1024*1024)).toFixed(1) + " MB)";
        log("Received file info: " + meta.name);

        const btn = document.getElementById('saveAndStartBtn');
        btn.style.display = 'inline-block';
        btn.disabled = false;
    }

    async function prepareSaveAndStart() {
        const btn = document.getElementById('saveAndStartBtn');
        if (!pendingMeta) return;
        const meta = pendingMeta;
        btn.disabled = true;

        try {
            if (useNativeFS) {
                const handle = await window.showSaveFilePicker({ suggestedName: meta.name });
                const writable = await handle.createWritable();
                writer = writable;
                usingNativeFS = true;
                log("Saving directly to disk.");
            } else {
                if (window.streamSaver) {
                    const fileStream = streamSaver.createWriteStream(meta.name, { size: meta.size });
                    writer = fileStream.getWriter();
                    usingNativeFS = false;
                    log("Using StreamSaver fallback.");
                } else {
                    throw new Error("No saving method available.");
                }
            }

            receivedBytes = 0;
            transferState.offset = 0;
            transferState.startTime = Date.now();
            transferState.lastChunkTime = Date.now();
            transferState.lastOffset = 0;
            pendingMeta = null;

            requestResume();
        } catch (e) {
            btn.disabled = false;
            logError("Save cancelled", e);
            alert("Could not start save.");
        }
    }

    function requestResume() {
        if (!dataChannel || dataChannel.readyState !== 'open') {
            log("Connection lost.");
            return;
        }
        log("Asking sender to start...");
        dataChannel.send(JSON.stringify({ type: 'request_offset', offset: receivedBytes }));
    }

    function requestNew() {
        receivedBytes = 0;
        transferState.offset = 0;
        updateProgress(0, transferState.fileSize || 1);
        requestResume();
    }

    async function handleIncomingChunk(buffer) {
        if (!writer) return;

        try {
            if (usingNativeFS) {
                await writer.write(buffer);
            } else {
                await writer.write(new Uint8Array(buffer));
            }
        } catch (err) {
            logError("Write failed", err);
            return;
        }

        receivedBytes += buffer.byteLength;
        document.getElementById('currentReceived').innerText = receivedBytes;
        updateProgress(receivedBytes, transferState.fileSize);

        if (receivedBytes >= transferState.fileSize) {
            log("Download Complete! Yuhuu!");
            try {
                if (usingNativeFS) {
                    await writer.close();
                } else {
                    writer.close();
                }
            } catch (err) {
                logError("Error closing file", err);
            }
        }
    }

    // UTILS
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
                    `${minutes}:${seconds.toString().padStart(2, '0')}`;
            } else {
                document.getElementById('timeDisplay').innerText = "--:--";
            }
        }
    }

    // DRAG & DROP
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.background = "#fab1a0"; // light red
    });
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.background = "#f1f2f6";
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.background = "#f1f2f6";
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
