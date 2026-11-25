import os
import time

import httpx


API_URL = "https://api.onlinecompiler.io/api/run-code-sync/"

COMPILERS = {
    "c": "gcc-15",
    "cpp": "g++-15",
    "python": "python-3.14",
    "java": "openjdk-25",
    "javascript": "nodejs-24",
}

TIME_LIMIT = 30
MAX_CODE_SIZE = 50_000
MAX_INPUT_SIZE = 50_000
MAX_OUTPUT_SIZE = 64 * 1024


def run_online(
    source_code: str,
    custom_input: str = "",
    language: str = "",
):
    start_time = time.monotonic()

    def result(
        status,
        output,
        execution_time_ms=0,
        return_code=None,
        memory_usage_mb=None,
    ):
        return {
            "status": status,
            "output": output,
            "execution_time_ms": round(execution_time_ms, 2),
            "return_code": return_code,
            "memory_usage_mb": memory_usage_mb,
        }

    # Validate source code.
    if not source_code.strip():
        return result("error", "No source code provided.")

    if len(source_code.encode("utf-8")) > MAX_CODE_SIZE:
        return result("error", "Source code exceeds the size limit.")

    if len(custom_input.encode("utf-8")) > MAX_INPUT_SIZE:
        return result("error", "Input exceeds the size limit.")

    compiler = COMPILERS.get(language)

    if not compiler:
        return result("error", f"Language '{language}' is not supported.")

    api_key = os.getenv("ONLINECOMPILER_API_KEY")

    if not api_key:
        return result(
            "error",
            "Code execution service is not configured. API key is missing.",
        )

    payload = {
        "compiler": compiler,
        "code": source_code,
        "input": custom_input,
        "time_limit": TIME_LIMIT,
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=35.0,
        )

        elapsed_ms = (time.monotonic() - start_time) * 1000

        if response.status_code == 401 or response.status_code == 403:
            return result(
                "error",
                "Code execution service rejected the API key. Check the backend configuration.",
                elapsed_ms,
            )

        if response.status_code == 429:
            return result(
                "error",
                "Code execution service rate limit reached. Please try again later.",
                elapsed_ms,
            )

        if response.status_code >= 400:
            return result(
                "error",
                f"Code execution service returned HTTP {response.status_code}.",
                elapsed_ms,
            )

        data = response.json()

        stdout = data.get("output") or ""
        stderr = data.get("error") or ""

        # Keep stdout and stderr visible in the existing output panel.
        output = stdout

        if stderr:
            if output and not output.endswith("\n"):
                output += "\n"
            output += stderr

        if data.get("truncated"):
            output += "\nOutput was truncated because it exceeded the output limit."

        output = output[:MAX_OUTPUT_SIZE]

        exit_code = data.get("exit_code")

        try:
            execution_time_ms = float(
                data.get("total") or data.get("time") or 0
            ) * 1000
        except (TypeError, ValueError):
            execution_time_ms = elapsed_ms

        try:
            memory_usage_mb = (
                round(float(data["memory"]) / 1024, 2)
                if data.get("memory") is not None
                else None
            )
        except (TypeError, ValueError):
            memory_usage_mb = None

        if exit_code == 124:
            status = "timeout"
            output = output or "Program exceeded the time limit."

        elif exit_code == 0 and data.get("status") == "success":
            status = "success"

        elif exit_code is not None and exit_code != 0:
            if language in ("c", "cpp", "java") and stderr:
                status = "compilation_error"
            else:
                status = "runtime_error"

        else:
            status = "error"

        return result(
            status,
            output,
            execution_time_ms,
            exit_code,
            memory_usage_mb,
        )

    except httpx.TimeoutException:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return result(
            "timeout",
            "The code execution service took too long to respond.",
            elapsed_ms,
        )

    except httpx.RequestError:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return result(
            "error",
            "Could not connect to the code execution service. Please try again.",
            elapsed_ms,
        )

    except (ValueError, KeyError):
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return result(
            "error",
            "Received an invalid response from the code execution service.",
            elapsed_ms,
        )