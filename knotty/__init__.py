from fastapi import FastAPI

import knotty.route.namespace
import knotty.route.package
import knotty.route.permission
import knotty.route.user

app = FastAPI()
app.include_router(knotty.route.namespace.router)
app.include_router(knotty.route.package.router)
app.include_router(knotty.route.permission.router)
app.include_router(knotty.route.user.router)


@app.get("/")
def root():
    return {"version": "knotty v0.0.1"}
