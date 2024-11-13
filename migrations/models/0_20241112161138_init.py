from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "room" (
    "id" CHAR(36) NOT NULL  PRIMARY KEY,
    "room_type" VARCHAR(10)   /* STANDARD: Standard\nDELUXE: Deluxe\nSUITE: Suite */,
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
    "is_admin" INT NOT NULL  DEFAULT 0,
    "is_superuser" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_admin_email_f3e751" ON "admin" ("email");
CREATE TABLE IF NOT EXISTS "guest" (
    "uid" CHAR(36) NOT NULL  PRIMARY KEY,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "password_hash" VARCHAR(200) NOT NULL UNIQUE,
    "joined_at" DATE NOT NULL,
    "is_active" INT NOT NULL  DEFAULT 1,
    "is_admin" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_guest_email_dbffa6" ON "guest" ("email");
CREATE TABLE IF NOT EXISTS "reservation" (
    "id" CHAR(36) NOT NULL  PRIMARY KEY,
    "occupants" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "check_in_date" TIMESTAMP NOT NULL,
    "check_out_date" TIMESTAMP NOT NULL,
    "guest_checked_out" INT NOT NULL  DEFAULT 0,
    "status" VARCHAR(11) NOT NULL  DEFAULT 'pending' /* PENDING: pending\nCONFIRMED: confirmed\nCHECKED_IN: checked_in\nCHECKED_OUT: checked_out\nCANCELLED: cancelled */,
    "guest_id" CHAR(36) NOT NULL REFERENCES "guest" ("uid") ON DELETE NO ACTION
);
CREATE TABLE IF NOT EXISTS "review" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "rating" INT NOT NULL  DEFAULT 0,
    "comment" TEXT,
    "guest_id" CHAR(36) NOT NULL REFERENCES "guest" ("uid") ON DELETE NO ACTION,
    "room_id" CHAR(36) NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "roomavailability" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "booked" INT NOT NULL  DEFAULT 0,
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL,
    "reservation_id" CHAR(36) NOT NULL REFERENCES "reservation" ("id") ON DELETE CASCADE,
    "room_id" CHAR(36) NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_roomavailab_room_id_3c984a" UNIQUE ("room_id", "start_date", "end_date")
);
CREATE TABLE IF NOT EXISTS "guestrequest" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "request" TEXT NOT NULL,
    "request_type" VARCHAR(20) NOT NULL  /* HOUSE_KEEPING: house_keeping\nMAINTENANCE: maintenance\nDINING: dining\nEXTRA_AMENITIES: extra_amenities */,
    "request_status" VARCHAR(11) NOT NULL  /* PENDING: pending\nIN_PROGRESS: in_progress\nCOMPLETED: completed */,
    "priority" VARCHAR(10)   /* URGENT: urgent\nHIGH: high\nMEDIUM: medium\nLOW: low */,
    "extra" TEXT,
    "created" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "guest_id" CHAR(36) NOT NULL REFERENCES "guest" ("uid") ON DELETE NO ACTION,
    "reservation_id" CHAR(36) REFERENCES "reservation" ("id") ON DELETE CASCADE,
    "room_id" CHAR(36) NOT NULL REFERENCES "room" ("id") ON DELETE NO ACTION
);
CREATE TABLE IF NOT EXISTS "invoice" (
    "id" CHAR(36) NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(6) NOT NULL  DEFAULT 'unpaid' /* paid: paid\nunpaid: unpaid */,
    "transaction_id" VARCHAR(100),
    "guest_email" VARCHAR(100) NOT NULL,
    "amount" VARCHAR(40),
    "reservation_id" CHAR(36) NOT NULL UNIQUE REFERENCES "reservation" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "models.RoomAvailability" (
    "reservation_id" CHAR(36) NOT NULL REFERENCES "reservation" ("id") ON DELETE CASCADE,
    "room_id" CHAR(36) NOT NULL REFERENCES "room" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_models.Room_reserva_c21454" ON "models.RoomAvailability" ("reservation_id", "room_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
