"""
Terminal service for CMDOP SDK.

Provides terminal session management: create, attach, send input, resize, close.
Supports both sync and async patterns.

Streaming:
    >>> async with client.terminal.stream() as stream:
    ...     stream.on_output(lambda data: print(data.decode(), end=""))
    ...     await stream.send_input(b"ls -la\\n")
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from cmdop.models.terminal import (
    CreateSessionRequest,
    HistoryRequest,
    HistoryResponse,
    OutputChunk,
    ResizeRequest,
    SessionInfo,
    SessionListItem,
    SessionListResponse,
    SessionMode,
    SessionState,
    SignalType,
)
from cmdop.services.base import BaseService

if TYPE_CHECKING:
    from cmdop.streaming.terminal import TerminalStream
    from cmdop.transport.base import BaseTransport


class TerminalService(BaseService):
    """
    Synchronous terminal service.

    Provides operations for terminal session management.

    Example:
        >>> session = client.terminal.create()
        >>> client.terminal.send_input(session.session_id, b"ls\\n")
        >>> for chunk in client.terminal.stream(session.session_id):
        ...     print(chunk.text, end="")
    """

    def __init__(self, transport: BaseTransport) -> None:
        super().__init__(transport)
        self._stub: Any = None

    @property
    def _get_stub(self) -> Any:
        """Lazy-load gRPC stub."""
        if self._stub is None:
            from cmdop._generated.service_pb2_grpc import (
                TerminalStreamingServiceStub,
            )

            self._stub = TerminalStreamingServiceStub(self._channel)
        return self._stub

    def create(
        self,
        shell: str = "/bin/bash",
        cols: int = 80,
        rows: int = 24,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
        mode: SessionMode = SessionMode.EXCLUSIVE,
    ) -> SessionInfo:
        """
        Create a new terminal session.

        Args:
            shell: Shell executable path
            cols: Terminal width in columns
            rows: Terminal height in rows
            env: Additional environment variables
            working_dir: Initial working directory
            mode: Session access mode

        Returns:
            Created session info

        Raises:
            CMDOPError: On creation failure
        """
        from cmdop._generated.rpc_messages.session_pb2 import CreateSessionRequest as PbRequest
        from cmdop._generated.common_types_pb2 import SessionConfig, TerminalSize

        # Build config with nested size
        config = SessionConfig(
            shell=shell,
            working_directory=working_dir or "",
            size=TerminalSize(cols=cols, rows=rows),
        )
        if env:
            for k, v in env.items():
                config.env[k] = v

        request = PbRequest(config=config)

        response = self._call_sync(self._get_stub.CreateSession, request)

        return SessionInfo(
            session_id=response.session_id,
            state=SessionState.ACTIVE,
            mode=mode,
            shell=shell,
            cols=cols,
            rows=rows,
            working_dir=working_dir,
            created_at=datetime.now(timezone.utc),
        )

    def send_input(self, session_id: str, data: bytes | str) -> None:
        """
        Send input to terminal session.

        Args:
            session_id: Target session UUID
            data: Input bytes or string to send
        """
        from cmdop._generated.rpc_messages.terminal_pb2 import SendInputRequest

        if isinstance(data, str):
            data = data.encode("utf-8")

        request = SendInputRequest(
            session_id=session_id,
            data=data,
        )
        self._call_sync(self._get_stub.SendInput, request)

    def resize(self, session_id: str, cols: int, rows: int) -> None:
        """
        Resize terminal window.

        Args:
            session_id: Target session UUID
            cols: New width in columns
            rows: New height in rows
        """
        from cmdop._generated.rpc_messages.terminal_pb2 import SendResizeRequest

        request = SendResizeRequest(
            session_id=session_id,
            cols=cols,
            rows=rows,
        )
        self._call_sync(self._get_stub.SendResize, request)

    def send_signal(self, session_id: str, signal: SignalType) -> None:
        """
        Send signal to terminal session.

        Args:
            session_id: Target session UUID
            signal: Signal to send
        """
        from cmdop._generated.rpc_messages.terminal_pb2 import SendSignalRequest

        # Map signal enum to int
        signal_map = {
            SignalType.SIGHUP: 1,
            SignalType.SIGINT: 2,
            SignalType.SIGTERM: 15,
            SignalType.SIGKILL: 9,
            SignalType.SIGSTOP: 19,
            SignalType.SIGCONT: 18,
        }

        request = SendSignalRequest(
            session_id=session_id,
            signal=signal_map.get(signal, 15),
        )
        self._call_sync(self._get_stub.SendSignal, request)

    def close(self, session_id: str, force: bool = False) -> None:
        """
        Close terminal session.

        Args:
            session_id: Session UUID to close
            force: Force kill if graceful close fails
        """
        from cmdop._generated.rpc_messages.session_pb2 import CloseSessionRequest

        request = CloseSessionRequest(
            session_id=session_id,
        )
        self._call_sync(self._get_stub.CloseSession, request)

    def get_history(
        self,
        session_id: str,
        lines: int = 1000,
        offset: int = 0,
    ) -> HistoryResponse:
        """
        Get terminal output history.

        Args:
            session_id: Target session UUID
            lines: Number of lines to retrieve
            offset: Start offset for pagination

        Returns:
            History response with output data
        """
        from cmdop._generated.rpc_messages.history_pb2 import GetHistoryRequest

        request = GetHistoryRequest(
            session_id=session_id,
            limit=lines,
            offset=0,
        )
        response = self._call_sync(self._get_stub.GetHistory, request)

        return HistoryResponse(
            session_id=session_id,
            data=response.data if hasattr(response, "data") else b"".join(c.encode() for c in response.commands),
            total_lines=response.total if hasattr(response, "total") else lines,
            has_more=False,
        )


class AsyncTerminalService(BaseService):
    """
    Asynchronous terminal service.

    Provides async operations for terminal session management.

    Example:
        >>> session = await client.terminal.create()
        >>> await client.terminal.send_input(session.session_id, b"ls\\n")
        >>> async for chunk in client.terminal.stream(session.session_id):
        ...     print(chunk.text, end="")
    """

    def __init__(self, transport: BaseTransport) -> None:
        super().__init__(transport)
        self._stub: Any = None

    @property
    def _get_stub(self) -> Any:
        """Lazy-load async gRPC stub."""
        if self._stub is None:
            from cmdop._generated.service_pb2_grpc import (
                TerminalStreamingServiceStub,
            )

            self._stub = TerminalStreamingServiceStub(self._async_channel)
        return self._stub

    async def create(
        self,
        shell: str = "/bin/bash",
        cols: int = 80,
        rows: int = 24,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
        mode: SessionMode = SessionMode.EXCLUSIVE,
    ) -> SessionInfo:
        """Create a new terminal session."""
        from cmdop._generated.rpc_messages.session_pb2 import CreateSessionRequest as PbRequest
        from cmdop._generated.common_types_pb2 import SessionConfig, TerminalSize

        # Build config with nested size
        config = SessionConfig(
            shell=shell,
            working_directory=working_dir or "",
            size=TerminalSize(cols=cols, rows=rows),
        )
        if env:
            for k, v in env.items():
                config.env[k] = v

        request = PbRequest(config=config)

        response = await self._call_async(self._get_stub.CreateSession, request)

        return SessionInfo(
            session_id=response.session_id,
            state=SessionState.ACTIVE,
            mode=mode,
            shell=shell,
            cols=cols,
            rows=rows,
            working_dir=working_dir,
            created_at=datetime.now(timezone.utc),
        )

    async def send_input(self, session_id: str, data: bytes | str) -> None:
        """Send input to terminal session."""
        from cmdop._generated.rpc_messages.terminal_pb2 import SendInputRequest

        if isinstance(data, str):
            data = data.encode("utf-8")

        request = SendInputRequest(
            session_id=session_id,
            data=data,
        )
        await self._call_async(self._get_stub.SendInput, request)

    async def resize(self, session_id: str, cols: int, rows: int) -> None:
        """Resize terminal window."""
        from cmdop._generated.rpc_messages.terminal_pb2 import SendResizeRequest

        request = SendResizeRequest(
            session_id=session_id,
            cols=cols,
            rows=rows,
        )
        await self._call_async(self._get_stub.SendResize, request)

    async def send_signal(self, session_id: str, signal: SignalType) -> None:
        """Send signal to terminal session."""
        from cmdop._generated.rpc_messages.terminal_pb2 import SendSignalRequest

        signal_map = {
            SignalType.SIGHUP: 1,
            SignalType.SIGINT: 2,
            SignalType.SIGTERM: 15,
            SignalType.SIGKILL: 9,
            SignalType.SIGSTOP: 19,
            SignalType.SIGCONT: 18,
        }

        request = SendSignalRequest(
            session_id=session_id,
            signal=signal_map.get(signal, 15),
        )
        await self._call_async(self._get_stub.SendSignal, request)

    async def close(self, session_id: str, force: bool = False) -> None:
        """Close terminal session."""
        from cmdop._generated.rpc_messages.session_pb2 import CloseSessionRequest

        request = CloseSessionRequest(
            session_id=session_id,
        )
        await self._call_async(self._get_stub.CloseSession, request)

    async def get_history(
        self,
        session_id: str,
        lines: int = 1000,
        offset: int = 0,
    ) -> HistoryResponse:
        """Get terminal output history."""
        from cmdop._generated.rpc_messages.history_pb2 import GetHistoryRequest

        request = GetHistoryRequest(
            session_id=session_id,
            limit=lines,
            offset=offset,
        )
        response = await self._call_async(self._get_stub.GetHistory, request)

        return HistoryResponse(
            session_id=session_id,
            data=response.data if hasattr(response, "data") else b"".join(c.encode() for c in response.commands),
            total_lines=response.total if hasattr(response, "total") else lines,
            has_more=False,
        )

    def stream(self) -> TerminalStream:
        """
        Create a bidirectional terminal stream.

        Returns a TerminalStream that manages real-time terminal I/O
        via gRPC bidirectional streaming.

        **IMPORTANT: Remote mode only!**
        Streaming requires cloud relay connection (RemoteTransport).
        Local connections will raise RuntimeError on connect().
        For local mode, use send_input(), get_history() methods instead.

        Usage (remote mode):
            >>> async with AsyncCMDOPClient.remote(api_key="xxx") as client:
            ...     async with client.terminal.stream() as stream:
            ...         stream.on_output(lambda data: print(data.decode(), end=""))
            ...         await stream.send_input(b"ls\\n")

        Returns:
            TerminalStream instance (not yet connected).

        Raises:
            RuntimeError: On connect() if using local transport.

        Note:
            Call `await stream.connect()` or use as context manager
            to establish the connection.
        """
        from cmdop.streaming.terminal import TerminalStream

        return TerminalStream(self._transport)

    async def execute(
        self,
        command: str,
        timeout: float = 30.0,
        session_id: str | None = None,
    ) -> tuple[bytes, int]:
        """
        Execute a command and return output.

        Works in both local and remote modes:
        - Local: Creates session, sends command, gets history
        - Remote: Uses streaming if available

        Args:
            command: Command to execute.
            timeout: Maximum time to wait for completion.
            session_id: Optional existing session ID (reuse session).

        Returns:
            Tuple of (output_bytes, exit_code).
            Note: exit_code is -1 if command completion not detected.

        Example:
            >>> output, code = await client.terminal.execute("ls -la")
            >>> print(output.decode())
        """
        import asyncio

        # Create session if not provided
        created_session = False
        if session_id is None:
            session = await self.create()
            session_id = session.session_id
            created_session = True

        try:
            # Send command
            cmd = command if command.endswith("\n") else f"{command}\n"
            await self.send_input(session_id, cmd.encode())

            # Wait for command to complete
            await asyncio.sleep(min(timeout, 2.0))

            # Get output via history
            history = await self.get_history(session_id)
            output = history.data if history.data else b""

            return output, -1  # exit_code not available via unary RPCs

        finally:
            # Close session if we created it
            if created_session:
                try:
                    await self.close(session_id)
                except Exception:
                    pass

    async def list_sessions(
        self,
        hostname: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> SessionListResponse:
        """
        List terminal sessions in workspace (v2.14.0).

        Returns sessions visible to the authenticated API key's workspace.

        Args:
            hostname: Optional filter by machine hostname (partial match).
            status: Optional filter by status ("connected", "disconnected").
            limit: Maximum sessions to return (default: 20).

        Returns:
            SessionListResponse with list of sessions.

        Example:
            >>> response = await client.terminal.list_sessions(status="connected")
            >>> for s in response.sessions:
            ...     print(f"{s.machine_hostname}: {s.status}")
        """
        from cmdop._generated.rpc_messages.session_pb2 import ListSessionsRequest

        request = ListSessionsRequest(
            hostname_filter=hostname or "",
            status_filter=status or "",
            limit=limit,
        )

        response = await self._call_async(self._get_stub.ListSessions, request)

        if response.error:
            from cmdop.exceptions import CMDOPError
            raise CMDOPError(response.error)

        sessions = []
        for s in response.sessions:
            connected_at = None
            if s.connected_at and s.connected_at.seconds > 0:
                connected_at = datetime.fromtimestamp(
                    s.connected_at.seconds, tz=timezone.utc
                )

            sessions.append(SessionListItem(
                session_id=s.session_id,
                machine_hostname=s.machine_hostname,
                machine_name=s.machine_name,
                status=s.status,
                os=s.os,
                agent_version=s.agent_version,
                heartbeat_age_seconds=s.heartbeat_age_seconds,
                has_shell=s.has_shell,
                shell=s.shell,
                working_directory=s.working_directory,
                connected_at=connected_at,
            ))

        return SessionListResponse(
            sessions=sessions,
            total=response.total,
            workspace_name=response.workspace_name,
        )

    async def get_active_session(
        self,
        hostname: str | None = None,
    ) -> SessionListItem | None:
        """
        Get first active (connected) session (v2.14.0).

        Convenience method to find a connected session.

        Args:
            hostname: Optional filter by machine hostname.

        Returns:
            SessionListItem if found, None otherwise.

        Example:
            >>> session = await client.terminal.get_active_session()
            >>> if session:
            ...     client.agent.set_session_id(session.session_id)
        """
        response = await self.list_sessions(
            hostname=hostname,
            status="connected",
            limit=1,
        )
        return response.sessions[0] if response.sessions else None
