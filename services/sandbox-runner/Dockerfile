# services/sandbox-runner/Dockerfile
FROM rust:latest

WORKDIR /app

# Install Python 3 for spawning runner subprocesses
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    && rm -rf /var/lib/apt/lists/*

COPY Cargo.toml /app/Cargo.toml
COPY src /app/src

RUN cargo build --release

EXPOSE 8001

CMD ["/app/target/release/sandbox-runner"]
