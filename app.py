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
        :root {
            --bg-body: #020617;      /* slate-950 */
            --bg-card: #020617;
            --bg-card-inner: #020617;
            --border-subtle: #1f2937; /* slate-800 */
            --accent: #6366f1;       /* indigo-500 */
            --accent-soft: rgba(99,102,241,0.12);
            --accent-strong: #4f46e5; /* indigo-600 */
            --text-main: #f9fafb;    /* very light */
            --text-muted: #e5e7eb;   /* light */
            --text-soft: #9ca3af;    /* medium */
            --danger: #f97373;
            --log-bg: #020617;
            --log-text: #4ade80;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            min-height: 100vh;
            background: radial-gradient(circle at top, #0f172a 0, #020617 45%, #000 100%);
            color: var(--text-main);
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .app-shell {
            max-width: 920px;
            margin: 32px auto;
            padding: 0 12px 32px;
        }

        .card-main {
            background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(15,23,42,0.95));
            border-radius: 18px;
            border: 1px solid rgba(148,163,184,0.20);
            box-shadow:
                0 22px 45px rgba(15,23,42,0.85),
                0 0 0 1px rgba(15,23,42,0.7);
            padding: 24px 20px 20px;
        }

        @media (min-width: 768px) {
            .card-main {
                padding: 28px 28px 22px;
            }
        }

        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 18px;
        }

        .app-title {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .app-title h1 {
            font-size: 1.4rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #ffffff;
        }

        .app-title h1 span.badge-pill {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            padding: 3px 9px;
            border-radius: 999px;
            background: rgba(15,23,42,0.95);
            border: 1px solid rgba(148,163,184,0.7);
            color: #e5e7eb;
        }

        .app-title p {
            margin: 0;
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .status-chips {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 4px;
            font-size: 0.75rem;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 9px;
            border-radius: 999px;
            background: rgba(15,23,42,0.92);
            border: 1px solid rgba(148,163,184,0.65);
            color: var(--text-muted);
            white-space: nowrap;
        }

        .chip-dot {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: 0 0 8px rgba(34,197,94,0.8);
        }

        .chip-label {
            font-weight: 600;
            color: #e5e7eb;
        }

        .chip-sub {
            font-size: 0.7em;
            opacity: 0.9;
        }

        .chip-fs {
            border-style: dashed;
        }

        /* Step 1 */
        #step1 {
            margin-top: 8px;
        }

        .role-buttons {
            display: grid;
            gap: 10px;
        }

        @media (min-width: 576px) {
            .role-buttons {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent), var(--accent-strong));
            border: none;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.95rem;
            padding-block: 10px;
            box-shadow: 0 14px 28px rgba(79,70,229,0.5);
            color: #f9fafb;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, var(--accent-strong), #4338ca);
            box-shadow: 0 16px 32px rgba(79,70,229,0.7);
        }

        .btn-outline-light {
            border-radius: 999px;
            border: 1px solid rgba(209,213,219,0.75) !important;
            color: #f9fafb;
            background: rgba(15,23,42,0.85);
            font-weight: 500;
            font-size: 0.95rem;
        }

        .btn-outline-light:hover {
            background: rgba(30,64,175,0.6);
            border-color: rgba(209,213,219,1) !important;
        }

        .hint-row {
            margin-top: 10px;
            font-size: 0.78rem;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 4px;
        }

        .pill-tag {
            font-size: 0.7rem;
            padding: 3px 9px;
            border-radius: 999px;
            border: 1px solid rgba(209,213,219,0.8);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
        }

        /* Step 2 – Room / Join */
        #step2 .alert {
            background: rgba(15,23,42,0.96);
            border-radius: 14px;
            border: 1px solid rgba(148,163,184,0.45);
            color: var(--text-main);
        }

        #roomIdDisplay {
            font-size: 0.98rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: #e5e7eb;
        }

        #joinInput {
            background: rgba(15,23,42,0.96);
            border-radius: 999px;
            border: 1px solid rgba(148,163,184,0.7);
            color: var(--text-main);
            font-size: 0.9rem;
        }

        #joinInput::placeholder {
            color: var(--text-soft);
        }

        #senderWaiting p {
            margin-top: 8px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        /* Step 3 */
        #step3 {
            margin-top: 6px;
        }

        .transfer-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
            gap: 20px;
            margin-bottom: 18px;
        }

        @media (max-width: 768px) {
            .transfer-layout {
                grid-template-columns: minmax(0, 1fr);
            }
        }

        .panel {
            border-radius: 14px;
            border: 1px solid rgba(148,163,184,0.45);
            background: radial-gradient(circle at top left, rgba(79,70,229,0.18), rgba(15,23,42,0.98));
            padding: 14px 14px 12px;
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .panel-title {
            font-size: 0.92rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #c7d2fe;
        }

        .panel-sub {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .panel-badge {
            font-size: 0.78rem;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid rgba(129,140,248,0.9);
            background: rgba(15,23,42,0.98);
            color: #e0e7ff;
            font-weight: 500;
        }

        /* Sender file selector */
        #dropZone {
            border: 2px dashed rgba(209,213,219,0.85);
            border-radius: 14px;
            padding: 26px 18px;
            text-align: center;
            cursor: pointer;
            transition: 0.18s ease;
            background: rgba(15,23,42,0.98);
        }

        #dropZone:hover {
            background: rgba(30,64,175,0.55);
            border-color: #a5b4fc;
            box-shadow: 0 0 0 1px rgba(129,140,248,0.9);
        }

        #dropZone h3 {
            margin: 0 0 6px;
            font-size: 1.02rem;
            font-weight: 600;
            color: #f9fafb;
        }

        #dropZone p {
            margin: 0;
            font-size: 0.82rem;
            color: var(--text-muted);
        }

        #fileActions {
            border-radius: 12px;
            background: rgba(15,23,42,0.98);
            border: 1px solid rgba(209,213,219,0.6);
            padding: 10px 12px;
        }

        #fileName {
            font-size: 0.9rem;
            margin: 0 0 2px;
            color: #f9fafb;
        }

        #fileSize {
            font-size: 0.8rem;
            color: var(--text-muted) !important;
            margin: 0 0 6px;
        }

        #receiverStatus {
            font-size: 0.84rem;
            color: var(--text-muted);
        }

        #resumeControl {
            margin-top: 10px;
            background: rgba(30,64,175,0.2);
            border-color: rgba(129,140,248,0.9);
            color: var(--text-main);
            font-size: 0.8rem;
        }

        #saveAndStartBtn {
            font-size: 0.84rem;
            font-weight: 600;
            border-radius: 999px;
            padding-block: 8px;
        }

        /* Progress & stats */
        .progress-wrapper {
            border-radius: 14px;
            background: radial-gradient(circle at top, rgba(15,23,42,0.98), rgba(15,23,42,1));
            border: 1px solid rgba(148,163,184,0.55);
            padding: 10px 14px 12px;
        }

        .progress {
            background-color: rgba(15,23,42,0.98);
            border-radius: 999px;
            overflow: hidden;
            height: 20px;
        }

        #progressBar {
            font-size: 0.77rem;
            font-weight: 700;
        }

        .stats-row {
            display: flex;
            justify-content: space-between;
            margin-top: 6px;
            font-size: 0.82rem;
            color: var(--text-muted);
        }

        .stats-row span strong {
            color: #f9fafb;
        }

        /* Logs */
        .log-container {
            margin-top: 12px;
            border-radius: 14px;
            background: var(--log-bg);
            border: 1px solid rgba(31,41,55,1);
        }

        .log-header {
            padding: 6px 10px 4px;
            border-bottom: 1px solid rgba(55,65,81,1);
            display: flex;
            justify-content: space-between;
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .log-header span.label {
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 700;
            font-size: 0.78rem;
            color: #e5e7eb;
        }

        .log-header span.right {
            font-size: 0.75rem;
            opacity: 0.9;
        }

        #logs {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            font-size: 0.78rem;
            color: var(--log-text);
            background: transparent;
            padding: 8px 9px;
            height: 140px;
            overflow-y: auto;
            border-radius: 0 0 14px 14px;
        }

        #logs div {
            white-space: pre-wrap;
        }

        .text-red {
            color: var(--danger);
        }
    </style>
