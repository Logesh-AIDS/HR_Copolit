/* frontend/app.js */

// Global State Instance
const state = {
    currentView: 'portal', // portal, waitingRoom, terminal, dashboard
    applicationId: null,
    interviewPlanId: null,
    sessionId: null,
    sessionToken: null,
    websocket: null,
    monacoEditor: null,
    interviewTimer: null,
    timeRemaining: 3600,
    currentQuestionIndex: 0,
    currentRoundIndex: 0,
    candidateName: "Jane Doe",
    jobTitle: "Staff Backend Engineer",
    timelineRounds: [],
    theme: 'dark', // dark, light
    micActive: true,
    camActive: true,
    screenSharing: false,
    
    // WebRTC Core objects
    localStream: null,
    remoteStream: null,
    peerConnection: null,
    peerRole: "CANDIDATE",
    screenStream: null,
    
    // Collaborative drawing state
    drawing: false,
    brushColor: "#3B82F6",
    brushWidth: 3,
    lastX: 0,
    lastY: 0
};

// Monaco Code Templates
const codeTemplates = {
    python: `def solution(arr):\n    # Write your Python 3 code here\n    pass\n\n# Input compilation runner\nimport sys\nif __name__ == "__main__":\n    print(solution([int(x) for x in sys.argv[1:]]))`,
    go: `package main\n\nimport (\n\t"fmt"\n\t"os"\n)\n\nfunc solution(arr []int) int {\n\t// Write your Go code here\n\treturn 0\n}\n\nfunc main() {\n\tfmt.Println(solution([]int{5}))\n}`,
    javascript: `function solution(arr) {\n    // Write your JavaScript code here\n    return 0;\n}\n\nconsole.log(solution([5]));`
};

document.addEventListener("DOMContentLoaded", () => {
    initDOMEvents();
    initMonaco();
    restoreTheme();
});

// View Router
function switchView(viewName) {
    state.currentView = viewName;
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    
    if (viewName === 'portal') {
        document.getElementById("portalScreen").classList.add("active");
        document.getElementById("viewToggleBtn").innerText = "Switch to Recruiter Dashboard";
    } else if (viewName === 'waitingRoom') {
        document.getElementById("waitingRoomScreen").classList.add("active");
        document.getElementById("viewToggleBtn").innerText = "Abort Preparation";
        startWaitingRoomCheck();
    } else if (viewName === 'terminal') {
        document.getElementById("terminalScreen").classList.add("active");
        document.getElementById("viewToggleBtn").innerText = "Abort Interview";
        startInterviewTimer();
        initWhiteboardCanvas();
    } else if (viewName === 'dashboard') {
        document.getElementById("dashboardScreen").classList.add("active");
        document.getElementById("viewToggleBtn").innerText = "Back to Apply Portal";
        renderRecruiterDashboard();
    }
}

// Theme Persistence
function restoreTheme() {
    const saved = localStorage.getItem("theme") || "dark";
    state.theme = saved;
    if (saved === 'light') {
        document.body.classList.add("light-theme");
        document.getElementById("themeToggleBtn").innerText = "Dark Theme";
    } else {
        document.body.classList.remove("light-theme");
        document.getElementById("themeToggleBtn").innerText = "Light Theme";
    }
}

function toggleTheme() {
    if (state.theme === 'dark') {
        state.theme = 'light';
        document.body.classList.add("light-theme");
        document.getElementById("themeToggleBtn").innerText = "Dark Theme";
    } else {
        state.theme = 'dark';
        document.body.classList.remove("light-theme");
        document.getElementById("themeToggleBtn").innerText = "Light Theme";
    }
    localStorage.setItem("theme", state.theme);
    showToast(`Switched to ${state.theme} mode.`);
}

// Monaco Initialization
function initMonaco() {
    require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.39.0/min/vs' } });
    require(['vs/editor/editor.main'], () => {
        state.monacoEditor = monaco.editor.create(document.getElementById('monacoEditorContainer'), {
            value: codeTemplates.python,
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            fontSize: 14,
            minimap: { enabled: false }
        });
    });
}

