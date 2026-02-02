import datetime
import getpass
import os
import pathlib
import secrets
import shutil
import socket
import sys
from contextlib import ExitStack
from typing import Generator
from typing import Optional
from unittest.mock import patch

import jwt
import pytest

from .mock_slurm import mock_slurm_clients


def pytest_addoption(parser):
    parser.addoption(
        "--slurm-root-directory",
        action="store",
        default=None,
        help="Specify the SLURM root directory for logs and data.",
    )
    parser.addoption(
        "--slurm-api-version",
        action="store",
        default=None,
        help="Specify the SLURM API version.",
    )
    parser.addoption(
        "--slurm-pre-script",
        action="store",
        default=None,
        help="Execute at the start of the SLURM job.",
    )


@pytest.fixture(scope="session")
def slurm_root_directory(tmp_path_factory, request) -> pathlib.Path:
    path = request.config.getoption("--slurm-root-directory")
    if path:
        return pathlib.Path(path)
    return tmp_path_factory.mktemp("slurm_root")


@pytest.fixture(scope="session", params=["mock", "production"])
def slurm_parameters(request, tmp_path_factory):
    api_version = request.config.getoption("--slurm-api-version")
    pre_script = request.config.getoption("--slurm-pre-script")

    if request.param == "mock":
        with _patch_mock_defaults(tmp_path_factory):
            params = _get_mock_parameters()
            params.update(api_version=api_version, pre_script=pre_script)
            yield params

    elif request.param == "production":
        params = _get_production_parameters(request)
        params.update(api_version=api_version, pre_script=pre_script)
        yield params

    else:
        raise ValueError(request.param)


def _patch_mock_defaults(tmp_path_factory):
    from pyslurmutils.client import defaults

    stack = ExitStack()
    tmp_dir = tmp_path_factory.mktemp("slurm_tempdir")
    stack.enter_context(patch.object(defaults, "SLURM_TEMPDIR", str(tmp_dir)))

    if sys.platform == "win32":
        from pyslurmutils.client.rest import pyconn

        stack.enter_context(
            patch.object(pyconn, "_create_script", pyconn._create_windows_script)
        )
        stack.enter_context(patch.object(defaults, "SHEBANG", "#!powershell"))
        stack.enter_context(patch.object(defaults, "PYTHON_CMD", "python"))

    return stack


def _get_mock_parameters():
    return {
        "mock": True,
        "url": "http://mockhost",
        "user_name": "mockuser",
        "token": _create_mock_token("mockuser"),
        "api_version": None,  # will be overwritten by the fixture
        "pre_script": None,  # will be overwritten by the fixture
    }


def _get_production_parameters(request):
    url = os.environ.get("SLURM_URL")
    if not url:
        pytest.skip("SLURM_URL environment variable required")

    user_name = os.environ.get("SLURM_USER") or getpass.getuser()
    token = os.environ.get("SLURM_TOKEN")
    renewal_url = os.environ.get("SLURM_RENEWAL_URL")
    if not token and not renewal_url:
        pytest.skip("SLURM_TOKEN or SLURM_RENEWAL_URL environment variable required")

    slurm_root_directory = request.config.getoption("--slurm-root-directory")
    if not slurm_root_directory:
        pytest.skip("--slurm-root-directory pytest argument is required")

    return {
        "mock": False,
        "url": url,
        "user_name": user_name,
        "token": token,
        "renewal_url": renewal_url,
        "api_version": None,  # will be overwritten by the fixture
        "pre_script": None,  # will be overwritten by the fixture
    }


def _create_mock_token(username: str = "mockuser", exp_seconds: int = 3600) -> str:
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "exp": now_utc + datetime.timedelta(seconds=exp_seconds),
        "iat": now_utc,
    }
    secret = secrets.token_bytes(
        32
    )  # Not used during decode (since signature verification is off)
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(scope="session")
def slurm_log_directory(
    slurm_root_directory, tmp_path_factory, slurm_parameters
) -> pathlib.Path:
    if slurm_parameters["mock"]:
        return tmp_path_factory.mktemp("slurm_logs")
    return slurm_root_directory / slurm_parameters["user_name"] / "slurm_logs"


@pytest.fixture(scope="session")
def slurm_data_directory(
    slurm_root_directory, tmp_path_factory, slurm_parameters
) -> Optional[pathlib.Path]:
    if slurm_parameters["mock"]:
        return tmp_path_factory.mktemp("slurm_data")
    return slurm_root_directory / slurm_parameters["user_name"] / "slurm_data"


@pytest.fixture()
def slurm_tmp_path(
    slurm_root_directory, tmp_path, slurm_parameters
) -> Generator[pathlib.Path, None, None]:
    if slurm_parameters["mock"]:
        yield tmp_path
    else:
        tmp_path = (
            pathlib.Path(slurm_root_directory)
            / slurm_parameters["user_name"]
            / "pyslurmutils"
            / tmp_path.parent.stem
            / tmp_path.stem
        )
        tmp_path.mkdir(parents=True, exist_ok=True)
        yield tmp_path
        shutil.rmtree(tmp_path.parent, ignore_errors=True)


@pytest.fixture(scope="session")
def mock_job_name():
    job_name = f"pyslurmutils.unittest.{socket.gethostname()}"
    with patch("pyslurmutils.client.defaults.JOB_NAME", job_name):
        yield job_name


@pytest.fixture(scope="session")
def slurm_client_kwargs(
    slurm_log_directory, tmp_path_factory, slurm_parameters, mock_job_name
) -> Generator[dict, None, None]:
    # This fixture must remain a session scope fixture for third-party libraries

    params = dict(slurm_parameters)
    _ = params.pop("mock")
    params["log_directory"] = slurm_log_directory
    if slurm_parameters["mock"]:
        tmp_path = tmp_path_factory.mktemp("slurm_mock")
        with mock_slurm_clients(tmp_path, slurm_parameters):
            yield params
    else:
        yield params
