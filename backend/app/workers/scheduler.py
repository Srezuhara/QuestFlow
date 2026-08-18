"""APScheduler worker entrypoint — placeholder for phase 0.

Real logic (reminder delivery, Web Push, streak-risk nudges) lands in
phase 7. For now this just proves the `worker` container stays up and logs
a heartbeat, so `docker compose up` gives a working four-service skeleton.
"""

import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s worker %(levelname)s %(message)s")
logger = logging.getLogger("questflow.worker")


def main() -> None:
    logger.info("QuestFlow worker starting (placeholder — no scheduled jobs yet, see phase 7)")
    while True:
        logger.info("worker heartbeat — idle, waiting for phase 7 (APScheduler + Web Push)")
        time.sleep(60)


if __name__ == "__main__":
    main()
