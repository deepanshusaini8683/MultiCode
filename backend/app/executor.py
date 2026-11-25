import os
import time
import uuid
import selectors
import subprocess
import base64


# Execution limits
TIME_LIMIT = 30
MEMORY_LIMIT = "256m"
MAX_CODE_SIZE = 50_000
MAX_INPUT_SIZE = 50_000
MAX_OUTPUT_SIZE = 64 * 1024


def _run_program(
    source_code: str,
    custom_input: str = "",
    *,
    docker_image: str,
    source_file: str,
    execution_command: str,
):
    # Validate source code
    if not source_code.strip():
        return {
            "status": "error",
            "output": "No source code provided.",
            "execution_time_ms": 0,
            "return_code": None,
            "memory_usage_mb": None,
        }

    if len(source_code.encode("utf-8")) > MAX_CODE_SIZE:
        return {
            "status": "error",
            "output": "Source code exceeds the size limit.",
            "execution_time_ms": 0,
            "return_code": None,
            "memory_usage_mb": None,
        }

    if len(custom_input.encode("utf-8")) > MAX_INPUT_SIZE:
        return {
            "status": "error",
            "output": "Input exceeds the size limit.",
            "execution_time_ms": 0,
            "return_code": None,
            "memory_usage_mb": None,
        }

    container_name = f"multicode-{uuid.uuid4().hex[:12]}"
    memory_marker = f"__MULTICODE_MEMORY_{uuid.uuid4().hex}__="

    encoded_code = base64.b64encode(
        source_code.encode("utf-8")
    ).decode("ascii")

    # Capture container peak memory when the shell exits.
    shell_script = (
        f"trap 'printf \"\\n{memory_marker}%s\\n\" "
        "\"$(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo 0)\"' EXIT; "
        f"printf '%s' '{encoded_code}' | base64 -d "
        f"> /workspace/{source_file} && "
        f"{execution_command}"
    )

    command = [
        "docker", "run",
        "--rm",
        "--name", container_name,
        "-i",
        "--network", "none",
        "--memory", MEMORY_LIMIT,
        "--memory-swap", MEMORY_LIMIT,
        "--cpus", "1",
        "--pids-limit", "64",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "10001:10001",
        "--tmpfs",
        "/workspace:rw,exec,nosuid,nodev,size=32m,uid=10001,gid=10001,mode=700",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=16m,uid=10001,gid=10001",
        "--ulimit", "cpu=8:8",
        "--ulimit", "fsize=1048576:1048576",
        "--ulimit", "nofile=64:64",
        docker_image,
        "sh", "-c",
        shell_script
    ]

    process = None
    selector = None
    output_chunks = []
    output_size = 0

    timed_out = False
    output_exceeded = False
    start_time = time.monotonic()

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        # Send custom input to the program.
        process.stdin.write(custom_input.encode("utf-8"))
        process.stdin.close()
        process.stdin = None

        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)

        deadline = time.monotonic() + TIME_LIMIT

        while selector.get_map():
            remaining = deadline - time.monotonic()

            if remaining <= 0 and process.poll() is None:
                timed_out = True
                break

            events = selector.select(
                timeout=max(0, min(0.2, remaining))
            )

            for key, _ in events:
                chunk = os.read(key.fd, 4096)

                if not chunk:
                    selector.unregister(key.fileobj)
                    continue

                output_size += len(chunk)

                if output_size > MAX_OUTPUT_SIZE:
                    output_exceeded = True
                    break

                output_chunks.append(chunk)

            if output_exceeded:
                break

            if not events and process.poll() is not None:
                break

        # Stop containers that exceed execution limits.
        if timed_out or output_exceeded:
            subprocess.run(
                ["docker", "kill", container_name],
                capture_output=True,
                timeout=3
            )

        return_code = process.wait(timeout=3)

        execution_time = round(
            (time.monotonic() - start_time) * 1000,
            2
        )

        # Extract peak memory measurement.
        raw_output = b"".join(output_chunks)

        peak_memory_bytes = None
        marker = memory_marker.encode("utf-8")
        filtered_output = []

        for line in raw_output.splitlines(keepends=True):
            if line.startswith(marker):
                try:
                    peak_memory_bytes = int(
                        line[len(marker):].strip()
                    )
                except ValueError:
                    pass
            else:
                filtered_output.append(line)

        output = b"".join(filtered_output).decode(
            "utf-8",
            errors="replace"
        )

        peak_memory_mb = (
            round(peak_memory_bytes / (1024 * 1024), 2)
            if peak_memory_bytes is not None
            else None
        )

        # Handle execution results.
        if timed_out:
            return {
                "status": "timeout",
                "output": (
                    f"Program exceeded the {TIME_LIMIT}-second time limit."
                ),
                "execution_time_ms": execution_time,
                "return_code": None,
                "memory_usage_mb": peak_memory_mb,
            }

        if output_exceeded:
            return {
                "status": "error",
                "output": "Program exceeded the output limit.",
                "execution_time_ms": execution_time,
                "return_code": return_code,
                "memory_usage_mb": peak_memory_mb,
            }

        if return_code == 100:
            return {
                "status": "compilation_error",
                "output": output,
                "execution_time_ms": execution_time,
                "return_code": return_code,
                "memory_usage_mb": peak_memory_mb,
            }

        if return_code != 0:
            return {
                "status": "runtime_error",
                "output": output,
                "execution_time_ms": execution_time,
                "return_code": return_code,
                "memory_usage_mb": peak_memory_mb,
            }

        return {
            "status": "success",
            "output": output,
            "execution_time_ms": execution_time,
            "return_code": return_code,
            "memory_usage_mb": peak_memory_mb,
        }

    except Exception as error:
        return {
            "status": "error",
            "output": str(error),
            "execution_time_ms": round(
                (time.monotonic() - start_time) * 1000,
                2
            ),
            "return_code": None,
            "memory_usage_mb": None,
        }

    finally:
        if selector:
            selector.close()

        if process:
            if process.poll() is None:
                process.kill()
                process.wait()

            if process.stdout:
                process.stdout.close()

        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            timeout=5
        )


