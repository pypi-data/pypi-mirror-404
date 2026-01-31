from fastapi import APIRouter

router = APIRouter(prefix="", tags=["healthz"])


@router.get("/healthzReadiness", include_in_schema=False)
async def get_healthz_readiness() -> str:
    return "OK"


@router.get("/healthzLiveness", include_in_schema=False)
async def get_healthz_liveness() -> str:
    return "OK"


@router.get("/healthzStartup", include_in_schema=False)
async def get_healthz_startup() -> str:
    return "OK"
