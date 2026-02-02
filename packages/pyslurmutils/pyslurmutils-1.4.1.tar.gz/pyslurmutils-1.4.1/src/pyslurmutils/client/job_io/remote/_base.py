import abc
import hashlib
import importlib
import logging
import os
import pickle
import shutil
import sys
import tempfile
import traceback
import uuid


def init_job():
    job_id = os.environ.get("SLURM_JOB_ID", "???")
    logging.basicConfig(
        level=logging.WARNING,
        stream=sys.stdout,
        format=f"[SLURM{job_id}] [%(levelname)s] [%(name)s] %(message)s",
    )


def main_task_loop(client):
    while not client.max_tasks_reached():
        result = None
        exc = None
        exc_info = None
        job_failure = None

        try:
            data = client.receive()
            if data is None:
                break
        except Exception as e:
            exc = e
            job_failure = "failed receiving result from the client"
            exc_info = _serialize_exception(exc)

        if not job_failure:
            result, exc, exc_info = _execute(*data)
            if not isinstance(exc, Exception) and isinstance(exc, BaseException):
                job_failure = f"base exception '{type(exc)}' causes the client to exit"

        try:
            client.send(result, exc_info)
        except Exception:
            logging.warning("failed sending result to the client", exc_info=True)
            break
        finally:
            if job_failure:
                logging.error(job_failure)
                raise exc
    _cleanup_cached_modules()


class Client:
    """Client-side of a connection. The server-side is `ewoksjob.client.job_io.local._connection_base.Connection`."""

    _HEADER_NBYTES = 64  # allows for 2**64 bytes (~18 EB) data transfer
    _MAX_CHUNK_NBYTES = 65536  # data transfer in chunks of 64 KB
    _ACK_BYTE = b"\x06"

    def __init__(self, in_name, out_name) -> None:
        self._task_counter = 0
        self._in_name = in_name
        self._out_name = out_name
        self._max_tasks, log_level = self._receive()
        logging.getLogger().setLevel(log_level)
        logging.debug("Python version: %s", sys.version)
        logging.debug("working directory: %s", os.getcwd())
        logging.debug("Process ID: %s", os.getpid())

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def max_tasks_reached(self):
        return self._max_tasks is not None and self._task_counter >= self._max_tasks

    def receive(self):
        try:
            data = self._receive()
        finally:
            self._task_counter += 1
        return data

    def _receive(self):
        logging.debug("Waiting for data from %s ...", self._in_name)
        bheader = self._receive_nbytes(self._HEADER_NBYTES)
        nbytes = int.from_bytes(bheader, "big")
        logging.debug("Receiving %d bytes from %s ...", nbytes, self._in_name)
        bdata = self._receive_nbytes(nbytes)
        self._send_ack()
        logging.debug("Data from %s received", self._in_name)
        return pickle.loads(bdata)

    def send(self, data, exc_info):
        bdata = pickle.dumps((data, exc_info))
        nbytes = len(bdata)
        logging.debug(
            "Sending data %s (%s bytes) to %s ...",
            type(data),
            nbytes,
            self._out_name,
        )
        bheader = nbytes.to_bytes(self._HEADER_NBYTES, "big")
        self._send_bytes(bheader + bdata)
        self._wait_ack()
        logging.debug("Data send to %s", self._out_name)

    def _wait_ack(self) -> None:
        err_msg = "Slurm client did not acknowledge it received data"
        try:
            ack = self._receive_nbytes(1)
        except Exception as ex:
            raise ConnectionError(err_msg) from ex
        if ack != self._ACK_BYTE:
            raise ConnectionError(err_msg)

    def _send_ack(self) -> None:
        err_msg = "Could not acknowledge receiving data"
        try:
            self._send_bytes(self._ACK_BYTE)
        except Exception as ex:
            raise ConnectionError(err_msg) from ex

    @abc.abstractmethod
    def close(self):
        pass

    @abc.abstractmethod
    def _receive_nbytes(self, nbytes):
        pass

    @abc.abstractmethod
    def _send_bytes(self, bdata):
        pass


def _execute(task, args, kwargs):
    if isinstance(task, tuple):
        func_name, source_code = task
        logging.info("Executing task: %s", func_name)
        # logging.debug("Code:\n%s", source_code)
    else:
        func_name = task.__name__
        logging.info("Executing task: %s", func_name)

    logging.debug("Arguments: %s", args)
    logging.debug("Keyword arguments: %s", kwargs)

    if args is None:
        args = tuple()
    if kwargs is None:
        kwargs = dict()

    result = None
    exc = None
    exc_info = None

    try:
        if isinstance(task, tuple):
            module = _import_temp_module(source_code)
            try:
                func = getattr(module, func_name)
            except AttributeError:
                raise NameError(f"function '{func_name}' not found in client code")

            result = func(*args, **kwargs)
        else:
            result = task(*args, **kwargs)

        logging.info("Succeeded task: %s", func_name)
        exc = None
        exc_info = None

    except BaseException as e:
        logging.info("Failed task: %s", func_name)
        traceback.print_exc()
        result = None
        exc = e
        exc_info = _serialize_exception(exc)

    return result, exc, exc_info


_MODULES = {}


def _import_temp_module(source_code):
    """Create a temporary module with the source code."""
    key = hashlib.sha256(source_code.encode("utf-8")).hexdigest()

    if key in _MODULES:
        module, _ = _MODULES[key]
        return module

    temp_dir = tempfile.mkdtemp(
        prefix="pyslurmutils_", dir=os.environ.get("_TEST_TMPDIR")
    )

    module_name = f"pyslurmutils_client_code_{uuid.uuid4().hex}"
    module_path = os.path.join(temp_dir, f"{module_name}.py")
    with open(module_path, "w", encoding="utf-8") as f:
        f.write(source_code)

    logging.debug("Import temporary module: %s", module_path)
    sys.path.insert(0, temp_dir)
    module = importlib.import_module(module_name)

    _MODULES[key] = (module, temp_dir)

    return module


def _cleanup_cached_modules():
    for _, temp_dir in _MODULES.values():
        try:
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            logging.exception("Failed to remove temp module directory %s", temp_dir)
    _MODULES.clear()


def _serialize_exception(exc):
    chain = list()
    cause = None
    while exc:
        if exc.__cause__ is not None:
            next_cause = True
            chained_exc = exc.__cause__
        elif exc.__context__ is not None and not exc.__suppress_context__:
            next_cause = False
            chained_exc = exc.__context__
        else:
            next_cause = None
            chained_exc = None

        exc_class = type(exc)
        exc_class_string = f"{exc_class.__module__}.{exc_class.__name__}"
        exc_tb_string = "".join(
            traceback.format_exception(exc_class, exc, exc.__traceback__, chain=False)
        )

        chain.append((exc_class_string, str(exc), exc_tb_string, cause))
        exc = chained_exc
        cause = next_cause
    return chain