# C++ execution
def run_cpp(source_code: str, custom_input: str = ""):
    return _run_program(
        source_code,
        custom_input,
        docker_image="multicode-cpp",
        source_file="main.cpp",
        execution_command=(
            "g++ -std=c++17 -O2 -pipe "
            "/workspace/main.cpp -o /workspace/program "
            "2> /workspace/compile_errors.txt; "
            "compile_status=$?; "
            "if [ $compile_status -ne 0 ]; then "
            "cat /workspace/compile_errors.txt; "
            "exit 100; "
            "fi; "
            "/workspace/program"
        )
    )


# C execution
def run_c(source_code: str, custom_input: str = ""):
    return _run_program(
        source_code,
        custom_input,
        docker_image="multicode-c",
        source_file="main.c",
        execution_command=(
            "gcc -std=c17 -O2 -pipe "
            "/workspace/main.c -o /workspace/program "
            "2> /workspace/compile_errors.txt; "
            "compile_status=$?; "
            "if [ $compile_status -ne 0 ]; then "
            "cat /workspace/compile_errors.txt; "
            "exit 100; "
            "fi; "
            "/workspace/program"
        )
    )


# Python execution
def run_python(source_code: str, custom_input: str = ""):
    return _run_program(
        source_code,
        custom_input,
        docker_image="multicode-python",
        source_file="main.py",
        execution_command="python3 /workspace/main.py"
    )


# Java execution
def run_java(source_code: str, custom_input: str = ""):
    return _run_program(
        source_code,
        custom_input,
        docker_image="multicode-java",
        source_file="Main.java",
        execution_command=(
            "javac Main.java 2> /workspace/compile_errors.txt; "
            "compile_status=$?; "
            "if [ $compile_status -ne 0 ]; then "
            "cat /workspace/compile_errors.txt; "
            "exit 100; "
            "fi; "
            "java Main"
        )
    )


# JavaScript execution
def run_javascript(source_code: str, custom_input: str = ""):
    return _run_program(
        source_code,
        custom_input,
        docker_image="multicode-javascript",
        source_file="main.js",
        execution_command="node /workspace/main.js"
    )
