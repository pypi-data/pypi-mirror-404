import logging
import os
import time

from ._base import Client
from ._base import init_job
from ._base import main_task_loop


def main():
    init_job()
    with FileClient() as client:
        main_task_loop(client)


class FileClient(Client):
    def __init__(self) -> None:
        input_filename = os.environ["_PYSLURMUTILS_INFILE"]
        output_filename = os.environ["_PYSLURMUTILS_OUTFILE"]

        logging.debug("Connecting to '%s' ...", input_filename)
        input_dirname = os.path.dirname(input_filename)
        while True:
            try:
                _ = os.listdir(input_dirname)  # force NFS cache
                self._input_file = open(input_filename, "rb+")
                self._input_filename = input_filename
                break
            except FileNotFoundError:
                time.sleep(0.5)
        logging.debug("Connected to '%s'", input_filename)

        self._output_file = open(output_filename, "wb+")
        self._output_filename = output_filename

        super().__init__(input_filename, output_filename)

    def close(self) -> None:
        logging.debug("Closing connection ...")
        if self._input_file is not None:
            self._input_file.close()
            self._input_file = None
        if self._output_file is not None:
            self._output_file.close()
            self._output_file = None
        logging.debug("Connection closed")

    def _send_bytes(self, bdata: bytes) -> None:
        self._output_file.write(bdata)
        self._output_file.flush()

    def _receive_nbytes(self, nbytes: int) -> bytes:
        data = bytearray()
        remaining = nbytes
        block = min(nbytes, self._MAX_CHUNK_NBYTES)

        while remaining > 0:
            filesize = os.path.getsize(self._input_filename)
            pos = self._input_file.tell()
            available = filesize - pos

            if available <= 0:
                time.sleep(0.1)
            else:
                chunk = self._input_file.read(min(block, remaining))
                data.extend(chunk)
                remaining -= len(chunk)

        return bytes(data)
