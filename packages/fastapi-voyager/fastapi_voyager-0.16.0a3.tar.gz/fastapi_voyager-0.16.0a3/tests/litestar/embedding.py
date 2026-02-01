"""
Litestar embedding example for fastapi-voyager.

This module demonstrates how to integrate voyager with a Litestar application.
"""
from fastapi_voyager import create_voyager
from tests.litestar.demo import app, diagram

# Create voyager app for visualization
# Note: create_voyager automatically detects Litestar and returns a Litestar app
voyager_app = create_voyager(
    app,
    er_diagram=diagram,
    module_color={"tests.service": "purple"},
    module_prefix="tests.service",
    swagger_url="/schema/swagger",
    initial_page_policy='first',
    ga_id='G-R64S7Q49VL',
    online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main",
    enable_pydantic_resolve_meta=True
)

# ASGI app that routes between main app and voyager
# This allows voyager to be accessed at /voyager while the main app handles other routes
async def asgi_app(scope, receive, send):
    """
    ASGI app that routes between main app and voyager.

    Usage:
        uvicorn tests.litestar.embedding:asgi_app --reload

    Then access:
        - http://localhost:8000/demo/* for the main app
        - http://localhost:8000/voyager for voyager UI
    """
    if scope["type"] == "http" and scope["path"].startswith("/voyager"):
        # Forward to voyager app
        # Remove /voyager prefix for the voyager app (it expects root path)
        new_scope = dict(scope)
        new_scope["path"] = scope["path"][8:]  # Remove '/voyager'
        if new_scope["path"] == "":
            new_scope["path"] = "/"
        if "raw_path" in new_scope:
            new_scope["raw_path"] = scope["raw_path"][8:]
        await voyager_app(new_scope, receive, send)
    else:
        # Forward to main app
        await app(scope, receive, send)

# Exports
# - Use `uvicorn tests.litestar.embedding:asgi_app --reload` for combined app (main + voyager at /voyager)
# - Use `uvicorn tests.litestar.embedding:app --reload` for main app only
# - Use `uvicorn tests.litestar.embedding:voyager_app --reload` for voyager only