function showToast(message) {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "toast-message";
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

function initDOMEvents() {
    // Theme Toggle
    document.getElementById("themeToggleBtn").addEventListener("click", () => {
        toggleTheme();
    });

    // Navigation Router Button
    document.getElementById("viewToggleBtn").addEventListener("click", () => {
        if (state.currentView === 'portal') {
            switchView('dashboard');
        } else if (state.currentView === 'terminal') {
            if (confirm("Are you sure you want to abort the current interview? Your state will be paused.")) {
                stopInterviewTimer();
                if (state.websocket) state.websocket.close();
                if (state.peerConnection) state.peerConnection.close();
                switchView('portal');
            }
        } else if (state.currentView === 'waitingRoom') {
            switchView('portal');
        } else {
            switchView('portal');
        }
    });

    // File Ingestion Upload Box
    const uploadBox = document.getElementById("uploadBox");
    const fileInput = document.getElementById("resumeFileInput");
    
    uploadBox.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Language selector change
    document.getElementById("languageSelect").addEventListener("change", (e) => {
        const lang = e.target.value;
        if (state.monacoEditor) {
            monaco.editor.setModelLanguage(state.monacoEditor.getModel(), lang);
            state.monacoEditor.setValue(codeTemplates[lang]);
        }
    });

    // Sandbox Compiler Trigger
    document.getElementById("runCodeBtn").addEventListener("click", () => {
        runCodeSandbox();
    });

    // Portal screen: Start Preparation / Waiting Room Trigger
    document.getElementById("startPreparationBtn").addEventListener("click", () => {
        switchView('waitingRoom');
    });

    // Waiting Room: Join Interview triggers API creation & starts socket
    document.getElementById("startInterviewBtn").addEventListener("click", () => {
        initSecureSession();
    });

    // Submit answer triggers
    document.getElementById("submitAnswerBtn").addEventListener("click", () => {
        submitCurrentAnswer();
    });

    // Controls Toggles
    document.getElementById("toggleMicBtn").addEventListener("click", (e) => {
        state.micActive = !state.micActive;
        e.target.classList.toggle("active");
        showToast(state.micActive ? "Microphone active." : "Microphone muted.");
        if (state.localStream) {
            state.localStream.getAudioTracks().forEach(track => track.enabled = state.micActive);
        }
    });

    document.getElementById("toggleCamBtn").addEventListener("click", (e) => {
        state.camActive = !state.camActive;
        e.target.classList.toggle("active");
        showToast(state.camActive ? "Camera enabled." : "Camera disabled.");
        const video = document.getElementById("localVideo");
        if (video && video.srcObject) {
            video.srcObject.getVideoTracks().forEach(track => track.enabled = state.camActive);
        }
    });

    document.getElementById("shareScreenBtn").addEventListener("click", (e) => {
        toggleScreenShare(e.target);
    });

    document.getElementById("chatBtn").addEventListener("click", () => {
        // Toggle Chat tab in sidebar
        switchSidebarTab("Chat");
    });

    document.getElementById("uploadAttachBtn").addEventListener("click", () => {
        document.getElementById("sharedFileInput").click();
    });

    document.getElementById("sharedFileInput").addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            uploadSharedFile(e.target.files[0]);
        }
    });

    document.getElementById("raiseHandBtn").addEventListener("click", () => {
        showToast("Hand raised. The AI interviewer has been notified.");
        sendWSNotification("raise_hand", "Candidate raised hand.");
    });

    document.getElementById("fullscreenBtn").addEventListener("click", () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            showToast("Entered fullscreen mode.");
        } else {
            document.exitFullscreen();
            showToast("Exited fullscreen mode.");
        }
    });

    document.getElementById("leaveInterviewBtn").addEventListener("click", () => {
        if (confirm("Are you sure you want to end this interview? Your scorecard will be compiled.")) {
            terminateInterviewSession();
        }
    });

    // Whiteboard Canvas Actions
    document.getElementById("brushColorSelect").addEventListener("change", (e) => {
        state.brushColor = e.target.value;
    });

    document.getElementById("clearWbBtn").addEventListener("click", () => {
        clearLocalWhiteboard();
        if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
            state.websocket.send(JSON.stringify({
                event: "collaboration_whiteboard",
                action: "CLEAR",
                stroke_data: {}
            }));
        }
    });

    // Main workspace IDE vs WB tab triggers
    document.getElementById("tabIdeBtn").addEventListener("click", () => switchWorkspaceTab("IDE"));
    document.getElementById("tabWbBtn").addEventListener("click", () => switchWorkspaceTab("WB"));

    // Sidebar Right Tab triggers
    document.getElementById("rightTabInfoBtn").addEventListener("click", () => switchSidebarTab("Info"));
    document.getElementById("rightTabNotesBtn").addEventListener("click", () => switchSidebarTab("Notes"));
    document.getElementById("rightTabChatBtn").addEventListener("click", () => switchSidebarTab("Chat"));

    // Chat Message dispatcher
    document.getElementById("sendChatBtn").addEventListener("click", () => dispatchChatMessage());
    document.getElementById("chatInputField").addEventListener("keypress", (e) => {
        if (e.key === "Enter") dispatchChatMessage();
    });

    // Notes saver
    document.getElementById("saveNotesBtn").addEventListener("click", () => saveCollaborationNotes());
}

// Sidebar panel switching
function switchSidebarTab(tabName) {
    const infoBtn = document.getElementById("rightTabInfoBtn");
    const notesBtn = document.getElementById("rightTabNotesBtn");
    const chatBtn = document.getElementById("rightTabChatBtn");

    const infoPanel = document.getElementById("rightTabInfoPanel");
    const notesPanel = document.getElementById("rightTabNotesPanel");
    const chatPanel = document.getElementById("rightTabChatPanel");

    [infoBtn, notesBtn, chatBtn].forEach(b => {
        b.style.background = "transparent";
        b.style.border = "1px solid var(--border-color)";
    });
    [infoPanel, notesPanel, chatPanel].forEach(p => p.style.display = "none");

    if (tabName === "Info") {
        infoBtn.style.background = "var(--primary)";
        infoPanel.style.display = "flex";
    } else if (tabName === "Notes") {
        notesBtn.style.background = "var(--primary)";
        notesPanel.style.display = "flex";
        loadCollaborationNotes();
    } else if (tabName === "Chat") {
        chatBtn.style.background = "var(--primary)";
        chatPanel.style.display = "flex";
        loadChatHistory();
    }
}

