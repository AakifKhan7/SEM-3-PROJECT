import asyncio
from app.database import SessionLocal
from app.api.admin import get_admin_graphs

async def test():
    db = SessionLocal()
    try:
        res = await get_admin_graphs(db)
        print("Success:", list(res.keys()))
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test())
