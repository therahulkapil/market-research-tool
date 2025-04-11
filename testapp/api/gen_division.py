from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/division", tags=["division"])
async def division(a: int, b: int):
    """
    Divide two numbers.
    """
    if b == 0:
        return {"error": "Division by zero is not allowed."}
    return {"result": a / b}