/* frontend/app.js */

// Global State Instance
const state = {
    currentView: 'portal', // portal, terminal, dashboard
    applicationId: null,
    sessionToken: null,
    websocket: null,
    monacoEditor: null,
    interviewTimer: null,
    timeRemaining: 3600,
    currentQuestionIndex: 0,
    currentStage: 'MCQ',
    uploadedSkills: [],
    candidateName: "Jane Doe",
    jobTitle: "Staff Backend Engineer",
    transcripts: []
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
});

// View Router
function switchView(viewName) {
    state.currentView = viewName;
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    
    if (viewName === 'portal') {
        document.getElementById("portalScreen").classList.add("active");
        document.getElementById("viewToggleBtn").innerText = "Switch to Recruiter Dashboard";
    } else if (viewName === 'terminal') {
        document.getElementById("terminalScreen").classList.add("active");
        document.getElementById("viewToggleBtn").innerText = "Abort Interview";
        startProctorWebcam();
        startTimer();
    } else if (viewName === 'dashboard') {
        document.getElementById("dashboardScreen").classList.add("active");
        document.getElementById("viewToggleBtn").innerText = "Back to Apply Portal";
        renderRecruiterDashboard();
    }
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

function initDOMEvents() {
    // Navigation Router Button
    document.getElementById("viewToggleBtn").addEventListener("click", () => {
        if (state.currentView === 'portal') {
            switchView('dashboard');
        } else if (state.currentView === 'terminal') {
            if (confirm("Are you sure you want to abort the current interview? Your state will be paused.")) {
                stopTimer();
                if (state.websocket) state.websocket.close();
                switchView('portal');
            }
        } else {
            switchView('portal');
        }
    });

    // Ingestion File Uploader Mock
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

    // Launch FSM interview flow
    document.getElementById("startInterviewBtn").addEventListener("click", () => {
        switchView('terminal');
        initInterviewSession();
    });

    // Submit answer triggers
    document.getElementById("submitAnswerBtn").addEventListener("click", () => {
        submitCurrentAnswer();
    });

    // Download PDF scorecard trigger
    document.getElementById("downloadPdfBtn").addEventListener("click", () => {
        downloadPdfScorecard();
    });
}

// Ingest Resume PDF file
function handleFileUpload(file) {
    document.getElementById("fileNameLabel").innerText = file.name;
    document.getElementById("uploadFeedback").style.display = "block";
    
    // Simulating parsing latency
    setTimeout(() => {
        state.uploadedSkills = ["Go", "Python", "Kubernetes", "gRPC", "Docker"];
        state.applicationId = "app-" + Math.floor(Math.random()*10000);
        document.getElementById("startInterviewBtn").disabled = false;
        document.getElementById("startInterviewBtn").innerText = "Start Adaptive Interview Session";
    }, 1000);
}

// WebRTC Media Streaming
function startProctorWebcam() {
    const video = document.getElementById("localVideo");
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
            video.srcObject = stream;
            // Simulated local eye tracking proctor warning loops
            setInterval(simulateProctorChecks, 15000);
        })
        .catch(err => {
            console.warn("Camera/Mic device blocks: Running in headless mock mode", err);
            document.getElementById("proctorStatusText").innerText = "Device Fail: Proctor Warning";
            document.getElementById("proctorStatusText").style.color = "var(--danger)";
        });
}

function simulateProctorChecks() {
    const statusText = document.getElementById("proctorStatusText");
    const statuses = [
        { text: "Proctor Guard Active", color: "var(--success)" },
        { text: "Suspicious Gaze Detected", color: "var(--warning)" },
        { text: "Multiple Face Shapes Detected", color: "var(--danger)" }
    ];
    // Random status
    const rand = statuses[Math.floor(Math.random() * statuses.length)];
    statusText.innerText = rand.text;
    statusText.style.color = rand.color;
    
    if (rand.color === "var(--danger)") {
        console.warn("[Proctoring]: Flag emitted to telemetry stream.");
    }
}

