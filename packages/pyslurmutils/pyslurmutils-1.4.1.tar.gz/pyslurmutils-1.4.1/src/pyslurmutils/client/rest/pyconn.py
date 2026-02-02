"""SLURM API to submit, cancel and monitor scripts that start a python process
to establish a connection over which python functions can be executed."""

import logging
import os
import uuid
from typing import Optional
from typing import Union

from .. import defaults
from ..job_io.local import RemoteWorkerProxy
from .script import SlurmScriptRestClient

logger = logging.getLogger(__name__)


class SlurmPyConnRestClient(SlurmScriptRestClient):
    """SLURM API to submit, cancel and monitor scripts that start a python process
    to establish a connection over which python functions can be executed.
    This class does not contain any job-related state."""

    def __init__(
        self,
        url: str = "",
        user_name: str = "",
        token: str = "",
        api_version: str = "",
        renewal_url: str = "",
        parameters: Optional[dict] = None,
        log_directory: Optional[str] = None,
        std_split: Optional[bool] = False,
        request_options: Optional[dict] = None,
        pre_script: Optional[str] = None,
        post_script: Optional[str] = None,
        python_cmd: Optional[str] = None,
        use_os_environment: bool = True,
    ):
        """
        :param url: SLURM REST API URL (fallback to SLURM_URL env)
        :param user_name: SLURM username (fallback to SLURM_USER or system user)
        :param token: SLURM JWT token (fallback to SLURM_TOKEN env)
        :param api_version: SLURM API version (e.g. 'v0.0.41')
        :param renewal_url: Url for SLURM JWT token renewal (fallback to SLURM_RENEWAL_URL env)
        :param parameters: SLURM job parameters
        :param log_directory: SLURM log directory
        :param std_split: Split standard output and standard error
        :param request_options: GET, POST and DELETE options
        :param pre_script: Shell script to execute at the start of a job
        :param post_script: Shell script to execute at the end of a job
        :param python_cmd: Python command
        """
        self.pre_script = pre_script
        self.post_script = post_script
        self.python_cmd = python_cmd
        super().__init__(
            url=url,
            user_name=user_name,
            token=token,
            api_version=api_version,
            renewal_url=renewal_url,
            parameters=parameters,
            log_directory=log_directory,
            std_split=std_split,
            request_options=request_options,
            use_os_environment=use_os_environment,
        )

    def submit_script(
        self,
        worker_proxy: RemoteWorkerProxy,
        pre_script: Optional[str] = None,
        post_script: Optional[str] = None,
        python_cmd: Optional[str] = None,
        parameters: Optional[dict] = None,
        metadata: Optional[Union[str, dict]] = None,
        request_options: Optional[dict] = None,
    ) -> int:
        """Submit a script that will establish a connection initialized in the current process."""
        if parameters is None:
            parameters = dict()

        environment = parameters.setdefault("environment", dict())
        environment.update(worker_proxy.remote_environment)

        if not metadata:
            metadata = dict()
        metadata.update(worker_proxy.metadata)

        script = self._make_executable(
            worker_proxy.remote_script(),
            pre_script=pre_script,
            post_script=post_script,
            python_cmd=python_cmd,
        )

        return super().submit_script(
            script=script,
            parameters=parameters,
            metadata=metadata,
            request_options=request_options,
        )

    def _make_executable(
        self,
        python_script: str,
        pre_script: Optional[str] = None,
        post_script: Optional[str] = None,
        python_cmd: Optional[str] = None,
    ) -> str:
        """Create the code of a shell script that writes a Python script to disk,
        executes it, and then cleans it up.

        This is needed because scripts that use multiprocessing with the 'spawn'
        start method cannot reliably be executed via:
        - a shebang (e.g., `#!/usr/bin/env python3`)
        - stdin pipes (e.g., `python3 <<'EOF' ... EOF`)

        By writing the Python code to a real temporary file, we ensure that
        spawned child processes can import the main module safely.
        """
        pre_script = pre_script or self.pre_script or ""
        post_script = post_script or self.post_script or ""
        python_cmd = python_cmd or self.python_cmd or defaults.PYTHON_CMD

        # if not pre_script and not post_script:
        #     return f"#!/usr/bin/env {python_cmd}\n{python_script}"

        tmp_script = os.path.join(
            defaults.SLURM_TEMPDIR, f"pyslurmutils_main_{uuid.uuid4().hex}.py"
        )

        return _create_script(
            tmp_script, pre_script, python_cmd, python_script, post_script
        )


def _create_linux_script(
    tmp_script, pre_script, python_cmd, python_script, post_script
):
    """
    Create the code of a bash script that writes a Python script to disk,
    executes it, and then cleans it up.

    - Uses a `cat <<'PYTHONEOF' ... PYTHONEOF` block so that variables,
      backticks, and special characters in the Python code are not expanded
      or interpolated by the shell.
    - Use `exec` so the Python process inherits the same PID and will
      directly receive any signals (e.g., `SIGTERM`, `SIGINT`) sent to the
      Slurm job.
    """

    return f"""
{pre_script}
tmp_script="{tmp_script}"

cat > "$tmp_script" <<'PYTHONEOF'
{python_script}
PYTHONEOF

echo "Shell PID: $$"

exec {python_cmd} "$tmp_script"

rm -f "$tmp_script"

{post_script}
"""


def _create_windows_script(
    tmp_script, pre_script, python_cmd, python_script, post_script
):
    """
    Create the code of a Windows batch script that writes a Python script to disk,
    executes it, and then cleans it up.

    - Uses PowerShell heredoc (`@' ... '@`) to avoid problems with `echo`
      and special characters in the Python code.
    """

    return f"""
{pre_script}

$TmpScript = "{tmp_script}"

@'
{python_script}
'@ | Set-Content -Path $TmpScript -Encoding UTF8

Write-Output "PowerShell PID: $PID"

& {python_cmd} $TmpScript

Remove-Item -Force $TmpScript

{post_script}
"""


_create_script = _create_linux_script
