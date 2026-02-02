"""
Secure Probe Runner

Executes environment probes with safety controls:
- Command whitelist
- No shell execution
- Timeout protection
- Minimal environment
"""

import asyncio
import os
import re
import shutil
import subprocess
from pathlib import Path

from hearth_worker.probes.path import build_safe_path, resolve_command
from hearth_worker.probes.registry import BUILTIN_PROBES, COMMAND_WHITELIST
from hearth_worker.probes.types import ProbeResult


class SecureProbeRunner:
    def __init__(self, extra_path: list[str] | None = None):
        self.safe_path = build_safe_path(extra_path)

    async def run_probes(self, probe_names: list[str]) -> list[ProbeResult]:
        results = []
        for name in probe_names:
            try:
                result = await self.run_probe(name)
                results.append(result)
            except Exception as e:
                results.append(ProbeResult(probe=name, found=False, error=str(e)))
        return results

    async def run_probe(self, probe_name: str) -> ProbeResult:
        if probe_name not in BUILTIN_PROBES:
            return ProbeResult(probe=probe_name, found=False, error="Unknown probe")

        spec = BUILTIN_PROBES[probe_name]
        probe_type = spec.get("type")

        if probe_type == "command_version":
            return await self._run_command_probe(probe_name, spec)
        elif probe_type == "builtin":
            return await self._run_builtin_probe(probe_name, spec)
        elif probe_type == "read_file":
            return await self._run_file_probe(probe_name, spec)
        elif probe_type == "python_import":
            return await self._run_python_import(probe_name, spec)
        elif probe_type == "env_var":
            return self._run_env_var(probe_name, spec)
        else:
            return ProbeResult(
                probe=probe_name, found=False, error=f"Unknown probe type: {probe_type}"
            )

    async def _run_command_probe(self, probe_name: str, spec: dict) -> ProbeResult:
        command = spec["command"]

        if command not in COMMAND_WHITELIST:
            return ProbeResult(probe=probe_name, found=False, error="Command not in whitelist")

        exe_path = resolve_command(command, self.safe_path)
        if not exe_path:
            return ProbeResult(probe=probe_name, found=False, error="Command not found")

        env = {
            "PATH": self.safe_path,
            "LANG": "C",
            "LC_ALL": "C",
            "HOME": str(Path.home()),
        }

        args = spec.get("args", [])
        proc: asyncio.subprocess.Process | None = None
        try:
            proc = await asyncio.create_subprocess_exec(
                exe_path,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        except asyncio.TimeoutError:
            if proc is not None:
                proc.kill()
                await proc.wait()
            return ProbeResult(probe=probe_name, found=False, path=exe_path, error="Timeout")
        except Exception as e:
            return ProbeResult(probe=probe_name, found=False, path=exe_path, error=str(e))

        output = (stdout or b"") + (stderr or b"")
        text = output.decode("utf-8", errors="replace")

        version = None
        if "version_regex" in spec:
            match = re.search(spec["version_regex"], text)
            if match:
                version = match.group(1)

        return ProbeResult(
            probe=probe_name,
            found=proc.returncode == 0,
            path=exe_path,
            version=version,
            raw=text[:2000],
        )

    async def _run_builtin_probe(self, probe_name: str, spec: dict) -> ProbeResult:
        handler = spec.get("handler")
        if handler == "detect_nvidia_gpu":
            return await self._detect_nvidia_gpu(probe_name)
        return ProbeResult(probe=probe_name, found=False, error=f"Unknown handler: {handler}")

    async def _detect_nvidia_gpu(self, probe_name: str) -> ProbeResult:
        nvidia_smi = resolve_command("nvidia-smi", self.safe_path)
        if not nvidia_smi:
            return ProbeResult(probe=probe_name, found=False, error="nvidia-smi not found")

        env = {"PATH": self.safe_path, "LANG": "C", "HOME": str(Path.home())}

        proc: asyncio.subprocess.Process | None = None
        try:
            proc = await asyncio.create_subprocess_exec(
                nvidia_smi,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        except asyncio.TimeoutError:
            if proc is not None:
                proc.kill()
                await proc.wait()
            return ProbeResult(probe=probe_name, found=False, error="Timeout")
        except Exception as e:
            return ProbeResult(probe=probe_name, found=False, error=str(e))

        if proc.returncode != 0:
            return ProbeResult(probe=probe_name, found=False, error="nvidia-smi failed")

        lines = stdout.decode().strip().split("\n")
        gpus = []
        for line in lines:
            parts = line.split(", ")
            if len(parts) >= 2:
                try:
                    gpus.append(
                        {
                            "name": parts[0].strip(),
                            "memory_mb": int(parts[1].strip()),
                        }
                    )
                except ValueError:
                    continue

        return ProbeResult(
            probe=probe_name,
            found=True,
            path=nvidia_smi,
            extra={"gpus": gpus, "gpu_count": len(gpus)},
        )

    async def _run_file_probe(self, probe_name: str, spec: dict) -> ProbeResult:
        for path in spec.get("paths", []):
            try:
                content = Path(path).read_text()[:4096]
                return ProbeResult(probe=probe_name, found=True, path=path, raw=content)
            except Exception:
                continue
        return ProbeResult(probe=probe_name, found=False, error="File not found")

    async def _run_python_import(self, probe_name: str, spec: dict) -> ProbeResult:
        module = spec["module"]
        version_attr = spec.get("version_attr", "__version__")

        python = resolve_command("python3", self.safe_path)
        if not python:
            return ProbeResult(probe=probe_name, found=False, error="python3 not found")

        code = f"import {module}; print(getattr({module}, '{version_attr}', 'unknown'))"

        try:
            proc = await asyncio.create_subprocess_exec(
                python,
                "-c",
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PATH": self.safe_path, "LANG": "C", "HOME": str(Path.home())},
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        except asyncio.TimeoutError:
            return ProbeResult(probe=probe_name, found=False, error="Timeout")
        except Exception as e:
            return ProbeResult(probe=probe_name, found=False, error=str(e))

        if proc.returncode != 0:
            return ProbeResult(probe=probe_name, found=False, error="Import failed")

        version = stdout.decode().strip()
        return ProbeResult(probe=probe_name, found=True, version=version)

    def _run_env_var(self, probe_name: str, spec: dict) -> ProbeResult:
        name = spec["name"]
        value = os.environ.get(name)
        if value:
            return ProbeResult(probe=probe_name, found=True, extra={"value": value})
        return ProbeResult(probe=probe_name, found=False)
