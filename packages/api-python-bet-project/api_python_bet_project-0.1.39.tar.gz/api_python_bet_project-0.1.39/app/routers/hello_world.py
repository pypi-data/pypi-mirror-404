from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/hello-word", tags=["hello-world"])


@router.get("")
async def get_hello_word() -> str:
    return "Hello World!"
