from __future__ import annotations

"""
Progress dataclasses.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UploadProgress:
    local_path: str
    remote_path: str
    total_bytes: int
    uploaded_bytes: int
    part_index: int
    total_parts: int
