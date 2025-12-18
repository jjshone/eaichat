"""Init DB helper: creates tables using models.Base.metadata.create_all
This script runs inside the API container and will create tables against the configured MYSQL DB.
"""
import logging
from app.db import engine, Base


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logging.info("Done.")


if __name__ == '__main__':
    main()
