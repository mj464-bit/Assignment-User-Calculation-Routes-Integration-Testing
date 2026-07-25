from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationCreate, CalculationUpdate, CalculationResponse
from app.auth.jwt import get_current_user

router = APIRouter(prefix="/calculations", tags=["calculations"])


def _get_owned_calculation(calc_id: UUID, current_user: User, db: Session) -> Calculation:
    """Fetch a calculation by id, scoped to the current user, or 404."""
    calculation = (
        db.query(Calculation)
        .filter(Calculation.id == calc_id, Calculation.user_id == current_user.id)
        .first()
    )
    if not calculation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")
    return calculation


# add
@router.post("", response_model=CalculationResponse, status_code=status.HTTP_201_CREATED)
def create_calculation(
    calculation_data: CalculationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute and persist a new calculation owned by the authenticated user."""
    try:
        new_calculation = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        new_calculation.result = new_calculation.get_result()
        db.add(new_calculation)
        db.commit()
        db.refresh(new_calculation)
        return new_calculation
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# browse
@router.get("", response_model=List[CalculationResponse])
def list_calculations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List every calculation belonging to the authenticated user."""
    return db.query(Calculation).filter(Calculation.user_id == current_user.id).all()


# read
@router.get("/{calc_id}", response_model=CalculationResponse)
def get_calculation(
    calc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch a single calculation by id, if it belongs to the authenticated user."""
    return _get_owned_calculation(calc_id, current_user, db)


# edit
@router.put("/{calc_id}", response_model=CalculationResponse)
def update_calculation(
    calc_id: UUID,
    calculation_update: CalculationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a calculation's inputs and recompute its result."""
    calculation = _get_owned_calculation(calc_id, current_user, db)
    try:
        if calculation_update.inputs is not None:
            calculation.inputs = calculation_update.inputs
            calculation.result = calculation.get_result()
        db.commit()
        db.refresh(calculation)
        return calculation
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# delete
@router.delete("/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calculation(
    calc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a calculation owned by the authenticated user."""
    calculation = _get_owned_calculation(calc_id, current_user, db)
    db.delete(calculation)
    db.commit()
    return None
