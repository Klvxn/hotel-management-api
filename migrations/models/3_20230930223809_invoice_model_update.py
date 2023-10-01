from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "invoice" RENAME COLUMN "customer" TO "customer_email";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "invoice" RENAME COLUMN "customer_email" TO "customer";"""
