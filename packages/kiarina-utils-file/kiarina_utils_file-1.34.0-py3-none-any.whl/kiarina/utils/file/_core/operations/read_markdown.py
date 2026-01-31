import os
from typing import Awaitable, Literal, overload

from ..types.markdown_content import MarkdownContent
from ..utils.read_text import read_text


@overload
def read_markdown(
    mode: Literal["sync"],
    file_path: str | os.PathLike[str],
    *,
    default: MarkdownContent | None = None,
) -> MarkdownContent | None: ...


@overload
def read_markdown(
    mode: Literal["async"],
    file_path: str | os.PathLike[str],
    *,
    default: MarkdownContent | None = None,
) -> Awaitable[MarkdownContent | None]: ...


def read_markdown(
    mode: Literal["sync", "async"],
    file_path: str | os.PathLike[str],
    *,
    default: MarkdownContent | None = None,
) -> MarkdownContent | None | Awaitable[MarkdownContent | None]:
    """
    Read Markdown file with optional YAML front matter.

    This function reads a Markdown file and extracts YAML front matter if present.
    The front matter must be at the beginning of the file, enclosed by `---` markers.

    Front matter format:
        ---
        key1: value1
        key2: value2
        ---
        Markdown content starts here...

    Args:
        mode (Literal["sync", "async"]): Execution mode, either "sync" or "async"
        file_path (str | os.PathLike[str]): Path to the Markdown file to read
        default (MarkdownContent | None): Default value to return if file doesn't exist.
            Default is None.

    Returns:
        MarkdownContent | None | Awaitable[MarkdownContent | None]:
            - MarkdownContent with content and metadata if file exists
            - default if file doesn't exist
            - Awaitable if mode is "async"

    Examples:
        >>> # Sync usage
        >>> result = read_markdown("sync", "document.md")
        >>> if result:
        ...     print(result.content)
        ...     print(result.metadata.get("title"))

        >>> # With default value
        >>> result = read_markdown(
        ...     "sync",
        ...     "missing.md",
        ...     default=MarkdownContent(content="", metadata={})
        ... )
        >>> print(result.content)  # Always str (empty if file missing)

        >>> # Async usage
        >>> result = await read_markdown("async", "document.md")
        >>> if result:
        ...     print(result.content)

    Note:
        - If the file has no front matter, metadata will be an empty dict
        - If the front matter is invalid YAML, it will be treated as regular content
        - The content does not include the front matter block
    """

    def _parse_markdown(raw_text: str | None) -> MarkdownContent | None:
        if raw_text is None:
            return default

        return MarkdownContent.from_text(raw_text)

    def _sync() -> MarkdownContent | None:
        raw_text = read_text("sync", file_path)
        return _parse_markdown(raw_text)

    async def _async() -> MarkdownContent | None:
        raw_text = await read_text("async", file_path)
        return _parse_markdown(raw_text)

    if mode == "sync":
        return _sync()
    else:
        return _async()