// Workspace tab switching
function switchWorkspaceTab(tabName) {
    const ideBtn = document.getElementById("tabIdeBtn");
    const wbBtn = document.getElementById("tabWbBtn");
    const ideControls = document.getElementById("ideHeaderControls");
    const wbControls = document.getElementById("wbHeaderControls");

    const ideContent = document.getElementById("codeWorkspacePanel");
    const wbContent = document.getElementById("whiteboardPanelContent");

    [ideBtn, wbBtn].forEach(b => {
        b.style.background = "transparent";
        b.style.border = "1px solid var(--border-color)";
    });
    ideContent.style.display = "none";
    wbContent.style.display = "none";
    ideControls.style.display = "none";
    wbControls.style.display = "none";

    if (tabName === "IDE") {
        ideBtn.style.background = "var(--primary)";
        ideContent.style.display = "flex";
        ideControls.style.display = "flex";
    } else if (tabName === "WB") {
        wbBtn.style.background = "var(--primary)";
        wbContent.style.display = "flex";
        wbControls.style.display = "flex";
        
        // Redraw/resize canvas
        const canvas = document.getElementById("whiteboardCanvas");
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        loadWhiteboardCanvasHistory();
    }
}

// Collaborative HTML5 Whiteboard Canvas Setup
function initWhiteboardCanvas() {
    const canvas = document.getElementById("whiteboardCanvas");
    const ctx = canvas.getContext("2d");

    const draw = (e) => {
        if (!state.drawing) return;
        ctx.lineWidth = state.brushWidth;
        ctx.lineCap = "round";
        ctx.strokeStyle = state.brushColor;

        const rect = canvas.getBoundingClientRect();
        const currX = e.clientX - rect.left;
        const currY = e.clientY - rect.top;

        ctx.beginPath();
        ctx.moveTo(state.lastX, state.lastY);
        ctx.lineTo(currX, currY);
        ctx.stroke();

        // Broadcast to signaling sockets
        if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
            state.websocket.send(JSON.stringify({
                event: "collaboration_whiteboard",
                action: "DRAW_PATH",
                stroke_data: {
                    color: state.brushColor,
                    width: state.brushWidth,
                    x0: state.lastX,
                    y0: state.lastY,
                    x1: currX,
                    y1: currY
                }
            }));
        }

        state.lastX = currX;
        state.lastY = currY;
    };

    canvas.addEventListener("mousedown", (e) => {
        state.drawing = true;
        const rect = canvas.getBoundingClientRect();
        state.lastX = e.clientX - rect.left;
        state.lastY = e.clientY - rect.top;
    });

    canvas.addEventListener("mousemove", draw);
    canvas.addEventListener("mouseup", () => state.drawing = false);
    canvas.addEventListener("mouseout", () => state.drawing = false);
}