</head>
<body>

<div class="app-shell">
    <div class="card-main">
        <header class="app-header">
            <div class="app-title">
                <h1>
                    ⚡ 100GB P2P Transfer
                    <span class="badge-pill">WebRTC · End-to-End</span>
                </h1>
                <p>Send huge files directly between two browsers. No server storage. Just signaling.</p>
            </div>
            <div class="status-chips">
                <div class="chip">
                    <span class="chip-dot"></span>
                    <span class="chip-label">Ready</span>
                    <span class="chip-sub">Awaiting role</span>
                </div>
                <div class="chip chip-fs">
                    <span id="fsStatus">Detecting file system...</span>
                </div>
            </div>
        </header>

        <!-- Step 1 -->
        <div id="step1">
            <div class="role-buttons mb-2">
                <button class="btn btn-primary" onclick="startSender()">I am the SENDER (Upload)</button>
                <button class="btn btn-outline-light" onclick="startReceiver()">I am the RECEIVER (Download)</button>
            </div>
            <div class="hint-row">
                <span id="wakeLockStatus">😴 Screen can sleep</span>
                <span class="pill-tag">Keep both tabs open during transfer</span>
            </div>
        </div>

        <!-- Step 2 -->
        <div id="step2" style="display:none;" class="mt-3">
            <div class="alert text-center">
                <h4 id="roomIdDisplay" class="mb-2"></h4>
                <p class="mb-3 text-muted" style="font-size:0.8rem;">
                    Share this Room ID with your peer. Only two peers are allowed per room.
                </p>
                <div id="receiverInput" style="display:none;">
                    <input type="text" id="joinInput" class="form-control text-center mb-2" placeholder="Enter Room ID from sender">
                    <button class="btn btn-success w-100" onclick="joinRoom()">Connect to Sender</button>
                </div>
                <div id="senderWaiting" style="display:none;">
                    <div class="spinner-border text-primary spinner-border-sm" role="status"></div>
                    <p class="mb-0" style="font-size:0.85rem;">Waiting for receiver to join…</p>
                </div>
            </div>
        </div>

        <!-- Step 3 -->
        <div id="step3" style="display:none;" class="mt-3">
            <div class="transfer-layout">
                <!-- Sender Panel -->
                <div id="senderUI" style="display:none;">
                    <div class="panel">
                        <div class="panel-header">
                            <div>
                                <div class="panel-title">Sender</div>
                                <div class="panel-sub">Choose the file you want to share</div>
                            </div>
                            <div class="panel-badge">Upload</div>
                        </div>

                        <div id="dropZone">
                            <h3>Select file</h3>
                            <p>Click to browse or drop a file here (multi-GB supported)</p>
                            <input type="file" id="fileInput" style="display: none;" onchange="handleFileSelect(this.files)">
                        </div>

                        <div id="fileActions" class="mt-3" style="display:none;">
                            <h5 id="fileName"></h5>
                            <p class="text-muted" id="fileSize"></p>
                            <button class="btn btn-success w-100" onclick="initiateTransfer()">Start / Resume Transfer</button>
                        </div>
                    </div>
                </div>

                <!-- Receiver Panel -->
                <div id="receiverUI" style="display:none;">
                    <div class="panel">
                        <div class="panel-header">
                            <div>
                                <div class="panel-title">Receiver</div>
                                <div class="panel-sub">Wait for metadata, then choose save location</div>
                            </div>
                            <div class="panel-badge">Download</div>
                        </div>

                        <p id="receiverStatus">Waiting for sender metadata…</p>

                        <div id="resumeControl" style="display:none;" class="alert alert-warning">
                            <strong>Resumable transfer detected.</strong><br>
                            Sender has <span id="remoteFileName"></span>.<br>
                            Current progress: <span id="currentReceived">0</span> bytes.
                            <div class="mt-2 d-flex gap-2">
                                <button class="btn btn-sm btn-warning flex-grow-1" onclick="requestResume()">Resume Download</button>
                                <button class="btn btn-sm btn-outline-danger flex-grow-1" onclick="requestNew()">Restart</button>
                            </div>
                        </div>

                        <button id="saveAndStartBtn"
                                class="btn btn-success mt-3 w-100"
                                style="display:none;"
                                onclick="prepareSaveAndStart()">
                            Choose save location & start download
                        </button>
                    </div>
                </div>
            </div>

            <!-- Progress & logs -->
            <div class="progress-wrapper">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span style="font-size:0.8rem; text-transform:uppercase; letter-spacing:0.12em; color:var(--text-soft);">
                        Transfer progress
                    </span>
                    <span style="font-size:0.8rem; color:var(--text-muted);">
                        P2P via WebRTC DataChannel
                    </span>
                </div>
                <div class="progress">
                    <div id="progressBar"
                         class="progress-bar progress-bar-striped progress-bar-animated bg-success"
                         role="progressbar"
                         style="width: 0%">
                        0%
                    </div>
                </div>
                <div class="stats-row">
                    <span>Speed: <strong id="speedDisplay">0 MB/s</strong></span>
                    <span>ETA: <strong id="timeDisplay">--:--</strong></span>
                </div>
            </div>

            <div class="log-container">
                <div class="log-header">
                    <span class="label">Transfer log</span>
                    <span class="right">Latest events at bottom</span>
                </div>
                <div id="logs"></div>
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
                document.getElementById('wakeLockStatus').innerText = "☀️ Screen kept awake";
                log("Screen Wake Lock active");
            }
        } catch (err) {
            log("Wake Lock Error: " + err.message);
        }
    }

    // FILE SYSTEM SUPPORT
    const useNativeFS = ('showSaveFilePicker' in window);
    document.getElementById('fsStatus').innerText =
        useNativeFS ? "💾 Native direct-write available" : "💾 Using StreamSaver fallback";

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

    // WEBRTC
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

    // DATA CHANNEL
    function setupDataChannel(channel) {
        channel.binaryType = 'arraybuffer';

        channel.onopen = () => log("P2P DataChannel open");
        channel.onclose = () => log("P2P DataChannel closed");
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
        log("Metadata sent. Waiting for receiver to choose save location…");
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

        const CHUNK_SIZE = 64 * 1024;
        const fileReader = new FileReader();

        function readNext() {
            if (transferState.offset >= selectedFile.size) {
                log("Transfer complete");
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

            requestResume();
        } catch (e) {
            btn.disabled = false;
            logError("File save cancelled or failed", e);
            alert("Failed to open save file dialog. Use Chrome on https:// or localhost and allow file access.");
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
                await writer.write(buffer);
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
            log("Download finished");
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

    // DRAG & DROP + CLICK (fixed)
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    // FIX: click to open file picker
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

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
