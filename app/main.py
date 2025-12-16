from fastapi import Cookie, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
KRATOS_EXTERNAL_API_URL = os.getenv("KRATOS_EXTERNAL_API_URL")
KETO_API_READ_URL = os.getenv("KETO_API_READ_URL")

from .dependencies import get_query_token, get_token_header
from .internal import admin
from .routers import items, users

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# app.include_router(users.router)
# app.include_router(items.router)
# app.include_router(
#     admin.router,
#     prefix="/admin",
#     tags=["admin"],
#     dependencies=[Depends(get_token_header)],
#     responses={418: {"description": "I'm a teapot"}},
# )


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html", context={}
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin(ory_kratos_session: str | None = Cookie(default=None, alias="ory_kratos_session")):
    if not ory_kratos_session:
        return HTMLResponse(content="<h1>Unauthorized</h1>", status_code=401)

    # Check Kratos session
    response = requests.get(
        f"{KRATOS_EXTERNAL_API_URL}/sessions/whoami",
        cookies={"ory_kratos_session": ory_kratos_session}
    )
    
    if response.status_code != 200:
        return HTMLResponse(content="<h1>Unauthorized</h1>", status_code=401)
    
    try:
        session_data = response.json()
    except requests.exceptions.JSONDecodeError:
        return HTMLResponse(content="<h1>Internal Server Error</h1>", status_code=500)
    
    active = session_data.get('active')
    if not active:
        return HTMLResponse(content="<h1>Forbidden</h1>", status_code=403)

    email = session_data.get('identity', {}).get('traits', {}).get('email', '')
    first_name = session_data.get('identity', {}).get('traits', {}).get('name', {}).get('first', '')
    last_name = session_data.get('identity', {}).get('traits', {}).get('name', {}).get('last', '')

    # Check permissions with Keto
    keto_response = requests.get(
        f"{KETO_API_READ_URL}/relation-tuples/check",
        params={
            "namespace": "app",
            "object": "admin",
            "relation": "member",
            "subject_id": email,
        }
    )

    print(keto_response.status_code)
    
    if keto_response.status_code == 404:
        return HTMLResponse(content="<h1>Forbidden</h1>", status_code=403)
    
    try:
        keto_data = keto_response.json()
    except requests.exceptions.JSONDecodeError:
        return HTMLResponse(content="<h1>Internal Server Error</h1>", status_code=500)
    
    if not keto_data.get("allowed"):
        return HTMLResponse(content="<h1>Forbidden</h1>", status_code=403)
    return HTMLResponse(content=f"<h1>Hello, {first_name} {last_name}! You are an admin.</h1>", status_code=200)

@app.get("/hello", response_class=HTMLResponse)
async def hello(ory_kratos_session: str | None = Cookie(default=None, alias="ory_kratos_session")):
    if not ory_kratos_session:
        return HTMLResponse(content="<h1>Unauthorized</h1>", status_code=401)

    # Check Kratos session
    response = requests.get(
        f"{KRATOS_EXTERNAL_API_URL}/sessions/whoami",
        cookies={"ory_kratos_session": ory_kratos_session}
    )
    
    if response.status_code != 200:
        return HTMLResponse(content="<h1>Unauthorized</h1>", status_code=401)
    
    try:
        session_data = response.json()
    except requests.exceptions.JSONDecodeError:
        return HTMLResponse(content="<h1>Internal Server Error</h1>", status_code=500)
    
    active = session_data.get('active')
    if not active:
        return HTMLResponse(content="<h1>Forbidden</h1>", status_code=403)

    email = session_data.get('identity', {}).get('traits', {}).get('email', '').replace('@', '')
    first_name = session_data.get('identity', {}).get('traits', {}).get('name', {}).get('first', '')
    last_name = session_data.get('identity', {}).get('traits', {}).get('name', {}).get('last', '')

    return HTMLResponse(content=f"<h1>Hello, {first_name} {last_name}!</h1>", status_code=200)

    # # Check permissions with Keto
    # keto_response = requests.get(
    #     f"{KETO_API_READ_URL}/check",
    #     params={
    #         "namespace": "app",
    #         "object": "homepage",
    #         "relation": "read",
    #         "subject_id": email,
    #     }
    # )
    
    # if keto_response.status_code == 404:
    #     return HTMLResponse(content="<h1>Forbidden</h1>", status_code=403)
    
    # try:
    #     keto_data = keto_response.json()
    # except requests.exceptions.JSONDecodeError:
    #     return HTMLResponse(content="<h1>Internal Server Error</h1>", status_code=500)
    
    # if not keto_data.get("allowed"):
    #     return HTMLResponse(content="<h1>Forbidden</h1>", status_code=403)
    # return HTMLResponse(content="<h1>Hello, World!</h1>", status_code=200)