"""Database migration system for Fairchild.

Migrations are stored as numbered SQL files in the migrations/ directory:
- 001_initial.sql
- 002_add_parent_id.sql
- etc.

Each migration runs exactly once, tracked in the fairchild_migrations table.
"""

from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def migrate(pool) -> None:
    """Run all pending database migrations in order.

    Usage:
        fairchild = Fairchild("postgresql://localhost/myapp")
        await fairchild.connect()
        await migrate(fairchild._pool)
    """
    async with pool.acquire() as conn:
        # Ensure migrations tracking table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fairchild_migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)

        # Get list of already applied migrations
        applied = set()
        rows = await conn.fetch("SELECT name FROM fairchild_migrations")
        for row in rows:
            applied.add(row["name"])

        # Find and run pending migrations in order
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        for migration_file in migration_files:
            name = migration_file.name

            if name in applied:
                continue

            print(f"Running migration: {name}")
            sql = migration_file.read_text()

            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO fairchild_migrations (name) VALUES ($1)",
                    name,
                )

            print(f"  Applied: {name}")

    print("Migrations complete.")


async def drop_all(pool) -> None:
    """Drop all Fairchild tables. Use with caution!"""
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS fairchild_workers CASCADE")
        await conn.execute("DROP TABLE IF EXISTS fairchild_jobs CASCADE")
        await conn.execute("DROP TABLE IF EXISTS fairchild_migrations CASCADE")
