from fastapi import FastAPI

from cm_customer_svc.routers.auth import auth_router

app = FastAPI(debug=True)

# add routers
app.include_router(auth_router, prefix="/api/auth")
