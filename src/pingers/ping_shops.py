import sys

sys.path.append("././.")

import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from loguru import logger

from src.utils.decorators import print_execution_time

from src.models import *


@print_execution_time
def ping_shops(
    db: Session,
    start_date: str = None,
    end_date: str = date.today().strftime("%Y-%m-%d"),
) -> pd.DataFrame:

    logger.debug("Here I am!")

    query = db.query(FacebookAd.shop_id)

    if start_date is not None:
        query = query.join(FacebookDailyPerformance).filter(
            FacebookDailyPerformance.date_start >= start_date,
            FacebookDailyPerformance.date_start <= end_date,
        )

    query = query.distinct()

    query = query.join(Shop, FacebookAd.shop_id == Shop.id).add_columns(Shop.name)
    df = pd.read_sql(query.statement, db.bind)

    return df