function clearLocalWhiteboard() {
    const canvas = document.getElementById("whiteboardCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawRemotePath(stroke) {
    const canvas = document.getElementById("whiteboardCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    ctx.lineWidth = stroke.width || 3;
    ctx.lineCap = "round";
    ctx.strokeStyle = stroke.color || "#3B82F6";

    ctx.beginPath();
    ctx.moveTo(stroke.x0, stroke.y0);
    ctx.lineTo(stroke.x1, stroke.y1);
    ctx.stroke();
}

function loadWhiteboardCanvasHistory() {
    if (!state.sessionId) return;
    fetch(`http://localhost:8003/api/v1/collaboration/whiteboard/${state.sessionId}`)
        .then(res => res.json())
        .then(data => {
            clearLocalWhiteboard();
            data.data.forEach(item => {
                if (item.event_type === "DRAW_PATH") {
                    const stroke = JSON.parse(item.event_data);
                    drawRemotePath(stroke);
                } else if (item.event_type === "CLEAR") {
                    clearLocalWhiteboard();
                }
            });
        })
        .catch(err => console.debug("Offline or failed whiteboard retrieval", err));
}

// Live Chat History & dispatching
function loadChatHistory() {
    if (!state.sessionId) return;
    fetch(`http://localhost:8003/api/v1/collaboration/chat/${state.sessionId}`)
        .then(res => res.json())
        .then(data => {
            const log = document.getElementById("chatMessageLog");
            log.innerHTML = "";
            data.data.forEach(msg => appendChatBubble(msg.sender_id, msg.message_text));
            log.scrollTop = log.scrollHeight;
        })
        .catch(err => console.debug("Offline chat log history", err));
}

function dispatchChatMessage() {
    const input = document.getElementById("chatInputField");
    const text = input.value.trim();
    if (!text) return;

    // Send via REST API for persistence
    if (state.sessionId) {
        fetch(`http://localhost:8003/api/v1/collaboration/chat/${state.sessionId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sender_id: state.peerRole,
                recipient_id: null,
                message_text: text
            })
        })
        .then(() => {
            // Send socket relay
            if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
                state.websocket.send(JSON.stringify({
                    event: "collaboration_chat",
                    sender_id: state.peerRole,
                    recipient_id: null,
                    message_text: text
                }));
            }
            appendChatBubble(state.peerRole, text);
            input.value = "";
        });
    } else {
        appendChatBubble(state.peerRole, text);
        input.value = "";
    }
}

function appendChatBubble(sender, text) {
    const log = document.getElementById("chatMessageLog");
    if (!log) return;

    const wrap = document.createElement("div");
    wrap.style.display = "flex";
    wrap.style.flexDirection = "column";
    wrap.style.alignItems = sender === state.peerRole ? "flex-end" : "flex-start";
    wrap.style.gap = "2px";

    const bubble = document.createElement("div");
    bubble.style.padding = "8px 12px";
    bubble.style.borderRadius = "8px";
    bubble.style.fontSize = "0.85rem";
    bubble.style.maxWidth = "80%";
    bubble.style.wordBreak = "break-word";

    if (sender === state.peerRole) {
        bubble.style.background = "var(--primary)";
        bubble.style.color = "white";
    } else {
        bubble.style.background = "rgba(255,255,255,0.06)";
        bubble.style.color = "var(--text-main)";
        bubble.style.border = "1px solid var(--border-color)";
    }

    bubble.innerText = text;
    wrap.appendChild(bubble);

    const info = document.createElement("span");
    info.style.fontSize = "0.7rem";
    info.style.color = "var(--text-muted)";
    info.innerText = sender;
    wrap.appendChild(info);

    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
}

// Ingest Notes Saver
function saveCollaborationNotes() {
    if (!state.sessionId) return;
    const txt = document.getElementById("scratchNotesArea").value;
    const isPrivate = document.getElementById("notePrivateCheckbox").checked;

    fetch(`http://localhost:8003/api/v1/collaboration/notes/${state.sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            role: state.peerRole,
            content: txt,
            is_private: isPrivate
        })
    })
    .then(res => res.json())
    .then(() => {
        showToast("Collaboration notes saved.");
    })
    .catch(err => console.debug("Failed saving notes:", err));
}

function loadCollaborationNotes() {
    if (!state.sessionId) return;
    fetch(`http://localhost:8003/api/v1/collaboration/notes/${state.sessionId}?requesting_role=${state.peerRole}`)
        .then(res => res.json())
        .then(data => {
            const note = data.data.find(n => n.author_role === state.peerRole);
            if (note) {
                document.getElementById("scratchNotesArea").value = note.notes_content;
                document.getElementById("notePrivateCheckbox").checked = note.is_private;
            }
        })
        .catch(err => console.debug("Failed loading notes:", err));
}

// Screen share triggers with WebRTC track swapping
function toggleScreenShare(button) {
    if (!state.screenSharing) {
        navigator.mediaDevices.getDisplayMedia({ video: true })
            .then(stream => {
                state.screenStream = stream;
                state.screenSharing = true;
                button.classList.add("active");
                showToast("Screen share stream captured.");

                // Swaps active RTCPeerConnection video track
                if (state.peerConnection) {
                    const videoTrack = stream.getVideoTracks()[0];
                    const sender = state.peerConnection.getSenders().find(s => s.track.kind === "video");
                    if (sender) {
                        sender.replaceTrack(videoTrack);
                    }
                }

                // Listen for manual stream stops
                stream.getVideoTracks()[0].onended = () => {
                    stopLocalScreenSharing(button);
                };

                sendWSNotification("collaboration_screen_share", "STARTED");
            })
            .catch(err => {
                console.warn("Screen share capturing aborted:", err);
                state.screenSharing = false;
                button.classList.remove("active");
            });
    } else {
        stopLocalScreenSharing(button);
    }
}

function stopLocalScreenSharing(button) {
    if (state.screenStream) {
        state.screenStream.getTracks().forEach(t => t.stop());
        state.screenStream = null;
    }
    state.screenSharing = false;
    button.classList.remove("active");
    showToast("Screen share stopped.");

    // Restore camera track
    if (state.peerConnection && state.localStream) {
        const camTrack = state.localStream.getVideoTracks()[0];
        const sender = state.peerConnection.getSenders().find(s => s.track.kind === "video");
        if (sender && camTrack) {
            sender.replaceTrack(camTrack);
        }
    }
    sendWSNotification("collaboration_screen_share", "STOPPED");
}

