from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "invoice" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(6) NOT NULL  DEFAULT 'unpaid',
    "transaction_id" VARCHAR(100),
    "customer_email" VARCHAR(100) NOT NULL,
    "amount" DECIMAL(6,3),
    "reservation_id" UUID NOT NULL UNIQUE REFERENCES "reservation" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "invoice"."status" IS 'paid: paid\nunpaid: unpaid';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "invoice";"""
