"""
Files service for CMDOP SDK.

Provides file system operations: list, read, write, delete, copy, move.
Supports both sync and async patterns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from cmdop.models.files import (
    FileEntry,
    FileInfo,
    FileType,
    ListDirectoryResponse,
)
from cmdop.services.base import BaseService

if TYPE_CHECKING:
    from cmdop.transport.base import BaseTransport


def _parse_file_type(pb_type: int) -> FileType:
    """Convert protobuf file type to enum."""
    # Map based on proto enum values
    type_map = {
        0: FileType.UNKNOWN,
        1: FileType.FILE,
        2: FileType.DIRECTORY,
        3: FileType.SYMLINK,
    }
    return type_map.get(pb_type, FileType.UNKNOWN)


def _parse_timestamp(ts: Any) -> datetime | None:
    """Convert protobuf timestamp to datetime."""
    if ts is None:
        return None
    try:
        if hasattr(ts, "seconds"):
            return datetime.fromtimestamp(ts.seconds, tz=timezone.utc)
        return None
    except (ValueError, OSError):
        return None


class FilesService(BaseService):
    """
    Synchronous files service.

    Provides file system operations.

    Example:
        >>> # Local IPC - session_id is optional
        >>> entries = client.files.list("/home/user")
        >>>
        >>> # Remote - set session_id first
        >>> session = client.terminal.get_active_session()
        >>> client.files.set_session_id(session.session_id)
        >>> entries = client.files.list("/home/user")
        >>>
        >>> # Or pass session_id directly
        >>> entries = client.files.list("/home/user", session_id=session.session_id)
    """

    def __init__(self, transport: BaseTransport) -> None:
        super().__init__(transport)
        self._stub: Any = None
        self._session_id: str | None = None

    def set_session_id(self, session_id: str) -> None:
        """
        Set session ID for file operations.

        Required for remote connections. For local IPC, session_id is optional.

        Args:
            session_id: Session ID from terminal.get_active_session() or terminal.create()

        Example:
            >>> session = client.terminal.get_active_session()
            >>> client.files.set_session_id(session.session_id)
            >>> files = client.files.list("/tmp")
        """
        self._session_id = session_id

    def _get_session_id(self, session_id: str | None = None) -> str:
        """Get session ID from parameter or stored value."""
        sid = session_id or self._session_id
        if not sid:
            # For local IPC, use empty string (server will handle)
            # For remote, this will likely fail but let server return proper error
            return ""
        return sid

    @property
    def _get_stub(self) -> Any:
        """Lazy-load gRPC stub."""
        if self._stub is None:
            from cmdop._generated.service_pb2_grpc import (
                TerminalStreamingServiceStub,
            )

            self._stub = TerminalStreamingServiceStub(self._channel)
        return self._stub

    def list(
        self,
        path: str,
        include_hidden: bool = False,
        page_size: int = 100,
        page_token: str | None = None,
        session_id: str | None = None,
    ) -> ListDirectoryResponse:
        """
        List directory contents.

        Args:
            path: Directory path to list
            include_hidden: Include hidden files
            page_size: Number of entries per page
            page_token: Pagination token
            session_id: Session ID (uses stored value if not provided)

        Returns:
            Directory listing response
        """
        from cmdop._generated.file_rpc.directory_pb2 import (
            FileListDirectoryRpcRequest,
        )

        request = FileListDirectoryRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            page_size=page_size,
            include_hidden=include_hidden,
        )
        if page_token:
            request.page_token = page_token

        response = self._call_sync(self._get_stub.FileListDirectory, request)

        entries = []
        for entry in response.result.entries:
            entries.append(
                FileEntry(
                    name=entry.name,
                    path=entry.path,
                    type=_parse_file_type(entry.type),
                    size=entry.size,
                    modified_at=_parse_timestamp(entry.modified_at),
                    is_hidden=entry.name.startswith("."),
                )
            )

        return ListDirectoryResponse(
            path=response.result.current_path,
            entries=entries,
            next_page_token=response.result.next_page_token or None,
            total_count=response.result.total_count,
        )

    def read(
        self,
        path: str,
        offset: int = 0,
        limit: int = 0,
        session_id: str | None = None,
    ) -> bytes:
        """
        Read file contents.

        Args:
            path: File path to read
            offset: Byte offset to start reading
            limit: Maximum bytes to read (0 = entire file)
            session_id: Session ID (uses stored value if not provided)

        Returns:
            File contents as bytes
        """
        from cmdop._generated.file_rpc.file_crud_pb2 import FileReadRpcRequest

        request = FileReadRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
        )

        response = self._call_sync(self._get_stub.FileRead, request)
        return response.result.content

    def write(
        self,
        path: str,
        content: bytes | str,
        create_parents: bool = False,
        overwrite: bool = True,
        session_id: str | None = None,
    ) -> None:
        """
        Write file contents.

        Args:
            path: File path to write
            content: Content to write (bytes or string)
            create_parents: Create parent directories
            overwrite: Overwrite existing file
            session_id: Session ID (uses stored value if not provided)
        """
        from cmdop._generated.file_rpc.file_crud_pb2 import FileWriteRpcRequest

        if isinstance(content, str):
            content = content.encode("utf-8")

        request = FileWriteRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            content=content,
            create_parents=create_parents,
        )

        self._call_sync(self._get_stub.FileWrite, request)

    def delete(
        self,
        path: str,
        recursive: bool = False,
        session_id: str | None = None,
    ) -> None:
        """
        Delete file or directory.

        Args:
            path: Path to delete
            recursive: Delete directory recursively
            session_id: Session ID (uses stored value if not provided)
        """
        from cmdop._generated.file_rpc.file_crud_pb2 import FileDeleteRpcRequest

        request = FileDeleteRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            recursive=recursive,
        )

        self._call_sync(self._get_stub.FileDelete, request)

    def copy(
        self,
        source: str,
        destination: str,
        session_id: str | None = None,
    ) -> None:
        """
        Copy file or directory.

        Args:
            source: Source path
            destination: Destination path
            session_id: Session ID (uses stored value if not provided)
        """
        from cmdop._generated.file_rpc.file_crud_pb2 import FileCopyRpcRequest

        request = FileCopyRpcRequest(
            session_id=self._get_session_id(session_id),
            source_path=source,
            destination_path=destination,
        )

        self._call_sync(self._get_stub.FileCopy, request)

    def move(
        self,
        source: str,
        destination: str,
        session_id: str | None = None,
    ) -> None:
        """
        Move/rename file or directory.

        Args:
            source: Source path
            destination: Destination path
            session_id: Session ID (uses stored value if not provided)
        """
        from cmdop._generated.file_rpc.file_crud_pb2 import FileMoveRpcRequest

        request = FileMoveRpcRequest(
            session_id=self._get_session_id(session_id),
            source_path=source,
            destination_path=destination,
        )

        self._call_sync(self._get_stub.FileMove, request)

    def info(self, path: str, session_id: str | None = None) -> FileInfo:
        """
        Get file information.

        Args:
            path: File path
            session_id: Session ID (uses stored value if not provided)

        Returns:
            Detailed file information
        """
        from cmdop._generated.file_rpc.file_crud_pb2 import FileGetInfoRpcRequest

        request = FileGetInfoRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
        )
        response = self._call_sync(self._get_stub.FileGetInfo, request)

        entry = response.result.entry
        return FileInfo(
            path=entry.path,
            type=_parse_file_type(entry.type),
            size=entry.size,
            modified_at=_parse_timestamp(entry.modified_at),
            permissions=entry.permissions if hasattr(entry, "permissions") else None,
        )

    def mkdir(
        self,
        path: str,
        create_parents: bool = True,
        session_id: str | None = None,
    ) -> None:
        """
        Create directory.

        Args:
            path: Directory path to create
            create_parents: Create parent directories
            session_id: Session ID (uses stored value if not provided)
        """
        from cmdop._generated.file_rpc.file_crud_pb2 import (
            FileCreateDirectoryRpcRequest,
        )

        request = FileCreateDirectoryRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            create_parents=create_parents,
        )

        self._call_sync(self._get_stub.FileCreateDirectory, request)


class AsyncFilesService(BaseService):
    """
    Asynchronous files service.

    Provides async file system operations.

    Example:
        >>> # Remote - set session_id first
        >>> session = await client.terminal.get_active_session()
        >>> client.files.set_session_id(session.session_id)
        >>> entries = await client.files.list("/home/user")
    """

    def __init__(self, transport: BaseTransport) -> None:
        super().__init__(transport)
        self._stub: Any = None
        self._session_id: str | None = None

    def set_session_id(self, session_id: str) -> None:
        """
        Set session ID for file operations.

        Required for remote connections. For local IPC, session_id is optional.

        Args:
            session_id: Session ID from terminal.get_active_session() or terminal.create()
        """
        self._session_id = session_id

    def _get_session_id(self, session_id: str | None = None) -> str:
        """Get session ID from parameter or stored value."""
        sid = session_id or self._session_id
        if not sid:
            return ""
        return sid

    @property
    def _get_stub(self) -> Any:
        """Lazy-load async gRPC stub."""
        if self._stub is None:
            from cmdop._generated.service_pb2_grpc import (
                TerminalStreamingServiceStub,
            )

            self._stub = TerminalStreamingServiceStub(self._async_channel)
        return self._stub

    async def list(
        self,
        path: str,
        include_hidden: bool = False,
        page_size: int = 100,
        page_token: str | None = None,
        session_id: str | None = None,
    ) -> ListDirectoryResponse:
        """List directory contents."""
        from cmdop._generated.file_rpc.directory_pb2 import (
            FileListDirectoryRpcRequest,
        )

        request = FileListDirectoryRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            page_size=page_size,
            include_hidden=include_hidden,
        )
        if page_token:
            request.page_token = page_token

        response = await self._call_async(self._get_stub.FileListDirectory, request)

        entries = []
        for entry in response.result.entries:
            entries.append(
                FileEntry(
                    name=entry.name,
                    path=entry.path,
                    type=_parse_file_type(entry.type),
                    size=entry.size,
                    modified_at=_parse_timestamp(entry.modified_at),
                    is_hidden=entry.name.startswith("."),
                )
            )

        return ListDirectoryResponse(
            path=response.result.current_path,
            entries=entries,
            next_page_token=response.result.next_page_token or None,
            total_count=response.result.total_count,
        )

    async def read(
        self,
        path: str,
        offset: int = 0,
        limit: int = 0,
        session_id: str | None = None,
    ) -> bytes:
        """Read file contents."""
        from cmdop._generated.file_rpc.file_crud_pb2 import FileReadRpcRequest

        request = FileReadRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
        )
        response = await self._call_async(self._get_stub.FileRead, request)
        return response.result.content

    async def write(
        self,
        path: str,
        content: bytes | str,
        create_parents: bool = False,
        overwrite: bool = True,
        session_id: str | None = None,
    ) -> None:
        """Write file contents."""
        from cmdop._generated.file_rpc.file_crud_pb2 import FileWriteRpcRequest

        if isinstance(content, str):
            content = content.encode("utf-8")

        request = FileWriteRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            content=content,
            create_parents=create_parents,
        )
        await self._call_async(self._get_stub.FileWrite, request)

    async def delete(
        self,
        path: str,
        recursive: bool = False,
        session_id: str | None = None,
    ) -> None:
        """Delete file or directory."""
        from cmdop._generated.file_rpc.file_crud_pb2 import FileDeleteRpcRequest

        request = FileDeleteRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            recursive=recursive,
        )
        await self._call_async(self._get_stub.FileDelete, request)

    async def copy(
        self,
        source: str,
        destination: str,
        session_id: str | None = None,
    ) -> None:
        """Copy file or directory."""
        from cmdop._generated.file_rpc.file_crud_pb2 import FileCopyRpcRequest

        request = FileCopyRpcRequest(
            session_id=self._get_session_id(session_id),
            source_path=source,
            destination_path=destination,
        )
        await self._call_async(self._get_stub.FileCopy, request)

    async def move(
        self,
        source: str,
        destination: str,
        session_id: str | None = None,
    ) -> None:
        """Move/rename file or directory."""
        from cmdop._generated.file_rpc.file_crud_pb2 import FileMoveRpcRequest

        request = FileMoveRpcRequest(
            session_id=self._get_session_id(session_id),
            source_path=source,
            destination_path=destination,
        )
        await self._call_async(self._get_stub.FileMove, request)

    async def info(self, path: str, session_id: str | None = None) -> FileInfo:
        """Get file information."""
        from cmdop._generated.file_rpc.file_crud_pb2 import FileGetInfoRpcRequest

        request = FileGetInfoRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
        )
        response = await self._call_async(self._get_stub.FileGetInfo, request)

        entry = response.result.entry
        return FileInfo(
            path=entry.path,
            type=_parse_file_type(entry.type),
            size=entry.size,
            modified_at=_parse_timestamp(entry.modified_at),
        )

    async def mkdir(
        self,
        path: str,
        create_parents: bool = True,
        session_id: str | None = None,
    ) -> None:
        """Create directory."""
        from cmdop._generated.file_rpc.file_crud_pb2 import (
            FileCreateDirectoryRpcRequest,
        )

        request = FileCreateDirectoryRpcRequest(
            session_id=self._get_session_id(session_id),
            path=path,
            create_parents=create_parents,
        )
        await self._call_async(self._get_stub.FileCreateDirectory, request)