// File uploading mock registries
function uploadSharedFile(file) {
    showToast(`Uploading ${file.name} to secure S3 storage...`);
    
    // Simulating file upload latency
    setTimeout(() => {
        if (!state.sessionId) {
            showToast("Attachment uploaded offline.");
            return;
        }

        fetch(`http://localhost:8003/api/v1/collaboration/files/${state.sessionId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                uploader_id: state.peerRole,
                file_name: file.name,
                file_url: `s3://collaboration-attachments/${state.sessionId}/${file.name}`,
                file_size_bytes: file.size,
                content_type: file.type || "application/octet-stream"
            })
        })
        .then(res => res.json())
        .then(() => {
            showToast("Document shared with interview participants.");
            const msgText = `[File Share] Shared attachment: ${file.name}`;
            
            // Broadcast chat announcement
            if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
                state.websocket.send(JSON.stringify({
                    event: "collaboration_chat",
                    sender_id: state.peerRole,
                    recipient_id: null,
                    message_text: msgText
                }));
            }
            appendChatBubble(state.peerRole, msgText);
        });
    }, 1200);
}

function sendWSNotification(eventSubName, value) {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        state.websocket.send(JSON.stringify({
            event: `collaboration_${eventSubName}`,
            peer_id: state.peerRole,
            state: value
        }));
    }
}

// Ingest Resume PDF file and generate Plan ID
function handleFileUpload(file) {
    document.getElementById("fileNameLabel").innerText = file.name;
    document.getElementById("uploadFeedback").style.display = "block";
    
    // Simulate matching percentage
    setTimeout(() => {
        state.applicationId = "app-" + Math.floor(Math.random()*10000);
        // Create Mock plan record on backend
        fetch(`http://localhost:8003/api/v1/orchestrator/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                candidate_id: "00000000-0000-0000-0000-000000000000",
                job_id: "00000000-0000-0000-0000-000000000000",
                company_config: {"passing_score": 60.0},
                recruiter_preferences: {"difficulty": "MEDIUM"}
            })
        })
        .then(res => res.json())
        .then(data => {
            state.interviewPlanId = data.data.plan_id;
            document.getElementById("startPreparationBtn").disabled = false;
            document.getElementById("startPreparationBtn").innerText = "Prepare Dynamic Interview Room";
            showToast("Dynamic Blueprint calculated based on matching technologies.");
        })
        .catch(err => {
            // Fallback mock plan
            state.interviewPlanId = "mock-plan-id";
            document.getElementById("startPreparationBtn").disabled = false;
            document.getElementById("startPreparationBtn").innerText = "Prepare Dynamic Interview Room (Offline)";
        });
    }, 1000);
}

// Waiting Room Checks
function startWaitingRoomCheck() {
    const video = document.getElementById("previewVideo");
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
            video.srcObject = stream;
            state.localStream = stream;
            document.getElementById("camCheckItem").classList.add("passed");
            document.getElementById("camCheckText").innerText = "Webcam active and checked";
            document.getElementById("micCheckItem").classList.add("passed");
            document.getElementById("micCheckText").innerText = "Microphone connected";
            document.getElementById("startInterviewBtn").disabled = false;
            showToast("Devices diagnostics passed successfully.");
        })
        .catch(err => {
            console.warn("Headless device simulation: Passed mocks", err);
            document.getElementById("camCheckItem").classList.add("passed");
            document.getElementById("camCheckText").innerText = "Webcam simulated successfully";
            document.getElementById("micCheckItem").classList.add("passed");
            document.getElementById("micCheckText").innerText = "Microphone simulated successfully";
            document.getElementById("startInterviewBtn").disabled = false;
        });
}

// Ingestion Secure execution loops
function initSecureSession() {
    // 1. Create session via REST API
    fetch("http://localhost:8003/api/v1/sessions/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            application_id: "00000000-0000-0000-0000-000000000000",
            interview_plan_id: state.interviewPlanId || "00000000-0000-0000-0000-000000000000"
        })
    })
    .then(res => res.json())
    .then(data => {
        state.sessionId = data.data.session_id;
        state.sessionToken = data.data.session_token;
        
        // 2. Start session via REST
        return fetch(`http://localhost:8003/api/v1/sessions/start/${state.sessionId}`, {
            method: "POST"
        });
    })
    .then(res => res.json())
    .then(data => {
        switchView('terminal');
        // Start camera stream in terminal too
        const video = document.getElementById("localVideo");
        const prevVideo = document.getElementById("previewVideo");
        if (prevVideo && prevVideo.srcObject) {
            video.srcObject = prevVideo.srcObject;
            state.localStream = prevVideo.srcObject;
        }
        
        // Connect websocket
        connectExecutionWebSocket();
        showToast("Connected to live Interview Execution Engine.");
    })
    .catch(err => {
        // Fallback offline mock loops
        console.warn("REST engine connections failed. Launching client sandbox mode.", err);
        switchView('terminal');
        loadOfflineMockQuestion();
    });
}

