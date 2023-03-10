from src.s3.s3_connect import s3_connect
import re
import boto3
import pandas as pd
from datetime import datetime
import numpy as np

import sqlalchemy

from src.utils.common import read_csv_and_eval
from src.feature_extractors import *
from src.crud import crud_fb_daily_performance

from src.database.session import SessionLocal


def get_shop_ids() -> list:
    client = s3_connect()

    response = client.list_objects_v2(Bucket="creative-features", Prefix="data/creative_by_shop_id/")
    list_of_paths = [content["Key"] for content in response["Contents"]]
    shop_ids = [re.findall("[\d]+(?=.csv)", path)[0] for path in list_of_paths]

    return shop_ids


def get_data_by_shop_id(
    shop_id: str | list[str],
    start_date: str = "2015-01-01",
    end_date: str = datetime.strftime(datetime.today(), "%Y-%m-%d"),
) -> pd.DataFrame:
    df = read_creative_data_by_shop_id(shop_id)
    df = join_with_performance(df=df, shop_id=shop_id, start_date=start_date, end_date=end_date)

    return df


def read_creative_data_by_shop_id(
    shop_id: str | list[str],
) -> pd.DataFrame:
    client = s3_connect()

    if type(shop_id) == str:
        object = client.get_object(Bucket="creative-features", Key=f"data/creative_by_shop_id/{shop_id}.csv")
        creative = read_csv_and_eval(object["Body"])

    else:
        object = client.get_object(Bucket="creative-features", Key=f"data/creative_by_shop_id/{shop_id[0]}.csv")
        creative = read_csv_and_eval(object["Body"])
        for id in shop_id[1:]:
            object = client.get_object(Bucket="creative-features", Key=f"data/creative_by_shop_id/{id}.csv")
            creative_new = read_csv_and_eval(object["Body"])
            creative = pd.concat([creative, creative_new], axis=0)

    return creative


def join_with_performance(
    df: pd.DataFrame,
    shop_id: str | list[str],
    session=None,
    start_date: str = "2015-01-01",
    end_date: str = datetime.strftime(datetime.today(), "%Y-%m-%d"),
) -> pd.DataFrame:
    if session is None:
        session = SessionLocal()

    query = crud_fb_daily_performance.query_performance(
        session=session, shop_id=shop_id, start_date=start_date, end_date=end_date
    )

    performance = pd.read_sql(query.statement, session.bind)

    performance = add_performance_columns(performance)

    full = df.merge(performance)

    return full
