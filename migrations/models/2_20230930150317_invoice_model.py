from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "invoice" (
    "id" CHAR(36) NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(6) NOT NULL  DEFAULT 'unpaid' /* paid: paid\nunpaid: unpaid */,
    "transaction_id" VARCHAR(100),
    "customer" VARCHAR(100) NOT NULL,
    "amount" VARCHAR(40),
    "reservations_id" CHAR(36) NOT NULL REFERENCES "reservation" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "invoice";"""