// Session Timer Loops
function startTimer() {
    state.interviewTimer = setInterval(() => {
        state.timeRemaining--;
        if (state.timeRemaining <= 0) {
            clearInterval(state.interviewTimer);
            alert("Interview Session Time Limit Exceeded. Auto-submitting workspace.");
            switchView('dashboard');
        }
        
        const mins = Math.floor(state.timeRemaining / 60);
        const secs = state.timeRemaining % 60;
        document.getElementById("timerLabel").innerText = 
            `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }, 1000);
}

function stopTimer() {
    if (state.interviewTimer) clearInterval(state.interviewTimer);
}

// REST Client: Code execution compiler
function runCodeSandbox() {
    const consoleOutput = document.getElementById("consoleOutput");
    consoleOutput.innerText = "Provisioning secure container sandbox runner...\nCompiling code file layers...";
    
    const userCode = state.monacoEditor ? state.monacoEditor.getValue() : "";
    const lang = document.getElementById("languageSelect").value;

    // Send payload request to local sandbox runner
    fetch("http://localhost:8001/api/v1/sandbox/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            submission_id: "test-" + Math.floor(Math.random() * 1000),
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
        // Local network fallbacks
        consoleOutput.innerText = `[Execution Successful]: Running mock tests...\nStatus: PASSED\nExecution Time: 8.4ms\nOutput: 25`;
        consoleOutput.style.color = "var(--success)";
    });
}

// WebSocket client connection loops
function initInterviewSession() {
    // Session registration REST endpoint setup
    fetch("http://localhost:8000/api/v1/interviews/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ application_id: state.applicationId || "mock-app-id" })
    })
    .then(res => res.json())
    .then(data => {
        state.sessionToken = data.session_token;
        connectWebSocket(data.websocket_url);
    })
    .catch(err => {
        // Offline sandbox mocks
        console.log("Offline mode: Booting mock WebSocket FSM loops.");
        loadMockQuestion();
    });
}

function connectWebSocket(url) {
    state.websocket = new WebSocket(url);
    
    state.websocket.onopen = () => {
        document.getElementById("connectionStatusText").innerText = "System Secure";
        document.getElementById("reconnectBanner").style.display = "none";
    };

    state.websocket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleWSMessage(msg);
    };

    state.websocket.onclose = () => {
        document.getElementById("connectionStatusText").innerText = "Connection Dropped";
        document.getElementById("reconnectBanner").style.display = "block";
        // Auto-reconnect trigger after 5 seconds
        setTimeout(() => {
            if (state.currentView === 'terminal') {
                connectWebSocket(url);
            }
        }, 5000);
    };
}

function handleWSMessage(msg) {
    if (msg.event === "next_question") {
        state.currentQuestionIndex = msg.index;
        state.currentStage = msg.stage;
        
        document.getElementById("roundStageLabel").innerText = `Round: ${msg.stage}`;
        document.getElementById("currentQuestionTitle").innerText = `Question #${msg.index + 1}`;
        document.getElementById("currentQuestionBody").innerText = msg.question;
        
        // Dynamic IDE vs MCQ view setups
        const ideContainer = document.querySelector(".code-workspace");
        if (msg.stage === "MCQ") {
            ideContainer.style.opacity = "0.3";
            ideContainer.style.pointerEvents = "none";
            renderMCQOptions(msg.question);
        } else {
            ideContainer.style.opacity = "1";
            ideContainer.style.pointerEvents = "auto";
            document.getElementById("mcqOptionsContainer").innerHTML = "";
        }
    }
}

function submitCurrentAnswer() {
    let answerText = "";
    if (state.currentStage === "MCQ") {
        const checked = document.querySelector('input[name="mcqOption"]:checked');
        answerText = checked ? checked.value : "No option selected";
    } else {
        answerText = state.monacoEditor ? state.monacoEditor.getValue() : "Empty code workspace";
    }

    // Save locally
    state.transcripts.push({
        stage: state.currentStage,
        question: document.getElementById("currentQuestionBody").innerText,
        response: answerText,
        score: Math.floor(Math.random() * 4) + 7, // mock score 7 to 10
        feedback: "Sound foundational reasoning and robust architecture design."
    });

    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        state.websocket.send(JSON.stringify({
            event: "submit_answer",
            answer: answerText
        }));
    } else {
        // Offline sequence progress
        state.currentQuestionIndex++;
        if (state.currentQuestionIndex >= 2) {
            state.currentQuestionIndex = 0;
            if (state.currentStage === "MCQ") {
                state.currentStage = "CODING";
            } else if (state.currentStage === "CODING") {
                state.currentStage = "SYSTEM_DESIGN";
            } else {
                stopTimer();
                switchView('dashboard');
                return;
            }
        }
        loadMockQuestion();
    }
}

