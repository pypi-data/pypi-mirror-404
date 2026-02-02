import argparse
import asyncio
import logging
import os
import sys

from hearth_worker.agent.main import HearthAgent


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Hearth Worker Agent")
    parser.add_argument(
        "--config",
        default=os.environ.get("HEARTH_CONFIG", "/opt/hearth-agent/config.yaml"),
        help="Path to config file",
    )
    args = parser.parse_args()

    config_path = args.config if os.path.exists(args.config) else None

    try:
        agent = HearthAgent(config_path=config_path)
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
