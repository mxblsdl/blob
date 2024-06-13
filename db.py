import aiosqlite

# Initialize the database
async def init_db():
    async with aiosqlite.connect("file_uploads.db") as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id TEXT PRIMARY KEY,
                bin BLOB,
                user TEXT
            )
        """
        )
        await db.commit()


# Initialize username table
async def init_user_db():
    async with aiosqlite.connect("file_uploads.db") as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """
        )
        await db.commit()


# Create database connection
async def get_db():
    db = await aiosqlite.connect("file_uploads.db")
    await db.set_trace_callback(print)
    try:
        yield db
    finally:
        await db.close()
