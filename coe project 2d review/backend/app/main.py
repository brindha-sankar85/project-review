import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.database_init import init_db
from backend.app.routes import auth, documents, sharing, audit, events, experiments, validation

# Initialize FastAPI application
app = FastAPI(
    title="Confidentiality-Aware Hospital Knowledge Summarisation & Sharing Assistant",
    description="End-to-End Hospital Confidentiality Assistant with RBAC, Redacted Summarization, Human Approvals, Resilient Event Handling & Baseline Evaluation",
    version="1.0.0"
)

# Initialize Database and seed synthetic data
@app.on_event("startup")
def startup_event():
    init_db(seed_data=True)

# Include API Routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(sharing.router)
app.include_router(audit.router)
app.include_router(events.router)
app.include_router(experiments.router)
app.include_router(validation.router)

# Serve Frontend Static Files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def read_root():
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Backend API is running. Frontend index.html not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