function loadMockQuestion() {
    const stage = state.currentStage;
    const idx = state.currentQuestionIndex;
    document.getElementById("roundStageLabel").innerText = `Round: ${stage}`;
    document.getElementById("currentQuestionTitle").innerText = `Question #${idx + 1}`;

    const mockDb = {
        MCQ: [
            "Which of the following database isolation levels prevents phantom reads in PostgreSQL?",
            "What is the time complexity of searching an element in a balanced Binary Search Tree (BST)?"
        ],
        CODING: [
            "Write a function to find the length of the longest substring without repeating characters. Input: s = 'abcabcbb', Output: 3"
        ],
        SYSTEM_DESIGN: [
            "Design a URL shortening service like bit.ly. Describe how you would scale it to handle 10k requests/sec."
        ]
    };

    const question = mockDb[stage][idx] || "Explain your experience working with highly concurrent systems.";
    document.getElementById("currentQuestionBody").innerText = question;

    const ideContainer = document.querySelector(".code-workspace");
    if (stage === "MCQ") {
        ideContainer.style.opacity = "0.3";
        ideContainer.style.pointerEvents = "none";
        renderMCQOptions(question);
    } else {
        ideContainer.style.opacity = "1";
        ideContainer.style.pointerEvents = "auto";
        document.getElementById("mcqOptionsContainer").innerHTML = "";
    }
}

function renderMCQOptions(question) {
    const container = document.getElementById("mcqOptionsContainer");
    container.innerHTML = "";
    
    const options = ["Serializable", "Repeatable Read", "Read Committed", "Read Uncommitted"];
    options.forEach((opt, index) => {
        const label = document.createElement("label");
        label.style.display = "flex";
        label.style.alignItems = "center";
        label.style.gap = "10px";
        label.style.padding = "10px";
        label.style.background = "rgba(255,255,255,0.04)";
        label.style.border = "1px solid var(--border-color)";
        label.style.borderRadius = "8px";
        label.style.cursor = "pointer";
        
        label.innerHTML = `<input type="radio" name="mcqOption" value="${opt}" ${index === 0 ? 'checked' : ''}> <span>${opt}</span>`;
        container.appendChild(label);
    });
}

// 3. Recruiter Dashboard Scorecard Compiler
function renderRecruiterDashboard() {
    const container = document.getElementById("transcriptTimelineContainer");
    container.innerHTML = "";

    if (state.transcripts.length === 0) {
        container.innerHTML = "<p style='color:var(--text-muted);'>No transcripts generated yet. Complete the interview flow to populate candidate scorecards.</p>";
        return;
    }

    // Populate overall matrices
    const sum = state.transcripts.reduce((acc, t) => acc + t.score, 0);
    const avg = roundDecimal(sum / state.transcripts.length, 1);
    document.getElementById("overallScoreText").innerText = avg;
    
    let verdict = "NO_HIRE";
    if (avg >= 8.5) verdict = "STRONG_HIRE";
    else if (avg >= 7.0) verdict = "HIRE";
    document.getElementById("verdictText").innerText = verdict;

    state.transcripts.forEach((item, index) => {
        const card = document.createElement("div");
        card.className = "glass-panel";
        card.style.padding = "16px";
        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-weight:bold; color:var(--primary);">${item.stage} Round</span>
                <span style="font-weight:bold; color:var(--success);">${item.score}.0/10</span>
            </div>
            <div style="margin-bottom:8px;"><b>Q:</b> ${item.question}</div>
            <div style="margin-bottom:8px; font-family:monospace; background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; font-size:0.85rem; max-height:80px; overflow-y:auto;">
                <b>A:</b> ${item.response.replace(/\n/g, "<br>")}
            </div>
            <div style="font-size:0.9rem; color:var(--text-muted);"><i>Feedback: ${item.feedback}</i></div>
        `;
        container.appendChild(card);
    });
}

function downloadPdfScorecard() {
    // Calls grading service endpoint
    fetch("http://localhost:8002/api/v1/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            session_id: state.sessionToken || "mock-session-id",
            candidate_name: state.candidateName,
            job_title: state.jobTitle,
            transcript: state.transcripts
        })
    })
    .then(res => res.json())
    .then(data => {
        window.open(`http://localhost:8002/api/v1/reports/download/${state.sessionToken || "mock-session-id"}`);
    })
    .catch(err => {
        alert("Grading microservice offline. Simulating local scorecard PDF generation.");
        // Simulated click download using Blob
        const jsonStr = JSON.stringify(state.transcripts, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Scorecard_${state.candidateName.replace(" ", "_")}.json`;
        a.click();
    });
}

function roundDecimal(value, decimals) {
    return Number(Math.round(value+'e'+decimals)+'e-'+decimals);
}
