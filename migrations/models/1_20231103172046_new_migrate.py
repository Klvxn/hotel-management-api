from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "customer" DROP COLUMN "is_superuser";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "customer" ADD "is_superuser" BOOL NOT NULL  DEFAULT False;"""
