from internal.db import create_db_and_tables

if __name__ == "__main__":
    import asyncio

    async def main():
        await create_db_and_tables()

    asyncio.run(main())
