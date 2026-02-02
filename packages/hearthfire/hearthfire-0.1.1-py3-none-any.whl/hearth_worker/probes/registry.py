"""
Probe Registry

Defines available probes with command names (not paths).
Paths are resolved dynamically using shutil.which().
"""

BUILTIN_PROBES = {
    "python.version": {
        "type": "command_version",
        "command": "python3",
        "args": ["--version"],
        "version_regex": r"Python (\d+\.\d+\.\d+)",
    },
    "uv.version": {
        "type": "command_version",
        "command": "uv",
        "args": ["--version"],
        "version_regex": r"uv (\d+\.\d+\.\d+)",
    },
    "node.version": {
        "type": "command_version",
        "command": "node",
        "args": ["--version"],
        "version_regex": r"v(\d+\.\d+\.\d+)",
    },
    "pnpm.version": {
        "type": "command_version",
        "command": "pnpm",
        "args": ["--version"],
        "version_regex": r"(\d+\.\d+\.\d+)",
    },
    "java.version": {
        "type": "command_version",
        "command": "java",
        "args": ["-version"],
        "version_regex": r'version "(\d+)',
    },
    "docker.version": {
        "type": "command_version",
        "command": "docker",
        "args": ["--version"],
        "version_regex": r"Docker version (\d+\.\d+\.\d+)",
    },
    "conda.version": {
        "type": "command_version",
        "command": "conda",
        "args": ["--version"],
        "version_regex": r"conda (\d+\.\d+\.\d+)",
    },
    "cargo.version": {
        "type": "command_version",
        "command": "cargo",
        "args": ["--version"],
        "version_regex": r"cargo (\d+\.\d+\.\d+)",
    },
    "go.version": {
        "type": "command_version",
        "command": "go",
        "args": ["version"],
        "version_regex": r"go(\d+\.\d+\.\d+)",
    },
    "nvidia.gpu": {
        "type": "builtin",
        "handler": "detect_nvidia_gpu",
    },
    "nvidia.cuda": {
        "type": "command_version",
        "command": "nvcc",
        "args": ["--version"],
        "version_regex": r"release (\d+\.\d+)",
    },
    "nvidia.driver": {
        "type": "command_version",
        "command": "nvidia-smi",
        "args": ["--query-gpu=driver_version", "--format=csv,noheader"],
        "version_regex": r"(\d+\.\d+)",
    },
    "os.release": {
        "type": "read_file",
        "paths": ["/etc/os-release"],
        "parser": "parse_os_release",
    },
    "python.torch": {
        "type": "python_import",
        "module": "torch",
        "version_attr": "__version__",
    },
    "python.tensorflow": {
        "type": "python_import",
        "module": "tensorflow",
        "version_attr": "__version__",
    },
    "env.cuda_home": {
        "type": "env_var",
        "name": "CUDA_HOME",
    },
}

COMMAND_WHITELIST = {
    "python3",
    "python",
    "python3.10",
    "python3.11",
    "python3.12",
    "uv",
    "pip",
    "pip3",
    "pipx",
    "node",
    "npm",
    "pnpm",
    "yarn",
    "java",
    "javac",
    "docker",
    "podman",
    "conda",
    "mamba",
    "cargo",
    "rustc",
    "go",
    "nvcc",
    "nvidia-smi",
    "git",
}
