import time
import logging
import requests
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    JSON
)
from sqlalchemy.orm import sessionmaker, declarative_base

# ======================================================
# LOGGING CONFIG
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ======================================================
# DATABASE CONFIG (MYSQL)
# ======================================================
DB_HOST = "localhost"
DB_USER = "dbadmin"
DB_PASSWORD = "DbAdmin123!"   # ada '!' → encode
DB_NAME = "lansitec_solar_tracker"

DATABASE_URL = (
    "mysql+pymysql://"
    f"{DB_USER}:{DB_PASSWORD.replace('!', '%21')}"
    f"@{DB_HOST}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# ======================================================
# MODEL (TABLE: trackings)
# ======================================================
class Tracking(Base):
    __tablename__ = "trackings"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), index=True)
    container_number = Column(String(50))
    last_activity = Column(String(255))
    city = Column(String(100))
    activity_date = Column(DateTime)
    status = Column(Integer)
    raw_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# ⚠ Jangan create table baru
# Base.metadata.create_all(bind=engine)

# ======================================================
# TRACKING SCHEDULER
# ======================================================
class TrackingScheduler:
    BASE_URL = "https://sync.tantoline.id/edoc/service/tracking"

    def __init__(self, tracking_number: str, interval_seconds: int = 60):
        self.tracking_number = tracking_number
        self.interval_seconds = interval_seconds

    def fetch_and_save(self):
        db = SessionLocal()
        insert_time = datetime.utcnow()

        try:
            response = requests.get(
                self.BASE_URL,
                params={"c": self.tracking_number},
                timeout=30
            )

            if response.status_code != 200:
                logger.error(
                    f"API ERROR {response.status_code} "
                    f"[{self.tracking_number}]"
                )
                return

            payload = response.json()

            if not payload.get("status") or not payload.get("data"):
                logger.warning(
                    f"NO DATA [{self.tracking_number}]"
                )
                return

            item = payload["data"][0]

            activity_date = datetime.strptime(
                item["date"], "%d %b %Y"
            )

            tracking = Tracking(
                tracking_number=self.tracking_number,
                container_number=item.get("container_number"),
                last_activity=item.get("last_activity"),
                city=item.get("city"),
                activity_date=activity_date,
                status=1 if payload.get("status") else 0,
                raw_response=payload,
                created_at=insert_time
            )

            db.add(tracking)
            db.commit()

            logger.info(
                f"✓ INSERT SUCCESS [{self.tracking_number}] "
                f"at {insert_time}"
            )

        except Exception as e:
            db.rollback()
            logger.error(
                f"✗ INSERT FAILED [{self.tracking_number}] "
                f"ERROR: {str(e)}",
                exc_info=True
            )

        finally:
            db.close()

    def start(self):
        logger.info(
            f"🚀 Scheduler STARTED [{self.tracking_number}]"
        )
        logger.info(
            f"⏱ Interval: {self.interval_seconds} seconds"
        )

        try:
            while True:
                self.fetch_and_save()
                time.sleep(self.interval_seconds)

        except KeyboardInterrupt:
            logger.info("🛑 Scheduler STOPPED manually")

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    scheduler = TrackingScheduler(
        tracking_number="TAKU2548597",
        interval_seconds=60
    )
    scheduler.start()
