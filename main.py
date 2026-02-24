"""
University ERP — Python Worker Entry Point

Loads configuration, initialises the logger, connects to the
database, and starts the background worker loop (RabbitMQ
consumer or gRPC server) to accept tasks from the Elixir
API gateway.
"""

from __future__ import annotations

import os
import sys
import signal
import yaml
from typing import Any, Dict

# Ensure the project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from python_core.utils.logger import ERPLogger
from python_core.utils.exceptions import ConfigurationError


def _resolve_env_vars(obj):
    """Recursively resolve ${VAR:-default} patterns in config values."""
    import re
    pattern = re.compile(r'\$\{(\w+)(?::-(.*?))?\}')
    if isinstance(obj, str):
        def replacer(m):
            return os.environ.get(m.group(1), m.group(2) or "")
        return pattern.sub(replacer, obj)
    elif isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj


def load_config(path: str = None) -> Dict[str, Any]:
    """Load and validate settings.yaml, resolving env-var placeholders."""
    if path is None:
        path = os.path.join(PROJECT_ROOT, "config", "settings.yaml")
    if not os.path.isfile(path):
        raise ConfigurationError("settings.yaml", f"File not found: {path}")
    with open(path, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict):
        raise ConfigurationError("settings.yaml", "Root must be a YAML mapping")
    return _resolve_env_vars(config)


def configure_logging(config: Dict[str, Any]) -> None:
    """Initialise the ERP logger from config."""
    log_cfg = config.get("logging", {})
    ERPLogger.configure(
        level=log_cfg.get("level", "DEBUG"),
        fmt=log_cfg.get("format"),
        log_file=log_cfg.get("file"),
        max_bytes=log_cfg.get("max_bytes", 10_485_760),
        backup_count=log_cfg.get("backup_count", 5),
    )


def connect_database(config: Dict[str, Any]):
    """
    Create a psycopg2 connection pool.

    Returns the connection pool object (or None if psycopg2
    is not installed — graceful degradation for dev).
    """
    db_cfg = config.get("database", {})
    try:
        import psycopg2
        from psycopg2 import pool

        return pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=db_cfg.get("pool_size", 20),
            host=db_cfg.get("host", "localhost"),
            port=db_cfg.get("port", 5432),
            dbname=db_cfg.get("name", "university_erp"),
            user=db_cfg.get("user", "erp_admin"),
            password=os.environ.get("DB_PASSWORD", db_cfg.get("password", "")),
            connect_timeout=db_cfg.get("timeout", 30),
        )
    except ImportError:
        return None


def start_message_consumer(config: Dict[str, Any], db_pool: Any) -> None:
    """
    Block on a RabbitMQ consumer that processes tasks dispatched
    by the Elixir gateway.  Placeholder for full implementation.
    """
    log = ERPLogger.get_logger("main")
    mq_cfg = config.get("message_queue", {})

    log.info("═══ University ERP Python Worker ═══")
    log.info("Environment : %s", config.get("environment", "development"))
    log.info("MQ host     : %s:%s", mq_cfg.get("host"), mq_cfg.get("port"))
    log.info("DB pool     : %s", "connected" if db_pool else "unavailable (dev mode)")

    try:
        import pika

        credentials = pika.PlainCredentials(
            mq_cfg.get("user", "guest"), mq_cfg.get("password", "guest")
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=mq_cfg.get("host", "localhost"),
                port=mq_cfg.get("port", 5672),
                credentials=credentials,
            )
        )
        channel = connection.channel()

        # Declare queues
        for queue_name in mq_cfg.get("queues", {}).values():
            channel.queue_declare(queue=queue_name, durable=True)
            log.info("Listening on queue: %s", queue_name)

        def callback(ch, method, properties, body):
            log.info("Received task: %s", body[:200])
            # TODO: dispatch to appropriate service
            ch.basic_ack(delivery_tag=method.delivery_tag)

        etl_queue = mq_cfg.get("queues", {}).get("etl_tasks", "etl_task_queue")
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=etl_queue, on_message_callback=callback)

        log.info("Worker ready — waiting for tasks. Press Ctrl+C to exit.")
        channel.start_consuming()

    except ImportError:
        log.warning("pika not installed — running in standalone dev mode")
        log.info("Worker idle. Install pika for RabbitMQ support.")
        # Block until SIGINT
        signal.pause() if hasattr(signal, "pause") else input("Press Enter to exit...\n")
    except Exception as exc:
        log.error("Worker failed: %s", exc)
        raise


def main() -> None:
    config = load_config()
    configure_logging(config)
    db_pool = connect_database(config)
    start_message_consumer(config, db_pool)


if __name__ == "__main__":
    main()
