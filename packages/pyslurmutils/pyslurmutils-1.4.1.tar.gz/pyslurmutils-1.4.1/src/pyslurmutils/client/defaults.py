import socket

JOB_NAME: str = f"pyslurmutils.{socket.gethostname()}"  # keep filename friendly
PYTHON_CMD: str = "python3"
SHEBANG: str = "#!/bin/bash -l"  # Assume Slurm is Linux
SLURM_TEMPDIR: str = "/tmp"  # Assume Slurm is Linux
SLURM_ARGUMENTS_NAME: str = "slurm_arguments"
MIN_PORT: int = 59000
NUM_PORTS: int = 100
DEFAULT_API_VERSION = "v0.0.42"
