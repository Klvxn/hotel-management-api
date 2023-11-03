from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "room" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "room_type" VARCHAR(10),
    "room_number" INT NOT NULL UNIQUE,
    "booked" BOOL NOT NULL  DEFAULT False,
    "capacity" VARCHAR(500) NOT NULL,
    "price" DECIMAL(5,3) NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_room_room_nu_c51115" ON "room" ("room_number");
COMMENT ON COLUMN "room"."room_type" IS 'STANDARD: Standard\nDELUXE: Deluxe\nSUITE: Suite';
COMMENT ON COLUMN "room"."price" IS 'price of room per night';
CREATE TABLE IF NOT EXISTS "admin" (
    "uid" UUID NOT NULL  PRIMARY KEY,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "password_hash" VARCHAR(200) NOT NULL UNIQUE,
    "joined_at" DATE NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_admin" BOOL NOT NULL  DEFAULT True,
    "is_superuser" BOOL NOT NULL  DEFAULT False
);
CREATE INDEX IF NOT EXISTS "idx_admin_email_f3e751" ON "admin" ("email");
CREATE TABLE IF NOT EXISTS "customer" (
    "uid" UUID NOT NULL  PRIMARY KEY,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "password_hash" VARCHAR(200) NOT NULL UNIQUE,
    "joined_at" DATE NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_admin" BOOL NOT NULL  DEFAULT False,
    "is_superuser" BOOL NOT NULL  DEFAULT False
);
CREATE INDEX IF NOT EXISTS "idx_customer_email_0c7dc6" ON "customer" ("email");
CREATE TABLE IF NOT EXISTS "reservation" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "occupants" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "check_in_date" TIMESTAMPTZ NOT NULL,
    "check_out_date" TIMESTAMPTZ NOT NULL,
    "customer_checked_out" BOOL NOT NULL  DEFAULT False,
    "customer_id" UUID NOT NULL REFERENCES "customer" ("uid") ON DELETE NO ACTION,
    "room_id" UUID NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "review" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "rating" INT NOT NULL  DEFAULT 0,
    "comment" TEXT,
    "customer_id" UUID NOT NULL REFERENCES "customer" ("uid") ON DELETE NO ACTION,
    "room_id" UUID NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "invoice" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(6) NOT NULL  DEFAULT 'unpaid',
    "transaction_id" VARCHAR(100),
    "customer_email" VARCHAR(100) NOT NULL,
    "amount" DECIMAL(6,3),
    "reservations_id" UUID NOT NULL REFERENCES "reservation" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "invoice"."status" IS 'paid: paid\nunpaid: unpaid';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
