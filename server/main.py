from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.exception_handlers import catch_exception_middleware
from routes.upload_pdfs import router as upload_router
from routes.ask_question import router as ask_router

app=FastAPI(title="Medical Assistant ",description="Apis for the app")

#cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


#routers a.upload b.asking queries
app.middleware("http")(catch_exception_middleware)
app.include_router(upload_router)
app.include_router(ask_router)

