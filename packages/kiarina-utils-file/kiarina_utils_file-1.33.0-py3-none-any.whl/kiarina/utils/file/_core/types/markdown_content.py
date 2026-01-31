import re
from typing import Any, NamedTuple

import yaml


class MarkdownContent(NamedTuple):
    """
    Markdown content with optional YAML front matter metadata.

    This class represents the result of parsing a Markdown file that may contain
    YAML front matter. The front matter is extracted and parsed into metadata,
    while the remaining content is stored separately.

    Attributes:
        content (str): Markdown content without the YAML front matter block.
            If the file has no front matter, this contains the entire file content.
        metadata (dict[str, Any]): Parsed YAML front matter as a dictionary.
            If the file has no front matter or the front matter is invalid,
            this is an empty dictionary.

    Examples:
        >>> # File with front matter:
        >>> # ---
        >>> # title: Example
        >>> # author: John Doe
        >>> # ---
        >>> # # Content
        >>> result = MarkdownContent(
        ...     content="# Content\\n",
        ...     metadata={"title": "Example", "author": "John Doe"}
        ... )
        >>> print(result.content)
        # Content
        >>> print(result.metadata["title"])
        Example

        >>> # File without front matter:
        >>> result = MarkdownContent(
        ...     content="# Just Content\\n",
        ...     metadata={}
        ... )
        >>> print(result.content)
        # Just Content
        >>> print(result.metadata)
        {}

        >>> # Parse from text:
        >>> text = '''---
        ... title: Example
        ... ---
        ... # Content
        ... '''
        >>> result = MarkdownContent.from_text(text)
        >>> print(result.metadata["title"])
        Example
    """

    content: str
    """Markdown content (without front matter)"""

    metadata: dict[str, Any]
    """YAML front matter metadata (empty dict if no front matter)"""

    @classmethod
    def from_text(cls, text: str) -> "MarkdownContent":
        """
        Parse Markdown text with optional YAML front matter.

        This method extracts YAML front matter if present and returns a MarkdownContent
        instance. The front matter must be at the beginning of the text, enclosed by
        `---` markers.

        Front matter format:
            ---
            key1: value1
            key2: value2
            ---
            Markdown content starts here...

        Args:
            text (str): Markdown text to parse

        Returns:
            MarkdownContent: Parsed content and metadata

        Examples:
            >>> # With front matter
            >>> text = '''---
            ... title: Test Document
            ... author: John Doe
            ... ---
            ... # Hello World
            ... '''
            >>> result = MarkdownContent.from_text(text)
            >>> print(result.metadata["title"])
            Test Document
            >>> print(result.content)
            # Hello World

            >>> # Without front matter
            >>> text = "# Just Content"
            >>> result = MarkdownContent.from_text(text)
            >>> print(result.metadata)
            {}
            >>> print(result.content)
            # Just Content

        Note:
            - If the text has no front matter, metadata will be an empty dict
            - If the front matter is invalid YAML, it will be treated as regular content
            - The content does not include the front matter block
        """
        # Pattern to match YAML front matter at the start of the text
        # Must start with ---, followed by content, then end with ---
        front_matter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

        match = front_matter_pattern.match(text)

        if match:
            # Extract front matter and content
            front_matter_text = match.group(1)
            content = text[match.end() :]

            try:
                metadata = yaml.safe_load(front_matter_text)

                # Ensure metadata is a dict (YAML can return other types)
                if not isinstance(metadata, dict):
                    # Invalid front matter structure, treat as regular content
                    return cls(content=text, metadata={})

                # Ensure all keys are strings
                if not all(isinstance(key, str) for key in metadata.keys()):
                    # Non-string keys, treat as regular content
                    return cls(content=text, metadata={})

            except yaml.YAMLError:
                # Invalid YAML, treat as regular content
                return cls(content=text, metadata={})
        else:
            # No front matter
            content = text
            metadata = {}

        return cls(content=content, metadata=metadata)
