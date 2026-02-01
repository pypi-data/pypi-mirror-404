from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_pundra.rest.exceptions import BaseAPIException, MethodNotAllowedException
from datetime import datetime

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(request: Request, exc: BaseAPIException):
        error_response = exc.to_dict()
        error_response["path"] = request.url.path
        error_response["type"] = exc.__class__.__name__
        error_response["timestamp"] = datetime.now().isoformat()

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    @app.middleware("http")
    async def exception_handling(request: Request, call_next):
        try:
            response = await call_next(request)
            
            # Method not allowed exception.
            if response.status_code == 405:
                raise MethodNotAllowedException(message="Method not allowed")
            
            return response
        except Exception as exc:
            error_details = {
                "success": False,
                "message": str(exc),
                "type": exc.__class__.__name__,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat()
            }

            return JSONResponse(status_code=500, content=error_details)