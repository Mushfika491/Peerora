"""Pydantic request/response schemas, one module per feature.

`from peerora.schemas import TutorIn, TutorOut` keeps working as before.
"""

from peerora.schemas.tutor import TutorIn, TutorOut, TutorPublicOut

__all__ = ["TutorIn", "TutorOut", "TutorPublicOut"]
