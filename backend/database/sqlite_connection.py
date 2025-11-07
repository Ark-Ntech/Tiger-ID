"""SQLite connection for demo/testing mode (no PostgreSQL required)"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from pathlib import Path

from backend.database.models import Base, Tiger, TigerImage

# Import AuditLog model so it's included in Base.metadata
from backend.database.audit_models import AuditLog  # noqa: F401

# SQLite database path - use production.db for production, demo.db for demo
USE_SQLITE_DEMO = os.getenv("USE_SQLITE_DEMO", "false").lower() == "true"
if USE_SQLITE_DEMO:
    DB_PATH = Path("data/demo.db")
else:
    DB_PATH = Path("data/production.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create SQLite engine
sqlite_engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # Needed for FastAPI
    pool_pre_ping=True,
    echo=False
)

# Enable foreign keys for SQLite
@event.listens_for(sqlite_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory
SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)


def get_sqlite_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get SQLite database session"""
    db = SQLiteSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_sqlite_session() -> Generator[Session, None, None]:
    """Context manager for SQLite database sessions"""
    session = SQLiteSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_sqlite_db():
    """Initialize SQLite database tables"""
    # Import all models to ensure they're registered with Base.metadata
    from backend.database.models import (
        User, Tiger, TigerImage, Facility, Investigation, InvestigationStep,
        Evidence, InvestigationTemplate, SavedSearch, InvestigationComment,
        InvestigationAnnotation, CrawlHistory, UserSession, PasswordResetToken,
        Notification, VerificationQueue
    )
    # AuditLog is already imported at module level
    # Ensure all models are registered
    import backend.database.models  # noqa: F401
    import backend.database.audit_models  # noqa: F401
    
    # Drop all tables first for clean slate
    Base.metadata.drop_all(bind=sqlite_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=sqlite_engine)
    
    # Verify audit_logs table was created
    from sqlalchemy import inspect
    inspector = inspect(sqlite_engine)
    tables = inspector.get_table_names()
    if 'audit_logs' not in tables:
        print("WARNING: audit_logs table was not created!")
    else:
        print("[OK] audit_logs table verified")
    
    print(f"[OK] SQLite database tables created ({len(tables)} tables)")


