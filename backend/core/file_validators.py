from typing import Optional, Tuple

import magic


class FileValidator:
    ALLOWED_EXTENSIONS = [".pdf"]
    ALLOWED_MIME_TYPES = ["application/pdf"]
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @staticmethod
    def validate_file(file_bytes: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file before parsing.
        Returns: (is_valid, error_message)
        """
        # Check 1: File size
        if len(file_bytes) > FileValidator.MAX_FILE_SIZE:
            return False, "File size exceeds 5MB limit"

        # Check 2: File extension
        if not any(
            filename.lower().endswith(ext) for ext in FileValidator.ALLOWED_EXTENSIONS
        ):
            return (
                False,
                f"File type not supported. Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}",
            )

        # Check 3: MIME type (actual content, not just extension)
        mime = magic.from_buffer(file_bytes, mime=True)
        if mime not in FileValidator.ALLOWED_MIME_TYPES:
            return False, f"Invalid file format. Detected: {mime}"

        # Check 4: Basic corruption check
        if len(file_bytes) < 100:  # Too small to be valid
            return False, "File appears to be corrupted or empty"

        return True, None
