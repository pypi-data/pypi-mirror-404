"""Command line interface for fastapi-voyager."""
import argparse
import importlib
import importlib.util
import logging
import os
import sys
from typing import Any

from fastapi_voyager import server as viz_server
from fastapi_voyager.version import __version__
from fastapi_voyager.voyager import Voyager

logger = logging.getLogger(__name__)

# Framework type constants
SUPPORTED_FRAMEWORKS = ["fastapi", "litestar", "django-ninja"]


def load_app_from_file(module_path: str, app_name: str = "app", framework: str | None = None) -> Any:
    """Load web framework app from a Python module file."""
    try:
        # Convert relative path to absolute path
        if not os.path.isabs(module_path):
            module_path = os.path.abspath(module_path)

        # Load the module
        spec = importlib.util.spec_from_file_location("app_module", module_path)
        if spec is None or spec.loader is None:
            logger.error(f"Could not load module from {module_path}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules["app_module"] = module
        spec.loader.exec_module(module)

        # Get the app instance
        if not hasattr(module, app_name):
            logger.error(f"No attribute '{app_name}' found in the module")
            return None

        app = getattr(module, app_name)

        # Verify app type if framework is specified
        if framework is not None:
            if not _validate_app_framework(app, framework):
                logger.error(f"'{app_name}' is not a {framework} instance")
                return None

        return app

    except Exception as e:
        logger.error(f"Error loading app: {e}")
        return None


def load_app_from_module(module_name: str, app_name: str = "app", framework: str | None = None) -> Any:
    """Load web framework app from a Python module name."""
    try:
        # Temporarily add the current working directory to sys.path
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            path_added = True
        else:
            path_added = False

        try:
            # Import the module by name
            module = importlib.import_module(module_name)

            # Get the app instance
            if not hasattr(module, app_name):
                logger.error(f"No attribute '{app_name}' found in module '{module_name}'")
                return None

            app = getattr(module, app_name)

            # Verify app type if framework is specified
            if framework is not None:
                if not _validate_app_framework(app, framework):
                    logger.error(f"'{app_name}' is not a {framework} instance")
                    return None

            return app
        finally:
            # Cleanup: if we added the path, remove it
            if path_added and current_dir in sys.path:
                sys.path.remove(current_dir)

    except ImportError as e:
        logger.error(f"Could not import module '{module_name}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading app from module '{module_name}': {e}")
        return None


def _validate_app_framework(app: Any, framework: str) -> bool:
    """Validate that the app matches the expected framework type."""
    try:
        if framework == "fastapi":
            from fastapi import FastAPI
            return isinstance(app, FastAPI)
        elif framework == "litestar":
            from litestar import Litestar
            return isinstance(app, Litestar)
        elif framework == "django-ninja":
            from ninja import NinjaAPI
            return isinstance(app, NinjaAPI)
        return False
    except ImportError as e:
        logger.error(
            f"The {framework} package is not installed. "
            f"Install it with: uv add fastapi-voyager[{framework}]"
        )
        logger.debug(f"Import error details: {e}")
        return False


def generate_visualization(
    app: Any,
    output_file: str = "router_viz.dot", tags: list[str] | None = None,
    schema: str | None = None,
    show_fields: bool = False,
    module_color: dict[str, str] | None = None,
    route_name: str | None = None,
):

    """Generate DOT file for API router visualization."""
    analytics = Voyager(
        include_tags=tags,
        schema=schema,
        show_fields=show_fields,
        module_color=module_color,
        route_name=route_name,
    )

    analytics.analysis(app)

    dot_content = analytics.render_dot()
    
    # Optionally write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(dot_content)
    logger.info(f"DOT file generated: {output_file}")
    logger.info("To render the graph, use: dot -Tpng router_viz.dot -o router_viz.png")
    logger.info("Or view online: https://dreampuf.github.io/GraphvizOnline/")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Visualize web application's routing tree and dependencies (supports FastAPI, Litestar, Django-Ninja)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  voyager app.py --web fastapi                                                       # Load 'app' from app.py (FastAPI)
  voyager app.py --web litestar                                                      # Load 'app' from app.py (Litestar)
  voyager -m tests.demo --web django-ninja                                             # Load 'app' from demo module (Django-Ninja)
  voyager -m tests.demo --app=api --web fastapi                                       # Load 'api' from tests.demo
  voyager -m tests.demo --web fastapi --schema=NodeA                                    # filter nodes by schema name
  voyager -m tests.demo --web fastapi --tags=page restful                               # filter routes by tags
  voyager -m tests.demo --web fastapi --module_color=tests.demo:red --module_color=tests.service:yellow
  voyager -m tests.demo --web fastapi -o my_graph.dot                                   # Output to my_graph.dot
  voyager -m tests.demo --web fastapi --server                                          # start a local server to preview
  voyager -m tests.demo --web fastapi --server --port=8001                              # start a local server to preview
"""
    )

    # Create mutually exclusive group for module loading options
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "module",
        nargs="?",
        help="Python file containing the web application"
    )
    group.add_argument(
        "-m", "--module",
        dest="module_name",
        help="Python module name containing the web application (like python -m)"
    )

    parser.add_argument(
        "--web",
        choices=SUPPORTED_FRAMEWORKS,
        help="Web framework type (required when using --server): fastapi, litestar, django-ninja"
    )

    parser.add_argument(
        "--app", "-a",
        default="app",
        help="Name of the app variable (default: app)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="router_viz.dot",
        help="Output DOT file name (default: router_viz.dot)"
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Start a local server to preview the generated DOT graph"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the preview server when --server is used (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host/IP for the preview server when --server is used (default: 127.0.0.1). Use 0.0.0.0 to listen on all interfaces."
    )
    parser.add_argument(
        "--module_prefix",
        type=str,
        default=None,
        help="Prefix routes with module name when rendering brief view (only valid with --server)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"fastapi-voyager {__version__}"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="Only include routes whose first tag is in the provided list"
    )
    parser.add_argument(
        "--module_color",
        action="append",
        metavar="KEY:VALUE",
        help="Module color mapping as key1:value1 key2:value2 (module name to Graphviz color)"
    )
    # removed service_prefixes option
    parser.add_argument(
        "--schema",
        default=None,
        help="Filter schemas by name"
    )
    parser.add_argument(
        "--show_fields",
        choices=["single", "object", "all"],
        default="object",
        help="Field display mode: single (no fields), object (only object-like fields), all (all fields). Default: object"
    )
    parser.add_argument(
        "--route_name",
        type=str,
        default=None,
        help="Filter by route id (format: <endpoint>_<path with _>)"
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="INFO",
        help="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)"
    )
    
    args = parser.parse_args()

    # Validate arguments
    if args.module_prefix and not args.server:
        parser.error("--module_prefix can only be used together with --server")

    if not (args.module_name or args.module):
        parser.error("You must provide a module file or -m module name")

    # When --server is used, --web is required
    if args.server and not args.web:
        parser.error("--web is required when using --server. Please specify: fastapi, litestar, or django-ninja")

    # Determine the framework (default to the one specified, or None for non-server mode)
    framework = args.web if args.server else None

    # Configure logging based on --log-level
    level_name = (args.log_level or "INFO").upper()
    logging.basicConfig(level=level_name)

    # Load app based on the input method (module_name takes precedence)
    if args.module_name:
        app = load_app_from_module(args.module_name, args.app, framework)
    else:
        if not os.path.exists(args.module):
            logger.error(f"File '{args.module}' not found")
            sys.exit(1)
        app = load_app_from_file(args.module, args.app, framework)

    if app is None:
        sys.exit(1)
    
    # helper: parse KEY:VALUE pairs into dict
    def parse_kv_pairs(pairs: list[str] | None) -> dict[str, str] | None:
        if not pairs:
            return None
        result: dict[str, str] = {}
        for item in pairs:
            if ":" in item:
                k, v = item.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k:
                    result[k] = v
        return result or None

    try:
        module_color = parse_kv_pairs(args.module_color)
        if args.server:
            # Build a preview server using the appropriate framework
            try:
                import uvicorn
            except ImportError:
                logger.info("uvicorn is required to run the server. Install via 'pip install uvicorn' or 'uv add uvicorn'.")
                sys.exit(1)

            # Create voyager app - it auto-detects framework and returns appropriate app type
            app_server = viz_server.create_voyager(
                app,
                module_color=module_color,
                module_prefix=args.module_prefix,
                server_mode=True,  # Enable server mode to serve at root path
            )
            logger.info(f"Starting {args.web} preview server at http://{args.host}:{args.port} ... (Ctrl+C to stop)")
            uvicorn.run(app_server, host=args.host, port=args.port, log_level=level_name.lower())
        else:
            # Generate and write dot file locally
            generate_visualization(
                app, 
                args.output, 
                tags=args.tags, 
                schema=args.schema,
                show_fields=args.show_fields,
                module_color=module_color,
                route_name=args.route_name,
            )
    except Exception as e:
        logger.info(f"Error generating visualization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