def create_demo_data():
    """Create demo data including admin user, investigations, evidence, and agent activities.
    Also enriches database with facility data from non-accredited facilities dataset.
    """
    from backend.database.models import (
        User, UserRole, Investigation, Tiger, Facility, 
        InvestigationStatus, Priority, TigerStatus, InvestigationStep,
        Evidence, EvidenceSourceType
    )
    from backend.auth.auth import hash_password
    import uuid
    from datetime import datetime, timedelta
    
    with get_sqlite_session() as db:
        # Create admin user
        admin = User(
            user_id=uuid.uuid4(),
            username="admin",
            email="admin@tigerid.local",
            password_hash=hash_password("admin"),
            role=UserRole.admin,
            permissions={
                "investigations": ["create", "read", "update", "delete"],
                "tigers": ["create", "read", "update", "delete"],
                "facilities": ["create", "read", "update", "delete"],
                "users": ["create", "read", "update", "delete"],
            },
            is_active=True,
            mfa_enabled=False,
            last_login=datetime.utcnow()
        )
        db.add(admin)
        db.flush()
        
        # Create demo investigator
        investigator = User(
            user_id=uuid.uuid4(),
            username="investigator",
            email="investigator@tigerid.local",
            password_hash=hash_password("demo"),
            role=UserRole.investigator,
            permissions={
                "investigations": ["create", "read", "update"],
                "tigers": ["read"],
                "facilities": ["read"],
            },
            is_active=True,
            mfa_enabled=False
        )
        db.add(investigator)
        db.flush()
        
        # Create demo facilities
        facilities = []
        for i, name in enumerate(["Big Cat Rescue", "Tiger Haven", "Wildlife Sanctuary"], 1):
            facility = Facility(
                facility_id=uuid.uuid4(),
                exhibitor_name=name,
                usda_license=f"58-C-{1000+i}",
                state="FL" if i == 1 else "TX",
                city="Tampa" if i == 1 else "Dallas",
                address=f"{i*100} Wildlife Way",
                tiger_count=5 + i,
                tiger_capacity=20,
                social_media_links={
                    "facebook": f"https://facebook.com/{name.lower().replace(' ', '')}",
                    "instagram": f"@{name.lower().replace(' ', '_')}"
                },
                website=f"https://{name.lower().replace(' ', '')}.org",
                last_inspection_date=datetime.utcnow() - timedelta(days=30*i),
                accreditation_status="Accredited" if i <= 2 else "Pending",
                created_at=datetime.utcnow() - timedelta(days=365*i)
            )
            facilities.append(facility)
            db.add(facility)
        
        db.flush()
        
        # Create demo tigers
        tigers = []
        for i, name in enumerate(["Rajah", "Shere Khan", "Tigger"], 1):
            tiger = Tiger(
                tiger_id=uuid.uuid4(),
                name=name,
                origin_facility_id=facilities[i-1].facility_id,
                last_seen_location=facilities[i-1].city,
                last_seen_date=datetime.utcnow() - timedelta(days=i),
                status=TigerStatus.active,
                tags=["demo", f"facility-{i}"],
                created_at=datetime.utcnow() - timedelta(days=365*i)
            )
            tigers.append(tiger)
            db.add(tiger)
        
        db.flush()
        
        # Create demo investigations with realistic workflow data
        investigations = []
        
        # Investigation 1: Active trafficking ring case
        inv1 = Investigation(
            investigation_id=uuid.uuid4(),
            title="Investigation #1 - Interstate Trafficking Ring",
            description="Investigating suspected tiger trafficking network across TX and FL facilities. Multiple social media posts suggest illegal transport and sale.",
            status=InvestigationStatus.active,
            priority=Priority.high,
            created_by=admin.user_id,
            tags=["trafficking", "multi-state", "social-media"],
            created_at=datetime.utcnow() - timedelta(days=10),
            updated_at=datetime.utcnow() - timedelta(hours=2),
            started_at=datetime.utcnow() - timedelta(days=9)
        )
        db.add(inv1)
        db.flush()
        investigations.append(inv1)
        
        # Add investigation steps for inv1 (showing agent workflow)
        steps_data = [
            {
                "step_type": "research",
                "agent_name": "research",
                "status": "completed",
                "result": {
                    "evidence_count": 5,
                    "sources": ["Facebook", "Instagram", "USDA Database"],
                    "keywords": ["tiger", "cub", "sale", "transport"]
                },
                "duration_ms": 12500,
                "timestamp": datetime.utcnow() - timedelta(days=9)
            },
            {
                "step_type": "analysis",
                "agent_name": "analysis",
                "status": "completed",
                "result": {
                    "risk_score": 0.87,
                    "entities_identified": ["Big Cat Rescue", "Tiger Haven"],
                    "connections_found": 3
                },
                "duration_ms": 8300,
                "timestamp": datetime.utcnow() - timedelta(days=9, hours=-2)
            },
            {
                "step_type": "validation",
                "agent_name": "validation",
                "status": "in_progress",
                "result": {
                    "verified_evidence": 3,
                    "pending_verification": 2,
                    "confidence": 0.82
                },
                "duration_ms": None,
                "timestamp": datetime.utcnow() - timedelta(hours=3)
            }
        ]
        
        for step_data in steps_data:
            step = InvestigationStep(
                step_id=uuid.uuid4(),
                investigation_id=inv1.investigation_id,
                **step_data
            )
            db.add(step)
        
        # Add evidence for inv1
        evidence_items = [
            {
                "source_type": EvidenceSourceType.web_search,
                "source_url": "https://facebook.com/bigcatrescue/posts/123456",
                "content": {"text": "Check out our new tiger cubs! Available for educational visits.", "platform": "Facebook"},
                "extracted_text": "New tiger cubs announced on social media",
                "relevance_score": 0.92,
                "created_at": datetime.utcnow() - timedelta(days=9, hours=-1)
            },
            {
                "source_type": EvidenceSourceType.image,
                "source_url": "https://instagram.com/tigerhaven/photo1.jpg",
                "content": {"description": "Photo of juvenile tiger in transport crate", "detected_tigers": 1},
                "extracted_text": "Tiger in transport crate, estimated age 6 months",
                "relevance_score": 0.88,
                "created_at": datetime.utcnow() - timedelta(days=8)
            },
            {
                "source_type": EvidenceSourceType.document,
                "source_url": "USDA License Check",
                "content": {"license": "58-C-1001", "status": "expired", "violations": 2},
                "extracted_text": "USDA license expired 3 months ago, 2 violations on record",
                "relevance_score": 0.95,
                "created_at": datetime.utcnow() - timedelta(days=8, hours=-3)
            },
            {
                "source_type": EvidenceSourceType.web_search,
                "source_url": "https://youtube.com/watch?v=abc123",
                "content": {"title": "Baby Tiger Playing", "views": 50000, "uploaded": "2024-10-15"},
                "extracted_text": "Video showing juvenile tiger, uploaded 2 weeks ago",
                "relevance_score": 0.76,
                "created_at": datetime.utcnow() - timedelta(days=7)
            },
            {
                "source_type": EvidenceSourceType.user_input,
                "source_url": None,
                "content": {"note": "Anonymous tip about illegal tiger sale, caller mentioned TX facility"},
                "extracted_text": "Anonymous tip received regarding TX facility tiger sales",
                "relevance_score": 0.85,
                "created_at": datetime.utcnow() - timedelta(days=10)
            }
        ]
        
        for ev_data in evidence_items:
            evidence = Evidence(
                evidence_id=uuid.uuid4(),
                investigation_id=inv1.investigation_id,
                **ev_data
            )
            db.add(evidence)
        
        # Investigation 2: Completed case
        inv2 = Investigation(
            investigation_id=uuid.uuid4(),
            title="Investigation #2 - Illegal Transport (Closed)",
            description="Successfully identified and stopped illegal tiger transport between states. Case closed with cooperation from authorities.",
            status=InvestigationStatus.completed,
            priority=Priority.medium,
            created_by=admin.user_id,
            tags=["transport", "completed", "successful"],
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow() - timedelta(days=5),
            started_at=datetime.utcnow() - timedelta(days=29),
            completed_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add(inv2)
        db.flush()
        investigations.append(inv2)
        
        # Add completed workflow steps for inv2
        for agent_name in ["research", "analysis", "validation", "reporting"]:
            step = InvestigationStep(
                step_id=uuid.uuid4(),
                investigation_id=inv2.investigation_id,
                step_type=agent_name,
                agent_name=agent_name,
                status="completed",
                result={"status": "success", "findings": f"{agent_name.title()} phase completed successfully"},
                duration_ms=10000 + (hash(agent_name) % 5000),
                timestamp=datetime.utcnow() - timedelta(days=25 - (["research", "analysis", "validation", "reporting"].index(agent_name) * 3))
            )
            db.add(step)
        
        # Investigation 3: Draft
        inv3 = Investigation(
            investigation_id=uuid.uuid4(),
            title="Investigation #3 - Social Media Sale Lead",
            description="Initial lead from social media monitoring. Requires further investigation to determine validity.",
            status=InvestigationStatus.draft,
            priority=Priority.low,
            created_by=investigator.user_id,
            tags=["social-media", "lead", "pending-review"],
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(inv3)
        investigations.append(inv3)
        
        db.commit()
        
        # Enrich with facility data from non-accredited facilities dataset
        print("\n→ Enriching with facility data from datasets...")
        try:
            enrich_facilities_from_dataset(db, create_tigers=True)
        except Exception as e:
            print(f"WARNING: Facility enrichment skipped: {e}")
        
        # Load tiger images from ATRW dataset
        print("\n→ Loading tiger images from ATRW dataset...")
        try:
            load_atrw_images(db)
        except Exception as e:
            print(f"WARNING: ATRW image loading skipped: {e}")
        
        # Refresh counts after enrichment and image loading
        enriched_facility_count = db.query(Facility).count()
        enriched_tiger_count = db.query(Tiger).count()
        image_count = db.query(TigerImage).count()
        
        print("[OK] Demo data created:")
        print("   Users: admin/admin, investigator/demo")
        print(f"   Facilities: {enriched_facility_count} (including enriched dataset)")
        print(f"   Tigers: {enriched_tiger_count} (including enriched dataset)")
        print(f"   Investigations: {len(investigations)}")
        print("   Investigation Steps: 7 (showing agent workflow)")
        print("   Evidence Items: 5 (various sources)")
        print(f"   Tiger Images: {image_count} (from ATRW dataset)")


def enrich_facilities_from_dataset(db_session, create_tigers: bool = True):
    """Enrich database with facilities from non-accredited facilities dataset"""
    from pathlib import Path
    from setup.scripts.enrich_facilities import (
        parse_facility_file,
        enrich_facilities
    )
    
    # Find facility data file
    facility_file = Path(__file__).parent.parent.parent / "data" / "datasets" / "non-accredited-facilities"
    
    if not facility_file.exists():
        print(f"WARNING: Facility dataset not found: {facility_file}")
        return
    
    # Parse facility data
    facilities_data = parse_facility_file(facility_file)
    
    if not facilities_data:
        print("WARNING: No facility data found in dataset")
        return
    
    # Enrich facilities (using existing session)
    print(f"   → Processing {len(facilities_data)} facilities from dataset...")
    stats = enrich_facilities(facilities_data, create_tigers=create_tigers, dry_run=False, db_session=db_session)
    
    print(f"   [OK] Enriched: {stats['facilities_created']} created, {stats['facilities_updated']} updated")
    if create_tigers:
        print(f"   [OK] Created {stats['tigers_created']} tigers from facility data")


def load_atrw_images(db_session):
    """Load tiger images from ATRW dataset"""
    from pathlib import Path
    from uuid import uuid4
    from datetime import datetime
    from backend.database.models import TigerStatus
    
    project_root = Path(__file__).parent.parent.parent
    atrw_images_dir = project_root / "data" / "models" / "atrw" / "images"
    
    if not atrw_images_dir.exists():
        print(f"WARNING: ATRW images directory not found: {atrw_images_dir}")
        return
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    # Find all tiger directories
    tiger_dirs = [d for d in atrw_images_dir.iterdir() if d.is_dir()]
    
    if not tiger_dirs:
        print(f"WARNING: No tiger directories found in {atrw_images_dir}")
        return
    
    images_loaded = 0
    tigers_with_images = 0
    
    for tiger_dir in tiger_dirs[:10]:  # Limit to first 10 tigers for demo
        tiger_id_str = tiger_dir.name
        
        # Find existing tiger or skip
        tiger = db_session.query(Tiger).filter(Tiger.alias == tiger_id_str).first()
        if not tiger:
            # Create tiger if it doesn't exist
            tiger = Tiger(
                tiger_id=uuid4(),
                name=f"ATRW Tiger {tiger_id_str}",
                alias=tiger_id_str,
                status=TigerStatus.active,
                created_at=datetime.utcnow()
            )
            db_session.add(tiger)
            db_session.flush()
            tigers_with_images += 1
        
        # Find image files
        image_files = [
            f for f in tiger_dir.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ][:3]  # Limit to 3 images per tiger for demo
        
        for image_file in image_files:
            # Check if image already exists
            existing = db_session.query(TigerImage).filter(
                TigerImage.image_path == str(image_file)
            ).first()
            
            if existing:
                continue
            
            # Create TigerImage record
            tiger_image = TigerImage(
                image_id=uuid4(),
                tiger_id=tiger.tiger_id,
                image_path=str(image_file),
                meta_data={
                    'dataset': 'ATRW',
                    'tiger_id_dataset': tiger_id_str,
                    'source_path': str(image_file.relative_to(atrw_images_dir))
                },
                verified=False,
                created_at=datetime.utcnow()
            )
            db_session.add(tiger_image)
            images_loaded += 1
    
    db_session.commit()
    print(f"   [OK] Loaded {images_loaded} images for {tigers_with_images} tigers from ATRW dataset")


if __name__ == "__main__":
    print("\nInitializing SQLite Demo Database...\n")
    init_sqlite_db()
    create_demo_data()
    print("\n[OK] SQLite demo database ready!")
    print(f"   Database file: {DB_PATH.absolute()}\n")

