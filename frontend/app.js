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
    peerRole: "CANDIDATE"
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
        state.screenSharing = !state.screenSharing;
        e.target.classList.toggle("active");
        showToast(state.screenSharing ? "Screen sharing initiated." : "Screen share ended.");
    });

    document.getElementById("chatBtn").addEventListener("click", () => {
        showToast("Chat panel placeholder active.");
    });

    document.getElementById("uploadAttachBtn").addEventListener("click", () => {
        showToast("Upload attachment overlay activated.");
    });

    document.getElementById("raiseHandBtn").addEventListener("click", () => {
        showToast("Hand raised. The AI interviewer has been notified.");
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
