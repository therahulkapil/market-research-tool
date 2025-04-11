from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/subtraction", tags=["subtraction"])
async def subtraction(a: int, b: int):
    """
    Subtract two numbers.
    """
    return {"result": a - b}