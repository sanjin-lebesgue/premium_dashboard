import datetime

from pydantic import Field

from src.schemas.api_model import APIModel


class FacebookAdAccountBase(APIModel):
    facebook_id: str = Field(..., alias="account_id")
    name: str
    currency: str
    shop_id: int
    created_time: datetime.datetime
    time_zone: str
    timezone_offset_hours_utc: int
    connected: bool


class FacebookAdAccountCreate(FacebookAdAccountBase):
    connected: bool = True


class FacebookAdAccountUpdate(FacebookAdAccountBase):
    pass


class FacebookAdAccountInLib(APIModel):
    account_id: str
    name: str
    currency: str
    time_zone: str = Field(..., alias="timezone_name")
    created_time: datetime.datetime | None = None
    timezone_offset_hours_utc: int


class FbAdAccount(FacebookAdAccountBase):
    id: int

    class Config:
        orm_mode = True
