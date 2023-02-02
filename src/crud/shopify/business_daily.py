from datetime import date
from sqlalchemy.orm import Session

from src.crud.base import CRUDBase
from src import models, schemas
from src.utils.common import timed_lru_cache
from src.utils.period import PeriodTypeBase, PeriodHandlerBase

from sqlalchemy.sql.expression import literal
from sqlalchemy import and_, func
from src.services.metrics.static.business import business_daily_metrics


class CRUDBusinessDaily(
    CRUDBase[models.BusinessDaily, schemas.BusinessDailyCreate, schemas.BusinessDailyUpdate]
):
    def get(self, db: Session, shop_id: int, date: date) -> models.BusinessDaily | None:
        return db.query(self.model).get((shop_id, date))

    @timed_lru_cache(
        seconds=5 * 60,
    )
    def get_per_period_metrics(
        self,
        db: Session,
        shop_id: int,
        period_type: PeriodTypeBase,
        date_first: date,
        date_last: date,
        metrics: tuple[str] = (),
        metrics_mapper: tuple[tuple[str]] = (),
        group_by: tuple[str] = [],
    ):
        """Returns metrics per period.

        Resulting list contains dictionaries with following keys:
            period
            date
            <metric labels>
        """

        metrics = list(metrics)
        group_by = list(group_by)
        metrics_mapper = {k: v for k, v in metrics_mapper}

        if not metrics:
            metrics = business_daily_metrics

        where = [
            self.model.shop_id == shop_id,
            self.model.date >= date_first,
            self.model.date <= date_last,
        ]

        if period_type == PeriodTypeBase.all:
            extended_group_by = [literal(1)] + [metrics_mapper.get(g, g) for g in group_by]
            cols = [literal(1).label("period")] + [
                getattr(self.model, metrics_mapper.get(g, g)).label(g) for g in group_by
            ]
            date_func = lambda x: None  # noqa: E731
        else:
            period_handler = PeriodHandlerBase(period_type)
            extended_group_by = [metrics_mapper.get(g, g) for g in group_by] + [
                func.to_char(self.model.date, period_handler.format)
            ]
            cols = [func.to_char(self.model.date, period_handler.format).label("period")] + [
                getattr(self.model, metrics_mapper.get(g, g)).label(g) for g in group_by
            ]
            date_func = period_handler.first_date

        for m in metrics:
            cols.append(func.sum(getattr(self.model, metrics_mapper.get(m, m))).label(m))

        data = self.get_all(db, where=and_(*where), group_by=extended_group_by, cols=cols)
        data = [d._asdict() for d in list(data)]

        for d in data:
            d["date"] = date_func(d["period"])

        return data


business_daily = CRUDBusinessDaily(models.BusinessDaily)
