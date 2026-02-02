"""CLI entry point for webterm."""

import argparse

import uvicorn

from webterm.core.config import settings
from webterm.logger import get_logger, set_log_level

logger = get_logger("cli")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="webterm",
        description="Web-based terminal",
    )

    parser.add_argument(
        "--host",
        type=str,
        default=settings.host,
        help=f"Host to bind to (default: {settings.host})",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Port to bind to (default: {settings.port})",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.reload,
        help="Enable auto-reload for development",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default=settings.log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Log level (default: {settings.log_level})",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for webterm CLI."""
    args = parse_args()

    # Set log level
    set_log_level(args.log_level)

    logger.info(f"Starting webterm on http://{args.host}:{args.port}")

    uvicorn.run(
        "webterm.api.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


if __name__ == "__main__":
    main()
