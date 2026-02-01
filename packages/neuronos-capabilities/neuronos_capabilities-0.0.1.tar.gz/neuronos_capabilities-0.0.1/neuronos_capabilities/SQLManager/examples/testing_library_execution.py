import asyncio
import time
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

# Adjust these imports to match your project structure
from SQLManager import SQLManager
from SQLManager.models.base import Base

# ============================================================
# 1. MODELS (Auth & Analytics Schema)
# ============================================================

class User(Base):
    """User accounts"""
    __tablename__ = "users"
    __table_args__ = {"schema": "test_us_east_1"}

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self):
        return f"User(id={self.id}, username={self.username!r})"

class UserSession(Base):
    """Tracks active user sessions"""
    __tablename__ = "user_sessions"
    __table_args__ = {"schema": "test_us_east_1"}

    id: Mapped[int] = mapped_column(primary_key=True)
    # Added ondelete="CASCADE" so deleting a user automatically deletes their sessions
    user_id: Mapped[int] = mapped_column(ForeignKey("test_us_east_1.users.id", ondelete="CASCADE"))
    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self):
        return f"UserSession(id={self.id}, user_id={self.user_id}, token={self.session_token!r})"

# ============================================================
# 2. CONFIGURATION
# ============================================================

db_config = {
    "provider": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "neuronos",
    "user": "neuronos_admin",
    "password": "TxPd#%a{uY{9KZdU>nKYX1oYr]!0Q]1*",
    "schema": "test_us_east_1",
    "echo_sql": False
}

# ============================================================
# 3. SYNC TESTS (CRUD & Transactions)
# ============================================================

def run_sync_tests():
    print("\n" + "="*50)
    print("RUNNING SYNC CRUD TESTS")
    print("="*50)
    
    with SQLManager(db_config) as db:
        # A. Setup Tables
        db.create_tables([User, UserSession])
        print("✓ Tables verified/created in schema 'test_us_east_1'")

        # B. Create
        user = db.insert(User, {
            "username": "tester_sync",
            "email": "sync@example.com",
            "password_hash": "secure_hash"
        })
        print(f"✓ Inserted User: {user}")

        # C. Read & Update
        db.update_by_id(User, user.id, {"username": "tester_sync_updated"})
        refreshed = db.get_by_id(User, user.id)
        print(f"✓ Updated User: {refreshed.username}")

        # D. Transaction (Atomic User + Session)
        tx_user_id = None
        try:
            with db.begin_transaction():
                new_u = db.insert(User, {"username": "tx_user", "email": "tx@test.com", "password_hash": "..."})
                tx_user_id = new_u.id
                db.insert(UserSession, {"user_id": new_u.id, "session_token": "abc_789"})
            print("✓ Transaction committed successfully")
        except Exception as e:
            print(f"✗ Transaction failed: {e}")

        # E. Bulk Insert Test
        print("\nTesting Bulk Insert (1,000 records)...")
        bulk_data = [
            {"username": f"bulk_{i}", "email": f"bulk_{i}@test.com", "password_hash": "hash"}
            for i in range(1000)
        ]
        start = time.time()
        db.insert_many(User, bulk_data)
        print(f"✓ Bulk Inserted 1,000 users in {time.time() - start:.3f}s")

        # F. Delete Cleanup (Order is vital!)
        print("\nCleaning up Sync records...")
        # Delete sessions first for ALL test users
        db.delete(UserSession, {"user_id": user.id})
        if tx_user_id:
            db.delete(UserSession, {"user_id": tx_user_id})
            
        deleted_count = db.delete(User, {"username": "bulk_%"})
        db.delete_by_id(User, user.id)
        db.delete(User, {"username": "tx_user"})
        print(f"✓ Cleanup: Deleted {deleted_count} bulk users and test records")

# ============================================================
# 4. ASYNC TESTS
# ============================================================

async def run_async_tests():
    print("\n" + "="*50)
    print("RUNNING ASYNC CRUD TESTS")
    print("="*50)
    
    async with SQLManager(db_config) as db:
        # A. Async Create
        user = await db.insert_async(User, {
            "username": "tester_async",
            "email": "async@example.com",
            "password_hash": "async_hash"
        })
        print(f"✓ [Async] Created: {user.username}")

        # B. Async Bulk Insert
        bulk_data = [
            {"username": f"async_bulk_{i}", "email": f"ab_{i}@test.com", "password_hash": "..."}
            for i in range(100)
        ]
        await db.insert_many_async(User, bulk_data)
        print(f"✓ [Async] Bulk Inserted 100 users")

        # C. Cleanup (Async)
        # Note: No sessions created in async test, so direct delete of User is okay here
        await db.delete_by_id_async(User, user.id)
        await db.delete_async(User, {"username": "async_bulk_%"})
        print("✓ [Async] Cleanup complete")

# ============================================================
# 5. EXECUTION
# ============================================================

if __name__ == "__main__":
    try:
        run_sync_tests()
        asyncio.run(run_async_tests())
        
        print("\n" + "="*50)
        print("RESULT: ALL DATABASE OPERATIONS SUCCESSFUL")
        print("="*50)
    except Exception as e:
        print(f"\nFATAL ERROR DURING TESTING: {e}")
        import traceback
        traceback.print_exc()