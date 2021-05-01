-- CreateTable
CREATE TABLE "User" (
    "discordId" INTEGER NOT NULL,
    "steamId" INTEGER NOT NULL,

    PRIMARY KEY ("discordId", "steamId")
);
