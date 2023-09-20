from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "room" (
    "id" CHAR(36) NOT NULL  PRIMARY KEY,
    "room_number" INT NOT NULL UNIQUE,
    "booked" INT NOT NULL  DEFAULT 0,
    "capacity" VARCHAR(500) NOT NULL,
    "price" VARCHAR(40) NOT NULL  /* price of room per night */
);
CREATE INDEX IF NOT EXISTS "idx_room_room_nu_c51115" ON "room" ("room_number");
CREATE TABLE IF NOT EXISTS "admin" (
    "uid" CHAR(36) NOT NULL  PRIMARY KEY,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "password_hash" VARCHAR(200) NOT NULL UNIQUE,
    "joined_at" DATE NOT NULL,
    "is_active" INT NOT NULL  DEFAULT 1,
    "is_superuser" INT NOT NULL  DEFAULT 0,
    "is_admin" INT NOT NULL  DEFAULT 1
);
CREATE INDEX IF NOT EXISTS "idx_admin_email_f3e751" ON "admin" ("email");
CREATE TABLE IF NOT EXISTS "customer" (
    "uid" CHAR(36) NOT NULL  PRIMARY KEY,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "password_hash" VARCHAR(200) NOT NULL UNIQUE,
    "joined_at" DATE NOT NULL,
    "is_active" INT NOT NULL  DEFAULT 1,
    "is_admin" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_customer_email_0c7dc6" ON "customer" ("email");
CREATE TABLE IF NOT EXISTS "reservation" (
    "id" CHAR(36) NOT NULL  PRIMARY KEY,
    "occupants" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "check_in_date" TIMESTAMP NOT NULL,
    "check_out_date" TIMESTAMP NOT NULL,
    "customer_checked_out" INT NOT NULL  DEFAULT 0,
    "customer_id" CHAR(36) NOT NULL REFERENCES "customer" ("uid") ON DELETE NO ACTION,
    "room_id" CHAR(36) NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "review" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "rating" INT NOT NULL  DEFAULT 0,
    "comment" TEXT,
    "customer_id" CHAR(36) NOT NULL REFERENCES "customer" ("uid") ON DELETE NO ACTION,
    "room_id" CHAR(36) NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
