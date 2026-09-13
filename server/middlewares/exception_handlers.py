from fastapi import Request
from fastapi.responses import JSONResponse
from logger import logger


async def catch_exception_middleware(req:Request,call_next):
    try:
        return await call_next(req)
    except Exception as exc:
        logger.exception("UNHANDLED EXCEPTION")
        return JSONResponse(status_code=500,content={"error":str(exc)})

    

