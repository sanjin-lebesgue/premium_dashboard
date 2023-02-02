from datetime import datetime
from sqlalchemy import Float, and_, func, orm
from src import models, schemas
from src.crud.base import CRUDBase


class CRUDShopifyOrder(CRUDBase[models.ShopifyOrder, schemas.ShopifyOrderCreate, schemas.ShopifyOrderUpdate]):
    def get_sum_of_total_usd_in_period(
        self, db: orm.Session, shop_id: int, start: datetime, end: datetime
    ) -> int:
        return (
            db.query(func.coalesce(func.sum(models.ShopifyOrder.total_price_usd.cast(Float)), 0))
            .filter(
                and_(
                    models.ShopifyOrder.shop_id == shop_id,
                    models.ShopifyOrder.processed_at >= start,
                    models.ShopifyOrder.processed_at <= end,
                )
            )
            .scalar()
        )

    def get_with_customer_id_set(
        self,
        db: orm.Session,
        shop_id: int,
        offset: int,
        limit: int,
        include_orders_after: datetime | None = None,
    ) -> list[models.ShopifyOrder]:
        query = db.query(models.ShopifyOrder)

        if include_orders_after:
            query = query.filter(
                models.ShopifyOrder.shop_id == shop_id,
                models.ShopifyOrder.customer_id.isnot(None),
                models.ShopifyOrder.created_at >= include_orders_after,
            )
        else:
            query = query.filter(
                models.ShopifyOrder.shop_id == shop_id, models.ShopifyOrder.customer_id.isnot(None)
            )

        return query.order_by(models.ShopifyOrder.processed_at.asc()).offset(offset).limit(limit).all()

    def get_first_processed_with_customer_id(
        self, db: orm.Session, shop_id: int, customer_id: int
    ) -> models.ShopifyOrder | None:
        return (
            db.query(models.ShopifyOrder)
            .filter(models.ShopifyOrder.customer_id == customer_id, models.ShopifyOrder.shop_id == shop_id)
            .order_by(models.ShopifyOrder.processed_at.asc())
            .first()
        )

    def get_shop_customers_first_order_ids(self, db: orm.Session, shop_id: int):
        return db.execute(
            """select distinct on (customer_id) customer_id, id as first_order_id
                from shopify_order
                where shop_id = :shop_id
                and customer_id is not null
                order by customer_id, processed_at;""",
            {"shop_id": shop_id},
        )


shopify_order = CRUDShopifyOrder(models.ShopifyOrder)
