from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)