"""Custom exceptions for audio loading and processing."""


class AudioError(Exception):
    """Base exception for audio-related errors."""

    pass


class AudioFileNotFoundError(AudioError, FileNotFoundError):
    """Raised when an audio file cannot be found.

    This exception is raised when trying to load an audio file that doesn't
    exist at the specified path.

    Args:
        path: Path to the missing audio file
        message: Optional custom error message

    Example:
        >>> try:
        ...     load_audio("missing.wav")
        ... except AudioFileNotFoundError as e:
        ...     print(f"File not found: {e}")
    """

    def __init__(self, path: str, message: str | None = None) -> None:
        """Initialize AudioFileNotFoundError."""
        self.path = path
        if message is None:
            message = f"Audio file not found: {path}"
        super().__init__(message)


class UnsupportedFormatError(AudioError):
    """Raised when an audio file format is not supported.

    mixref supports WAV, FLAC, and MP3 (with FFmpeg). This exception is
    raised when trying to load a file with an unsupported extension.

    Args:
        path: Path to the unsupported file
        format_: File format/extension that was detected
        message: Optional custom error message

    Example:
        >>> try:
        ...     load_audio("track.ogg")
        ... except UnsupportedFormatError as e:
        ...     print(f"Unsupported format: {e.format_}")
    """

    def __init__(
        self,
        path: str,
        format_: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize UnsupportedFormatError."""
        self.path = path
        self.format_ = format_
        if message is None:
            if format_:
                message = (
                    f"Unsupported audio format '{format_}' for file: {path}\n"
                    f"Supported formats: WAV, FLAC, MP3 (requires FFmpeg)"
                )
            else:
                message = (
                    f"Unsupported audio format for file: {path}\n"
                    f"Supported formats: WAV, FLAC, MP3 (requires FFmpeg)"
                )
        super().__init__(message)


class CorruptFileError(AudioError):
    """Raised when an audio file is corrupt or cannot be decoded.

    This exception is raised when a file exists but cannot be read properly,
    indicating corruption or invalid audio data.

    Args:
        path: Path to the corrupt file
        original_error: Original exception that was raised during reading
        message: Optional custom error message

    Example:
        >>> try:
        ...     load_audio("corrupt.wav")
        ... except CorruptFileError as e:
        ...     print(f"Cannot read file: {e}")
        ...     print(f"Original error: {e.original_error}")
    """

    def __init__(
        self,
        path: str,
        original_error: Exception | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize CorruptFileError."""
        self.path = path
        self.original_error = original_error
        if message is None:
            message = f"Failed to read audio file (corrupt or invalid format): {path}"
            if original_error:
                message += f"\nOriginal error: {original_error}"
        super().__init__(message)


class InvalidAudioDataError(AudioError):
    """Raised when audio data is invalid or has unexpected properties.

    This can occur when audio has zero duration, invalid sample rate,
    or other problematic characteristics.

    Args:
        message: Description of what's invalid about the audio data

    Example:
        >>> if audio.size == 0:
        ...     raise InvalidAudioDataError("Audio file contains no data")
    """

    pass
