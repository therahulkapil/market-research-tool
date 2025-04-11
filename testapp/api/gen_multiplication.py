from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/multiplication", tags=["multiplication"])
async def multiplication(a: int, b: int):
    """
    Multiply two numbers.
    """
    return {"result": a * b}