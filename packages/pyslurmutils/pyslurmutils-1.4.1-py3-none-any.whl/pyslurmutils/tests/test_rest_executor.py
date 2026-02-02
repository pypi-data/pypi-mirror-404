import os
import sys
import time

import pytest

from ..client import os_utils
from ..client.errors import RemoteExit
from ..concurrent.futures import SlurmRestExecutor


@pytest.fixture(params=["tcp", "file"])
def slurm_executor_kwargs(
    request, slurm_data_directory, slurm_client_kwargs, slurm_parameters
):
    if request.param == "tcp":
        slurm_data_directory = None
    elif not slurm_parameters["mock"]:
        request.node.add_marker(
            pytest.mark.xfail(reason="Distributed filesystems I/O is not reliable")
        )
    return {"data_directory": slurm_data_directory, **slurm_client_kwargs}


def test_rest_executor_submit(slurm_executor_kwargs):
    with SlurmRestExecutor(**slurm_executor_kwargs, max_workers=8) as slurm_executor:
        future1 = slurm_executor.submit(time.sleep, 0)
        future2 = slurm_executor.submit(sum, [1, 1])
        future3 = slurm_executor.submit(sum, [1, "a"])
        assert future1.result(timeout=60) is None
        assert future2.result(timeout=60) == 2
        with pytest.raises(TypeError):
            future3.result(timeout=60)


def test_rest_executor_map(slurm_executor_kwargs):
    with SlurmRestExecutor(**slurm_executor_kwargs, max_workers=8) as slurm_executor:
        results = [
            result
            for result in slurm_executor.map(sum, [[1, 1], [2, 2], [3, 3]], timeout=60)
        ]
    assert results == [2, 4, 6], str(results)


def test_rest_executor_initializer(slurm_executor_kwargs):
    with SlurmRestExecutor(
        **slurm_executor_kwargs,
        initializer=_initializer,
        max_workers=1,
        max_tasks_per_worker=5,
    ) as slurm_executor:
        ftls = [slurm_executor.submit(_increment_global_value) for _ in range(5)]
        results = {future.result(timeout=60) for future in ftls}
    assert results == set(range(1, 6)), str(results)


def _initializer():
    global GLOBAL_VALUE
    GLOBAL_VALUE = 0


def _increment_global_value():
    global GLOBAL_VALUE
    GLOBAL_VALUE += 1
    return GLOBAL_VALUE


def test_rest_executor_max_tasks_per_worker(slurm_executor_kwargs):
    with SlurmRestExecutor(
        **slurm_executor_kwargs, max_workers=8, max_tasks_per_worker=2
    ) as slurm_executor:
        # Note: the sleep time is needed to ensure jobs don't finish
        # before the submit for-loop is finished. In production this
        # does not matter but here we want to test `max_tasks_per_worker`.

        # Each worker executes one job.
        ftls = [slurm_executor.submit(_job_ident) for _ in range(8)]
        job_idents = {future.result(timeout=60) for future in ftls}
        assert len(job_idents) == 8, str(len(job_idents))

        # Each worker executes another job.
        ftls = [slurm_executor.submit(_job_ident) for _ in range(8)]
        job_idents |= {future.result(timeout=60) for future in ftls}
        assert len(job_idents) == 8, str(len(job_idents))

        # Each worker needs to be restarted because it has reached
        # the `max_tasks_per_worker` limit.
        ftls = [slurm_executor.submit(_job_ident) for _ in range(8)]
        job_idents |= {future.result(timeout=60) for future in ftls}
        assert len(job_idents) == 16, str(len(job_idents))


def _job_ident():
    time.sleep(0.3)
    return os.environ["SLURM_JOB_ID"]


@pytest.mark.parametrize("abort_delay", [0, 0.1, 1])
@pytest.mark.skipif(
    sys.platform == "win32", reason="Signal propagation not reliable on Windows"
)
def test_rest_executor_cancel(slurm_executor_kwargs, abort_delay):
    with SlurmRestExecutor(**slurm_executor_kwargs, max_workers=8) as slurm_executor:
        future = slurm_executor.submit(time.sleep, 10)
        if abort_delay:
            time.sleep(abort_delay)
        future.abort()

        with pytest.raises(RemoteExit, match=r"SLURM job \d+ CANCELLED"):
            future.result(timeout=60)


def test_slurm_tmp_path(slurm_executor_kwargs, slurm_tmp_path):
    print(slurm_tmp_path)
    filename = slurm_tmp_path / "test.txt"
    with SlurmRestExecutor(**slurm_executor_kwargs) as slurm_executor:
        future = slurm_executor.submit(_touch, str(filename))
        _ = future.result(timeout=60)
    os_utils.nfs_cache_refresh(slurm_tmp_path)
    assert filename.exists()


def _touch(filename):
    with open(filename, "w"):
        pass