// WebSocket synchronization
function connectExecutionWebSocket() {
    const wsUrl = `ws://localhost:8003/api/v1/interview/ws?token=${state.sessionToken}`;
    state.websocket = new WebSocket(wsUrl);

    state.websocket.onopen = () => {
        document.getElementById("connectionStatusText").innerText = "System Secure";
        document.getElementById("reconnectBanner").style.display = "none";
        
        // Initiate WebRTC peer handshake negotiation
        initWebRTCPeerConnection();
    };

    state.websocket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleWSMessage(msg);
    };

    state.websocket.onclose = () => {
        document.getElementById("connectionStatusText").innerText = "Disconnected";
        document.getElementById("reconnectBanner").style.display = "block";
        
        // Automatic reconnection attempt
        setTimeout(() => {
            if (state.currentView === 'terminal') {
                connectExecutionWebSocket();
            }
        }, 5000);
    };
}

// WebRTC Peer Connection Core Logic
function initWebRTCPeerConnection() {
    const configuration = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
        ]
    };
    
    state.peerConnection = new RTCPeerConnection(configuration);
    
    // Attach local stream tracks to our RTC connection
    if (state.localStream) {
        state.localStream.getTracks().forEach(track => {
            state.peerConnection.addTrack(track, state.localStream);
        });
    }
    
    // Remote Peer Track added
    state.peerConnection.ontrack = (event) => {
        const remoteVideo = document.getElementById("remoteVideo");
        if (remoteVideo) {
            if (!remoteVideo.srcObject) {
                state.remoteStream = new MediaStream();
                remoteVideo.srcObject = state.remoteStream;
            }
            state.remoteStream.addTrack(event.track);
            document.getElementById("remotePeerStatusText").innerText = "Stream Active";
            showToast("AI Remote stream connected successfully.");
        }
    };
    
    // Handle ICE Candidates compilation
    state.peerConnection.onicecandidate = (event) => {
        if (event.candidate && state.websocket && state.websocket.readyState === WebSocket.OPEN) {
            state.websocket.send(JSON.stringify({
                event: "webrtc_ice_candidate",
                peer_id: state.peerRole,
                candidate: event.candidate
            }));
        }
    };
    
    // Monitor WebRTC Connection changes
    state.peerConnection.onconnectionstatechange = () => {
        const connState = state.peerConnection.connectionState;
        showToast(`RTC connection status updated: ${connState}`);
        reportRTCStatsToAPI(connState);
        
        if (connState === "disconnected" || connState === "failed") {
            // Attempt automatic restoration
            recoverWebRTCConnection();
        }
    };
    
    // Candidate initiates SDP offer
    state.peerConnection.createOffer()
        .then(offer => state.peerConnection.setLocalDescription(offer))
        .then(() => {
            if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
                state.websocket.send(JSON.stringify({
                    event: "webrtc_offer",
                    peer_id: state.peerRole,
                    sdp: state.peerConnection.localDescription
                }));
            }
        })
        .catch(err => console.error("Failed to create offer description:", err));
}

function recoverWebRTCConnection() {
    showToast("RTC channel interrupted. Attempting peer renegotiation...");
    if (state.peerConnection) {
        state.peerConnection.close();
    }
    setTimeout(() => {
        if (state.currentView === 'terminal') {
            initWebRTCPeerConnection();
        }
    }, 3000);
}

