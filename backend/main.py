# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from backend.api.routes import router
# from backend.database import init_db

# app = FastAPI(
#     title="Nimbus Freight Cold-Chain Alerting API",
#     version="1.0.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "http://127.0.0.1:5173"
#     ],
#     allow_methods=["GET"],
#     allow_headers=["*"]
# )

# app.include_router(router)


# @app.on_event("startup")
# def startup():
#     init_db()


# @app.get("/")
# def home():
#     return {"message": "Nimbus Freight Cold-Chain API"}


# @app.get("/health")
# def health():
#     return {"status": "ok"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.database import init_db
from backend.auth.routes import router as auth_router

app = FastAPI(
    title="Nimbus Freight Cold-Chain Alerting API",
    description="Sensor monitoring and sustained temperature violation detection",
    version="1.0.0",
)
app.include_router(auth_router)
app.include_router(router)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "http://127.0.0.1:5173",
#     ],
#     allow_methods=["GET"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {
        "message": "Nimbus Freight Cold-Chain API",
        "documentation": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
