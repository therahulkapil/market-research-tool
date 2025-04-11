from fastapi import APIRouter

router = APIRouter()
@router.post("/addition", tags=["addition"])
async def division(a: int, b: int):
    """
    Add two numbers.
    """
    return {"result": a + b}