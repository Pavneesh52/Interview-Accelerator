from app.api.v1 import auth, documents, analysis

api_router = auth.router
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])