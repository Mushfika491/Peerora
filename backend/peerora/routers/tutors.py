"""Tutor profile endpoints.

Reading is public. Creating requires a Tutor account (one profile each; the
owner comes from the access token). Updating and deleting require the owner or
an administrator. The private Student ID is only returned to those two.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from peerora import crud
from peerora.constants import ACCOUNT_TYPE_TUTOR, DEPARTMENTS, SUBJECTS, TEACHING_MODES
from peerora.core.dependencies import Client, CurrentUser, DbSession, OptionalUser, require_account_type
from peerora.models import User
from peerora.schemas import TutorIn, TutorOut, TutorPublicOut
from peerora.services.audit_service import AuditAction, log_event

DUPLICATE_STUDENT_ID_MESSAGE = "A tutor with this University Student ID already exists."
PROFILE_EXISTS_MESSAGE = "You already have a tutor profile."
NOT_FOUND_MESSAGE = "Tutor not found."
FORBIDDEN_MESSAGE = "You can only change your own tutor profile."

router = APIRouter(prefix="/api/tutors", tags=["tutors"])

# The id in the address must be a positive whole number that fits a database integer.
TutorId = Annotated[int, Path(ge=1, le=2147483647)]
TutorAccount = Annotated[User, Depends(require_account_type(ACCOUNT_TYPE_TUTOR))]


def _view(user: User | None, tutor) -> TutorOut | TutorPublicOut:
    """Full profile for the owner/admin, public profile for everyone else."""
    if crud.can_manage(user, tutor):
        return TutorOut.model_validate(tutor)
    return TutorPublicOut.model_validate(tutor)


def _get_manageable(db, user: User, tutor_id: int):
    tutor = crud.get_tutor(db, tutor_id)
    if tutor is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    if not crud.can_manage(user, tutor):
        raise HTTPException(status_code=403, detail=FORBIDDEN_MESSAGE)
    return tutor


@router.get("", response_model=list[TutorPublicOut])
def list_tutors(
    response: Response,
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100)] = None,
    subject: Annotated[str | None, Query(max_length=100)] = None,
    department: Annotated[str | None, Query(max_length=100)] = None,
    teaching_mode: Annotated[str | None, Query(max_length=20)] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Public tutor list (newest first) as a plain JSON array. The total number
    of matches is sent in the X-Total-Count header for pagination."""
    unknown_value = (
        (subject and subject not in SUBJECTS)
        or (department and department not in DEPARTMENTS)
        or (teaching_mode and teaching_mode not in TEACHING_MODES)
    )
    if unknown_value:
        response.headers["X-Total-Count"] = "0"
        return []  # a filter value outside the allowed lists matches nothing
    filters = crud.TutorFilters(q=q, subject=subject, department=department, teaching_mode=teaching_mode)
    tutors, total = crud.list_tutors(db, filters, limit, offset)
    response.headers["X-Total-Count"] = str(total)
    return tutors


@router.get("/me", response_model=TutorOut)
def read_my_tutor_profile(user: TutorAccount, db: DbSession):
    tutor = crud.get_tutor_by_user(db, user.id)
    if tutor is None:
        raise HTTPException(status_code=404, detail="You have not created a tutor profile yet.")
    return tutor


@router.get("/{tutor_id}", response_model=TutorOut | TutorPublicOut)
def read_tutor(tutor_id: TutorId, db: DbSession, user: OptionalUser):
    tutor = crud.get_tutor(db, tutor_id)
    if tutor is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return _view(user, tutor)


@router.post("", response_model=TutorOut, status_code=status.HTTP_201_CREATED)
def create_tutor(data: TutorIn, user: TutorAccount, db: DbSession):
    try:
        return crud.create_tutor(db, data, user_id=user.id)
    except crud.TutorProfileExistsError:
        raise HTTPException(status_code=409, detail=PROFILE_EXISTS_MESSAGE) from None
    except crud.DuplicateStudentIdError:
        raise HTTPException(status_code=409, detail=DUPLICATE_STUDENT_ID_MESSAGE) from None


@router.put("/{tutor_id}", response_model=TutorOut)
def update_tutor(tutor_id: TutorId, data: TutorIn, user: CurrentUser, db: DbSession, client: Client):
    """Full update: every field is replaced by the values sent."""
    tutor = _get_manageable(db, user, tutor_id)
    if tutor.user_id != user.id:
        log_event(db, AuditAction.TUTOR_PROFILE_MODERATED, client, actor_id=user.id,
                  target_user_id=tutor.user_id, target_type="tutor", target_id=tutor.id)
    try:
        return crud.update_tutor(db, tutor_id, data)
    except crud.DuplicateStudentIdError:
        raise HTTPException(status_code=409, detail=DUPLICATE_STUDENT_ID_MESSAGE) from None


@router.delete("/{tutor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tutor(tutor_id: TutorId, user: CurrentUser, db: DbSession, client: Client):
    tutor = _get_manageable(db, user, tutor_id)
    log_event(db, AuditAction.TUTOR_PROFILE_DELETED, client, actor_id=user.id, target_user_id=tutor.user_id,
              target_type="tutor", target_id=tutor.id,
              details={"full_name": tutor.full_name, "by_admin": tutor.user_id != user.id})
    crud.delete_tutor(db, tutor_id)  # commits the delete and the audit row together
    return Response(status_code=status.HTTP_204_NO_CONTENT)
