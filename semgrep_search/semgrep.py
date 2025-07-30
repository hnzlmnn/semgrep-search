import asyncio
import functools
import subprocess
import sys
from asyncio import StreamReader

from semgrep_search.runconfig import RunConfig
from semgrep_search.utils import logger


class MyProtocol(asyncio.subprocess.SubprocessStreamProtocol):
    def __init__(self, stdout: StreamReader, stderr: StreamReader, limit, loop):
        super().__init__(limit=limit, loop=loop)
        self._stdout = stdout
        self._stderr = stderr

    def pipe_data_received(self, fd, data):
        """Called when the child process writes data into its stdout
        or stderr pipe.
        """
        super().pipe_data_received(fd, data)
        if fd == 1:
            self._stdout.feed_data(data)
        elif fd == 2:
            self._stderr.feed_data(data)

    def pipe_connection_lost(self, fd, exc):
        """Called when one of the pipes communicating with the child
        process is closed.
        """
        super().pipe_connection_lost(fd, exc)
        if fd == 1:
            if exc:
                self._stdout.set_exception(exc)
            else:
                self._stdout.feed_eof()
        elif fd == 2:
            if exc:
                self._stderr.set_exception(exc)
            else:
                self._stderr.feed_eof()


async def run_semgrep(run: RunConfig):
    args = [
        # 'echo',
        run.binary,
        '--disable-version-check', '--metrics=off', '--disable-nosem',
        '--config', str(run.rules_file.absolute()),
        *run.output_params(),
    ]

    loop = asyncio.get_event_loop()
    stdout = StreamReader(loop=loop)
    stderr = StreamReader(loop=loop)
    protocol_factory = functools.partial(MyProtocol, stdout, stderr, limit=2 ** 16, loop=loop)

    async def log_stream(src: StreamReader, dst) -> None:
        async for line in src:
            dst.write(line.decode())

    transport, protocol = await loop.subprocess_exec(
        protocol_factory,
        *args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=run.target,
    )

    proc = asyncio.subprocess.Process(transport, protocol, loop)

    (out, err), _, _ = await asyncio.gather(
        proc.communicate(), log_stream(stdout, sys.stdout), log_stream(stderr, sys.stderr)
    )
    if proc.returncode > 0:
        logger.error(f'semgrep returned non-zero exit code: {proc.returncode}')
    return proc.returncode
