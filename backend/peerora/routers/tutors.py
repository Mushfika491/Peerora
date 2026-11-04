"""The five tutor endpoints. Paths and responses match frontend/src/services/tutorService.ts."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from peerora import crud
from peerora.database import get_db
from peerora.schemas import TutorIn, TutorOut

DUPLICATE_STUDENT_ID_MESSAGE = "A tutor with this University Student ID already exists."
NOT_FOUND_MESSAGE = "Tutor not found."

router = APIRouter(prefix="/api/tutors", tags=["tutors"])

# The id in the address must be a positive whole number that fits a database integer.
TutorId = Annotated[int, Path(ge=1, le=2147483647)]
# Each request receives its own database session (closed automatically afterwards).
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[TutorOut])
def list_tutors(db: DbSession):
    """Return every tutor as a plain JSON array."""
    return crud.list_tutors(db)


@router.get("/{tutor_id}", response_model=TutorOut)
def read_tutor(tutor_id: TutorId, db: DbSession):
    tutor = crud.get_tutor(db, tutor_id)
    if tutor is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return tutor


@router.post("", response_model=TutorOut, status_code=status.HTTP_201_CREATED)
def create_tutor(data: TutorIn, db: DbSession):
    try:
        return crud.create_tutor(db, data)
    except crud.DuplicateStudentIdError:
        raise HTTPException(status_code=409, detail=DUPLICATE_STUDENT_ID_MESSAGE) from None


@router.put("/{tutor_id}", response_model=TutorOut)
def update_tutor(tutor_id: TutorId, data: TutorIn, db: DbSession):
    """Full update: every field is replaced by the values sent."""
    try:
        tutor = crud.update_tutor(db, tutor_id, data)
    except crud.DuplicateStudentIdError:
        raise HTTPException(status_code=409, detail=DUPLICATE_STUDENT_ID_MESSAGE) from None
    if tutor is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return tutor


@router.delete("/{tutor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tutor(tutor_id: TutorId, db: DbSession):
    if not crud.delete_tutor(db, tutor_id):
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return Response(status_code=status.HTTP_204_NO_CONTENT)