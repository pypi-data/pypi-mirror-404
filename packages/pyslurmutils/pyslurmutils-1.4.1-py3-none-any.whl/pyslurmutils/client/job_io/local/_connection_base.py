import abc
import logging
import pickle
import threading
from contextlib import contextmanager
from typing import Any
from typing import Generator
from typing import Optional
from typing import Tuple

logger = logging.getLogger(__name__)


class Connection(abc.ABC):
    """Server-side of a connection. The client-side is `ewoksjob.client.job_io.remote._base.Client`.

    Wire-level protocol: every message consists of a fixed-size length header followed
    by the payload, and every successful payload transfer is acknowledged
    with a single "ACK" byte.

    Send data:

    .. code-block::

        → | <nbytes-data>[#bytes=_HEADER_NBYTES] | <data>[#bytes=nbytes-data] |
        ← | _ACK_BYTE[1] |

    Receive data:

    .. code-block::

        ← | <nbytes-data>[#bytes=_HEADER_NBYTES]  | <data>[#bytes=nbytes-data] |
        → | _ACK_BYTE[1] |
    """

    _HEADER_NBYTES = 64  # allows for 2**64 bytes (~18 EB) data transfer
    _MAX_CHUNK_NBYTES = 65536  # data transfer in chunks of 64 KB
    _ACK_BYTE = b"\x06"  # ASCII "ACK"

    def __init__(self, raise_on_status_error: Optional[callable] = None) -> None:
        """
        :param raise_on_status_error: function that raises an exception when there is a status error (remote or local exit).
        """
        self._cancel_event = threading.Event()
        self._yield_period = 1
        self._raise_on_status_error = raise_on_status_error

    @property
    @abc.abstractmethod
    def input_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def output_name(self) -> str:
        pass

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def cancel(self) -> None:
        self._cancel_event.set()

    def cancelled(self) -> bool:
        return self._cancel_event.is_set()

    @abc.abstractmethod
    def close(self):
        pass

    @abc.abstractmethod
    def _wait_client(self) -> None:
        """Wait for the client to be online. The client is remote, we are the server.

        :raises RemoteExit: raises exception when client is not alive
        """
        pass

    @contextmanager
    def _wait_client_context(self) -> Generator[None, None, None]:
        logger.debug("waiting for remote job to connect to %s ...", self.output_name)
        try:
            yield
        except Exception:
            logger.debug(
                "waiting for remote job to connect to %s failed", self.output_name
            )
            raise
        if self.cancelled():
            logger.debug(
                "waiting for remote job to connect to %s cancelled", self.output_name
            )
        else:
            logger.debug("remote job connected to %s", self.output_name)

    def send_data(self, data: Any) -> None:
        """Send data to the client."""
        bdata = self._serialize_data(data)
        nbytes = len(bdata)
        logger.debug(
            "send data %s (%d bytes) to client of %s ...",
            type(data),
            nbytes,
            self.output_name,
        )
        bheader = self._serialize_header(bdata)
        try:
            self._send_bytes_with_check(bheader + bdata)
            if data is not None:
                self._wait_ack()
        except (BrokenPipeError, ConnectionResetError):
            if data is None:
                logger.debug("client of %s already exited", self.output_name)
                return
            raise
        logger.debug("data send to client of %s", self.output_name)

    def receive_data(self) -> Tuple[Any, Optional[BaseException]]:
        """Receive data from the client.

        :raises RemoteExit: raises exception when client is not alive
        """
        logger.debug("waiting for client data on %s ...", self.input_name)
        bheader = self._receive_nbytes_with_check(self._HEADER_NBYTES)
        nbytes = self._deserialize_header(bheader)
        if nbytes == 0:
            logger.warning(
                "corrupt header %s from client on %s ...", bheader, self.input_name
            )
        bdata = self._receive_nbytes_with_check(nbytes)
        self._send_ack()
        logger.debug("client data received from %s", self.input_name)
        return self._deserialize_data(bdata)

    def _serialize_header(self, bdata: bytes) -> bytes:
        return len(bdata).to_bytes(self._HEADER_NBYTES, "big")

    def _deserialize_header(self, bheader: bytes) -> int:
        return int.from_bytes(bheader, "big")

    def _serialize_data(self, data: Any) -> bytes:
        return pickle.dumps(data)

    def _deserialize_data(self, data: bytes) -> Any:
        return pickle.loads(data)

    def _receive_nbytes_with_check(self, nbytes: int) -> bytes:
        """
        :raises RemoteExit: raises exception when not alive
        :raises ValueError: cancelled or did not receive the requested number of bytes
        """
        bdata = self._receive_nbytes(nbytes)
        if len(bdata) != nbytes:
            err_msg = f"{len(bdata)} bytes received from {self.input_name} instead of {nbytes} bytes"
            if self.cancelled():
                raise ValueError(f"{err_msg} (cancelled)")
            else:
                raise ValueError(err_msg)
        return bdata

    @abc.abstractmethod
    def _receive_nbytes(self, nbytes: int) -> bytes:
        """Receive exactly nbytes from the client.

        :raises RemoteExit: raises exception when client is not alive
        """
        pass

    def _send_bytes_with_check(self, data: bytes) -> None:
        """
        :raises RuntimeError: cancelled
        """
        if self.cancelled():
            raise RuntimeError(f"send to %{self} is cancelled")
        self._send_bytes(data)

    @abc.abstractmethod
    def _send_bytes(self, data: bytes) -> None:
        """Send bytes to the client."""
        pass

    def _wait_ack(self) -> None:
        err_msg = "Slurm job did not acknowledge it received data"
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


class Buffer:
    def __init__(self, nbytes: int, max_chunk_size: int) -> None:
        self._data = bytearray()
        self._nbytes = nbytes
        self._remaining = nbytes
        self._has_data = False
        self._MAX_CHUNK_NBYTES = max_chunk_size

    @property
    def read_size(self) -> int:
        return min(self._remaining, self._MAX_CHUNK_NBYTES)

    def extend(self, bdata: bytes) -> None:
        if bdata:
            self._data.extend(bdata)
            self._remaining -= len(bdata)
            self._has_data = True

    @property
    def complete(self) -> bool:
        return self._remaining <= 0

    @property
    def has_data(self) -> bool:
        return self._has_data

    @property
    def progress(self) -> str:
        return f"{len(self._data)}/{self._nbytes} bytes"

    def to_bytes(self) -> bytes:
        return bytes(self._data)
