// services/sandbox-runner/src/main.rs
use serde::{Deserialize, Serialize};
use std::convert::Infallible;
use std::process::Stdio;
use std::time::Duration;
use tokio::process::Command;
use tokio::time::timeout;
use warp::Filter;

#[derive(Deserialize, Serialize, Debug)]
struct TestCase {
    input: String,
    expected_output: String,
}

#[derive(Deserialize, Debug)]
struct ExecutionRequest {
    submission_id: String,
    code: String,
    language: String,
    test_cases: Vec<TestCase>,
}

#[derive(Serialize, Debug)]
struct TestCaseResult {
    status: String, // PASSED, FAILED, TIMEOUT, RUNTIME_ERROR
    actual_output: String,
    execution_time_ms: u128,
}

#[derive(Serialize, Debug)]
struct ExecutionResponse {
    submission_id: String,
    executed: bool,
    results: Vec<TestCaseResult>,
    compilation_error: Option<String>,
    limits_exceeded: bool,
}

async fn execute_handler(req: ExecutionRequest) -> Result<impl warp::Reply, Infallible> {
    let mut results = Vec::new();
    let mut compilation_error = None;
    let mut limits_exceeded = false;

    // Simulate writing code to temporary disk location
    let filename = format!("/tmp/solution_{}.py", req.submission_id);
    if let Err(e) = std::fs::write(&filename, &req.code) {
        return Ok(warp::reply::json(&ExecutionResponse {
            submission_id: req.submission_id,
            executed: false,
            results: vec![],
            compilation_error: Some(format!("Sandbox write failed: {}", e)),
            limits_exceeded: false,
        }));
    }

    // Process each test case
    for test in req.test_cases {
        let start = std::time::Instant::now();

        // Spawn sandbox run simulation (e.g. executing the Python solution with strict limit constraints)
        // In full production, this runs under a docker container or gVisor sandbox container target.
        let child_process = Command::new("python3")
            .arg(&filename)
            .arg(&test.input)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .kill_on_drop(true)
            .spawn();

        match child_process {
            Ok(child) => {
                // Apply CPU / Process Execution timeout (max 2 seconds limit)
                let timeout_duration = Duration::from_secs(2);
                let wait_result = timeout(timeout_duration, child.wait_with_output()).await;

                let duration = start.elapsed().as_millis();

                match wait_result {
                    Ok(Ok(output)) => {
                        let actual = String::from_utf8_lossy(&output.stdout).trim().to_string();
                        let error = String::from_utf8_lossy(&output.stderr).trim().to_string();

                        if !output.status.success() {
                            compilation_error = Some(error.clone());
                            results.push(TestCaseResult {
                                status: "RUNTIME_ERROR".to_string(),
                                actual_output: error,
                                execution_time_ms: duration,
                            });
                        } else if actual == test.expected_output {
                            results.push(TestCaseResult {
                                status: "PASSED".to_string(),
                                actual_output: actual,
                                execution_time_ms: duration,
                            });
                        } else {
                            results.push(TestCaseResult {
                                status: "FAILED".to_string(),
                                actual_output: actual,
                                execution_time_ms: duration,
                            });
                        }
                    }
                    Ok(Err(e)) => {
                        results.push(TestCaseResult {
                            status: "RUNTIME_ERROR".to_string(),
                            actual_output: format!("Execution failure: {}", e),
                            execution_time_ms: duration,
                        });
                    }
                    Err(_) => {
                        // Timeout exceeded, the child process is automatically dropped and killed
                        limits_exceeded = true;
                        results.push(TestCaseResult {
                            status: "TIMEOUT".to_string(),
                            actual_output: "Execution exceeded 2.0s sandbox CPU time limit.".to_string(),
                            execution_time_ms: duration,
                        });
                    }
                }
            }
            Err(e) => {
                results.push(TestCaseResult {
                    status: "RUNTIME_ERROR".to_string(),
                    actual_output: format!("Failed to spawn runner compiler environment: {}", e),
                    execution_time_ms: 0,
                });
            }
        }
    }

    // Clean up file
    let _ = std::fs::remove_file(&filename);

    Ok(warp::reply::json(&ExecutionResponse {
        submission_id: req.submission_id,
        executed: true,
        results,
        compilation_error,
        limits_exceeded,
    }))
}

#[tokio::main]
async fn main() {
    let execute_route = warp::post()
        .and(warp::path("api"))
        .and(warp::path("v1"))
        .and(warp::path("sandbox"))
        .and(warp::path("execute"))
        .and(warp::body::json())
        .and_then(execute_handler);

    let health_route = warp::get()
        .and(warp::path("health"))
        .map(|| warp::reply::json(&serde_json::json!({ "status": "healthy", "service": "sandbox-runner" })));

    let routes = execute_route.or(health_route);

    println!("Sandbox Runner listening on port 8001...");
    warp::serve(routes).run(([0, 0, 0, 0], 8001)).await;
}