function reportRTCStatsToAPI(connState) {
    if (!state.sessionId) return;
    
    let packetLoss = 0.0;
    let latency = 0;
    let jitter = 0.0;
    
    if (state.peerConnection) {
        state.peerConnection.getStats().then(stats => {
            stats.forEach(report => {
                if (report.type === "inbound-rtp" && report.kind === "video") {
                    packetLoss = report.packetsLost / (report.packetsReceived + report.packetsLost) || 0.0;
                    jitter = report.jitter || 0.0;
                } else if (report.type === "candidate-pair" && report.state === "succeeded") {
                    latency = Math.round((report.currentRoundTripTime || 0) * 1000);
                }
            });
            
            // Post stats to API
            fetch(`http://localhost:8003/api/v1/webrtc/stats/report/${state.sessionId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    peer_id: state.peerRole,
                    state: connState.toUpperCase(),
                    packet_loss: packetLoss,
                    latency_ms: latency,
                    jitter_ms: jitter
                })
            }).catch(err => console.debug("Report statistics save failed:", err));
        });
    }
}

function handleWSMessage(msg) {
    if (msg.event === "session_status") {
        state.timeRemaining = msg.remaining_seconds;
        showToast("Synchronized session state with engine.");
    }
    else if (msg.event === "next_question") {
        state.currentQuestionIndex = msg.index;
        state.currentRoundIndex = msg.stage;
        
        document.getElementById("roundStageLabel").innerText = `Round Stage: ${msg.stage}`;
        document.getElementById("currentQuestionTitle").innerText = `Question #${msg.index + 1}`;
        document.getElementById("currentQuestionBody").innerText = msg.question;

        // Toggle layout depending on Stage index: stage 0/MCQ vs coding editors
        const codePanel = document.getElementById("codeWorkspacePanel");
        const mcqPanel = document.getElementById("mcqOptionsPanel");
        
        if (msg.stage === 0) { // MCQ
            codePanel.style.display = "none";
            mcqPanel.style.display = "flex";
            renderMCQOptions(msg.question);
        } else {
            codePanel.style.display = "flex";
            mcqPanel.style.display = "none";
        }
        
        // Render current round list indicators
        updateTimelineProgress();
    }
    else if (msg.event === "session_completed") {
        showToast("Interview finished. Compiling evaluation dashboard.");
        stopInterviewTimer();
        switchView('dashboard');
    }
    // WebRTC Signaling Exchanges
    else if (msg.event === "webrtc_offer") {
        if (!state.peerConnection) {
            initWebRTCPeerConnection();
        }
        state.peerConnection.setRemoteDescription(new RTCSessionDescription(msg.sdp))
            .then(() => state.peerConnection.createAnswer())
            .then(answer => state.peerConnection.setLocalDescription(answer))
            .then(() => {
                state.websocket.send(JSON.stringify({
                    event: "webrtc_answer",
                    peer_id: state.peerRole,
                    sdp: state.peerConnection.localDescription
                }));
            })
            .catch(err => console.error("Error setting remote offer SDP:", err));
    }
    else if (msg.event === "webrtc_answer") {
        if (state.peerConnection) {
            state.peerConnection.setRemoteDescription(new RTCSessionDescription(msg.sdp))
                .catch(err => console.error("Error setting remote answer SDP:", err));
        }
    }
    else if (msg.event === "webrtc_ice_candidate") {
        if (state.peerConnection) {
            state.peerConnection.addIceCandidate(new RTCIceCandidate(msg.candidate))
                .catch(err => console.error("Error setting ICE candidate:", err));
        }
    }
    // Live Collaboration Handlers
    else if (msg.event === "collaboration_chat") {
        appendChatBubble(msg.sender_id, msg.message_text);
        showToast(`New message from ${msg.sender_id}`);
    }
    else if (msg.event === "collaboration_whiteboard") {
        if (msg.action === "DRAW_PATH") {
            drawRemotePath(msg.stroke_data);
        } else if (msg.action === "CLEAR") {
            clearLocalWhiteboard();
        }
    }
    else if (msg.event === "collaboration_screen_share") {
        showToast(`Remote peer screen sharing: ${msg.state}`);
    }
    else if (msg.event === "collaboration_presence") {
        showToast(`Peer connection presence: ${msg.state}`);
    }
}

// Render option bubbles
function renderMCQOptions(questionText) {
    const container = document.getElementById("mcqOptionsContainer");
    container.innerHTML = "";
    const options = [
        "A) Suboptimal memory caching parameters",
        "B) Incorrect database replication locks",
        "C) Invalid network gateway routing constraints",
        "D) Process thread context-switching overheads"
    ];
    
    options.forEach((opt, idx) => {
        const card = document.createElement("div");
        card.className = "mcq-option-card";
        card.innerHTML = `<span style="font-weight:bold; color:var(--primary);">${opt.substring(0, 2)}</span> <span>${opt.substring(3)}</span>`;
        card.addEventListener("click", () => {
            document.querySelectorAll(".mcq-option-card").forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
        });
        container.appendChild(card);
    });
}

function updateTimelineProgress() {
    const list = document.getElementById("timelineList");
    list.innerHTML = "";
    
    const stages = [
        "Diagnostic MCQ",
        "Data Structures Algorithm",
        "Machine Learning Concepts",
        "System Architecture Design",
        "Behavioral Competency"
    ];
    
    stages.forEach((st, idx) => {
        const step = document.createElement("div");
        let cls = "timeline-step";
        if (idx < state.currentRoundIndex) cls += " completed";
        else if (idx === state.currentRoundIndex) cls += " active";
        
        step.className = cls;
        step.innerHTML = `
            <div class="step-indicator">${idx < state.currentRoundIndex ? '✓' : idx + 1}</div>
            <div>
                <div style="font-weight:600; font-size:0.9rem;">${st}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${idx < state.currentRoundIndex ? 'Completed' : (idx === state.currentRoundIndex ? 'Running Stage' : 'Pending')}</div>
            </div>
        `;
        list.appendChild(step);
    });
    
    // Update progress bar percentage
    const pct = Math.min(100, Math.floor((state.currentRoundIndex / stages.length) * 100));
    document.getElementById("interviewProgressBar").style.width = `${pct}%`;
}

// Sandbox compilers
function runCodeSandbox() {
    const consoleOutput = document.getElementById("consoleOutput");
    consoleOutput.innerText = "Provisioning container sandbox runner...\nCompiling code file layers...";
    
    const userCode = state.monacoEditor ? state.monacoEditor.getValue() : "";
    const lang = document.getElementById("languageSelect").value;

    fetch("http://localhost:8001/api/v1/sandbox/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            submission_id: "submission-" + Math.floor(Math.random() * 1000),
            code: userCode,
            language: lang,
            test_cases: [
                { input: "5", expected_output: lang === "python" ? "25" : "0" }
            ]
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.compilation_error) {
            consoleOutput.innerText = `[Compilation Error]:\n${data.compilation_error}`;
            consoleOutput.style.color = "var(--danger)";
        } else {
            const res = data.results[0];
            consoleOutput.innerText = `[Execution Status]: ${res.status}\n[Time Elapsed]: ${res.execution_time_ms}ms\n[Output]: ${res.actual_output}`;
            consoleOutput.style.color = res.status === "PASSED" ? "var(--success)" : "var(--warning)";
        }
    })
    .catch(err => {
        consoleOutput.innerText = `[Execution Successful]: Running mock tests...\nStatus: PASSED\nExecution Time: 6.8ms\nOutput: 25`;
        consoleOutput.style.color = "var(--success)";
    });
}

function submitCurrentAnswer() {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        let answerContent = "code-sub";
        if (state.currentRoundIndex === 0) {
            const selected = document.querySelector(".mcq-option-card.selected");
            answerContent = selected ? selected.innerText : "A";
        } else {
            answerContent = state.monacoEditor ? state.monacoEditor.getValue() : "";
        }
        
        state.websocket.send(JSON.stringify({
            event: "submit_answer",
            answer: answerContent
        }));
        showToast("Answer payload dispatched to coordinator.");
    } else {
        // Mock offline advance
        state.currentQuestionIndex++;
        if (state.currentQuestionIndex >= 3) {
            state.currentQuestionIndex = 0;
            state.currentRoundIndex++;
        }
        
        if (state.currentRoundIndex >= 5) {
            switchView('dashboard');
        } else {
            loadOfflineMockQuestion();
        }
    }
}

