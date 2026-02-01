"""
Test adapter interface design to ensure clean and consistent API.

This test validates:
1. Adapters don't have get_mount_path() method (mount path is user's choice)
2. Adapters have create_app() method
3. Adapters work correctly with user-defined mount paths
"""
import os

import pytest

from fastapi_voyager import create_voyager
from fastapi_voyager.adapters.base import VoyagerAdapter


def test_adapter_base_class_does_not_have_get_mount_path():
    """Test that VoyagerAdapter base class does not define get_mount_path method."""
    # The base class should only have create_app as abstract method
    abstract_methods = VoyagerAdapter.__abstractmethods__

    # Should only have create_app
    assert "create_app" in abstract_methods, "create_app must be abstract"
    assert "get_mount_path" not in abstract_methods, "get_mount_path should not exist in base class"

    # Verify get_mount_path is not defined anywhere in the class
    assert not hasattr(VoyagerAdapter, "get_mount_path"), \
        "VoyagerAdapter should not have get_mount_path method - mount path is user's choice"


@pytest.mark.parametrize("app_factory", [
    pytest.param(lambda: __import__("fastapi", fromlist=["FastAPI"]).FastAPI(), id="fastapi"),
    pytest.param(lambda: __import__("litestar", fromlist=["Litestar"]).Litestar(), id="litestar"),
])
def test_adapter_create_app_exists_and_works(app_factory):
    """Test that adapters have create_app method and it works correctly."""
    # Import and setup
    app = app_factory()
    voyager_app = create_voyager(app)

    # Should return a valid app object
    assert voyager_app is not None, "create_voyager should return an app"

    # The returned app should be callable (ASGI interface)
    assert callable(voyager_app), "Voyager app must be callable (ASGI interface)"


def test_django_ninja_adapter_create_app_works():
    """Test that Django Ninja adapter works correctly."""
    import django

    # Setup Django BEFORE importing NinjaAPI
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_ninja.settings")
    django.setup()

    from ninja import NinjaAPI

    # Create API and voyager
    api = NinjaAPI()
    voyager_app = create_voyager(api)

    # Should return a valid ASGI app
    assert voyager_app is not None, "create_voyager should return an app"
    assert callable(voyager_app), "Voyager app must be callable (ASGI interface)"


def test_adapter_instances_do_not_have_get_mount_path():
    """Test that adapter instances do not have get_mount_path method."""
    from fastapi import FastAPI
    from litestar import Litestar
    import django

    # Test FastAPI adapter
    fastapi_app = FastAPI()
    voyager_app = create_voyager(fastapi_app)
    assert not hasattr(voyager_app, "get_mount_path"), \
        "FastAPI voyager app should not have get_mount_path method"

    # Test Litestar adapter
    litestar_app = Litestar()
    voyager_app = create_voyager(litestar_app)
    assert not hasattr(voyager_app, "get_mount_path"), \
        "Litestar voyager app should not have get_mount_path method"

    # Test Django Ninja adapter
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_ninja.settings")
    django.setup()
    from ninja import NinjaAPI
    ninja_api = NinjaAPI()
    voyager_app = create_voyager(ninja_api)
    assert not hasattr(voyager_app, "get_mount_path"), \
        "Django Ninja voyager app should not have get_mount_path method"


def test_mount_path_is_user_responsibility():
    """
    Test that mount path is completely under user control.

    This test documents and enforces the design principle that
    mount path should be decided by users in their embedding code,
    not hardcoded in adapters.
    """
    from fastapi import FastAPI
    import httpx

    # Test multiple different mount paths - all should work
    test_paths = [
        "/voyager",
        "/docs",
        "/api/viz",
        "/my-custom-path",
    ]

    for path in test_paths:
        app = FastAPI()
        voyager_app = create_voyager(app)
        app.mount(path, voyager_app)

        # Verify the path works using async client
        transport = httpx.ASGITransport(app=app)
        # Use loop.run_until_complete for sync context
        import asyncio
        async def check_path():
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"{path}/dot")
                assert response.status_code == 200, \
                    f"Mount path {path} should work - proves path is user's choice"

        asyncio.run(check_path())


def test_adapter_design_principles():
    """
    Test that adapter design follows correct principles.

    This test documents the design decision that:
    - Adapters create framework-specific apps
    - Users decide mount paths in their embedding code
    - Adapters should NOT hardcode mount paths
    """
    from fastapi import FastAPI
    from fastapi_voyager.adapters.base import VoyagerAdapter
    import inspect

    # Check that VoyagerAdapter only has one abstract method
    abstract_methods = VoyagerAdapter.__abstractmethods__
    assert len(abstract_methods) == 1, "Should only have one abstract method"
    assert "create_app" in abstract_methods, "Abstract method should be create_app"

    # Check that create_app signature is correct
    sig = inspect.signature(VoyagerAdapter.create_app)
    assert len(sig.parameters) == 1, "create_app should only take self parameter"
    assert sig.return_annotation != inspect.Signature.empty, "create_app should have return type annotation"

    # Verify the principle: voyager app doesn't impose mount path
    app = FastAPI()
    voyager_app = create_voyager(app)

    # The voyager app is just a standard ASGI app
    # It doesn't know or care about where it's mounted
    assert callable(voyager_app), "Voyager app must be callable ASGI interface"

    # User can mount it anywhere they want
    # This is verified by test_mount_path_is_user_responsibility
    assert True, "Design principle validated: mount path is user's responsibility"

