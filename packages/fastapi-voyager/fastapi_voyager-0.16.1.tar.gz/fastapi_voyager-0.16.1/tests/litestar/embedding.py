"""
Litestar embedding example for fastapi-voyager.

This module demonstrates how to integrate voyager with a Litestar application.

Unlike FastAPI, Litestar doesn't support mounting to an existing app after creation.
The recommended pattern is to reuse the ROUTE_HANDLERS from demo.py.
"""
from typing import Any, Awaitable, Callable

from litestar import Litestar, asgi

from fastapi_voyager import create_voyager
from tests.litestar.demo import ROUTE_HANDLERS, app as demo_app, diagram

# Create voyager app (returns a Litestar app)
voyager_app = create_voyager(
    demo_app,
    er_diagram=diagram,
    module_color={"tests.service": "purple"},
    module_prefix="tests.service",
    swagger_url="/schema/swagger",
    initial_page_policy='first',
    ga_id='G-R64S7Q49VL',
    online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main",
    enable_pydantic_resolve_meta=True
)

# Mount voyager using Litestar's @asgi() decorator
@asgi("/voyager", is_mount=True, copy_scope=True)
async def voyager_mount(
    scope: dict[str, Any],
    receive: Callable[[], Awaitable[dict[str, Any]]],
    send: Callable[[dict[str, Any]], Awaitable[None]]
) -> None:
    await voyager_app(scope, receive, send)

# Create combined app by reusing ROUTE_HANDLERS from demo.py
# This is the recommended pattern for Litestar
app = Litestar(route_handlers=ROUTE_HANDLERS + [voyager_mount])

# Exports
# - Use `uvicorn tests.litestar.embedding:app --reload` for combined app
# - Use `uvicorn tests.litestar.embedding:demo_app --reload` for demo only