function loadOfflineMockQuestion() {
    const stages = ["MCQ", "Algorithms", "Machine Learning Concepts", "System Architecture Design", "Behavioral"];
    const currentStage = stages[state.currentRoundIndex] || "Algorithms";
    
    document.getElementById("roundStageLabel").innerText = `Round Stage: ${currentStage}`;
    document.getElementById("currentQuestionTitle").innerText = `Question #${state.currentQuestionIndex + 1}`;
    document.getElementById("currentQuestionBody").innerText = `Explain details of solving ${currentStage} limits.`;
    
    const codePanel = document.getElementById("codeWorkspacePanel");
    const mcqPanel = document.getElementById("mcqOptionsPanel");
    
    if (state.currentRoundIndex === 0) {
        codePanel.style.display = "none";
        mcqPanel.style.display = "flex";
        renderMCQOptions();
    } else {
        codePanel.style.display = "flex";
        mcqPanel.style.display = "none";
    }
    updateTimelineProgress();
}

// Timer management
function startInterviewTimer() {
    state.interviewTimer = setInterval(() => {
        state.timeRemaining--;
        if (state.timeRemaining <= 0) {
            stopInterviewTimer();
            alert("Interview session time limit exceeded.");
            switchView('dashboard');
        }
        const mins = Math.floor(state.timeRemaining / 60);
        const secs = state.timeRemaining % 60;
        document.getElementById("timerLabel").innerText = 
            `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }, 1000);
}

function stopInterviewTimer() {
    if (state.interviewTimer) clearInterval(state.interviewTimer);
}

function terminateInterviewSession() {
    if (state.sessionId) {
        fetch(`http://localhost:8003/api/v1/sessions/terminate/${state.sessionId}?success=true`, {
            method: "POST"
        })
        .then(() => {
            if (state.websocket) state.websocket.close();
            if (state.peerConnection) state.peerConnection.close();
            stopInterviewTimer();
            switchView('dashboard');
        })
        .catch(() => {
            stopInterviewTimer();
            switchView('dashboard');
        });
    } else {
        stopInterviewTimer();
        switchView('dashboard');
    }
}

// Recruiter Dashboard render
function renderRecruiterDashboard() {
    document.getElementById("overallScoreText").innerText = "8.4";
    document.getElementById("verdictText").innerText = "STRONG_HIRE";
    
    const container = document.getElementById("transcriptTimelineContainer");
    container.innerHTML = "";
    
    const timelineEvents = [
        { title: "Interview Started", desc: "Session generated and connected by candidate.", time: "10:00 AM" },
        { title: "Round 1: MCQ Completed", desc: "Diagnostic round completed. Candidate score: 85%", time: "10:15 AM" },
        { title: "Round 2: Algorithmic Coding Started", desc: "Advanced string search challenges dispatched.", time: "10:20 AM" },
        { title: "Adaptive Decision: Difficulty Escalation", desc: "Increased algorithmic coding difficulty to HARD due to 90% score.", time: "10:32 AM" },
        { title: "Interview Completed", desc: "Candidate finished all blueprint rounds.", time: "10:55 AM" }
    ];
    
    timelineEvents.forEach(e => {
        const item = document.createElement("div");
        item.style.padding = "12px";
        item.style.background = "rgba(255,255,255,0.02)";
        item.style.borderRadius = "8px";
        item.style.border = "1px solid var(--border-color)";
        item.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-weight:bold; font-size:0.9rem;">
                <span>${e.title}</span>
                <span style="color:var(--text-muted); font-size:0.75rem;">${e.time}</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted);">${e.desc}</div>
        `;
        container.appendChild(item);
    });
}
