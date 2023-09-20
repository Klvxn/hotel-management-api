from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "room" ADD "room_type" VARCHAR(10)   /* STANDARD: standard\nDELUXE: deluxe\nSUITE: suite */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "room" DROP COLUMN "room_type";"""
