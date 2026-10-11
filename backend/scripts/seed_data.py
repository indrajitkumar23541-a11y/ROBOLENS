import sys
import os
import uuid
from datetime import datetime, timezone

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole, Organization, OrganizationMember
from app.models.task import Task, TaskStatus
from app.models.dataset import Dataset, DatasetVersion, DatasetVersionStatus


def seed_database():
    print("Connecting to database and creating tables if not present...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ---------------------------------------------------------------------
        # 1. Seed Users & Organizations
        # ---------------------------------------------------------------------
        print("\n--- Seeding Users ---")
        users_data = [
            {
                "email": "admin@robolens.ai",
                "full_name": "ROBOLENS Platform Admin",
                "role": UserRole.ADMIN,
                "password": "AdminPassword123!"
            },
            {
                "email": "reviewer@robolens.ai",
                "full_name": "Lead Quality Reviewer",
                "role": UserRole.REVIEWER,
                "password": "ReviewerPassword123!"
            },
            {
                "email": "contributor@robolens.ai",
                "full_name": "Demo Contributor",
                "role": UserRole.CONTRIBUTOR,
                "password": "ContributorPassword123!"
            },
            {
                "email": "researcher@physical-ai.org",
                "full_name": "Robotics Research Partner",
                "role": UserRole.ENTERPRISE,
                "password": "EnterprisePassword123!"
            }
        ]

        created_users = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    is_active=True
                )
                db.add(user)
                db.flush()
                created_users[u["email"]] = user
                print(f"Created user: {u['email']} [{u['role']}]")
            else:
                created_users[u["email"]] = existing
                print(f"User already exists: {u['email']}")

        # Seed Organization
        org = db.query(Organization).filter(Organization.slug == "physical-ai-lab").first()
        if not org:
            org = Organization(
                name="Physical AI Robotics Laboratory",
                slug="physical-ai-lab"
            )
            db.add(org)
            db.flush()
            member = OrganizationMember(
                organization_id=org.id,
                user_id=created_users["researcher@physical-ai.org"].id,
                role="LEAD_RESEARCHER"
            )
            db.add(member)
            print(f"Created organization: {org.name}")

        # ---------------------------------------------------------------------
        # 2. Seed Robotics Tasks
        # ---------------------------------------------------------------------
        print("\n--- Seeding Robotics Manipulation Tasks ---")
        tasks_data = [
            {
                "id": "task_cup_manipulation_v1",
                "title": "Tabletop Cup Pick & Place",
                "category": "tabletop_manipulation",
                "expected_duration_min": 8,
                "expected_duration_max": 35,
                "reward_amount": 150.0,
                "description": "Pick a standard ceramic or plastic coffee cup from a tabletop, rotate it 90 degrees, and place it gently inside a marked tray.",
                "instructions_md": """## Objective
Demonstrate human hand grasp and placement dynamics for training tabletop manipulation policies.

### Environment & Objects
- A solid, well-lit table with minimal clutter.
- One standard coffee mug or cup with handle.
- A marked tray or contrasting target placemat.

### Step-by-Step Execution
1. **Frame View:** Position smartphone camera 30-45° angled from above, ensuring hand and cup are clearly in frame.
2. **Resting Pose:** Start with hand resting next to the table for 1 second.
3. **Approach & Grasp:** Reach toward the cup smoothly, grasping firmly by the handle or cylinder body.
4. **Lift & Transport:** Lift the cup approximately 10-15 cm off the table and move horizontally toward the target tray.
5. **Placement:** Lower the cup gently into the tray without bouncing or dropping.
6. **Retract:** Release fingers and retract hand back to resting position.

### Rejection Criteria
- Cup out of frame during grasp or release.
- Camera shaking excessively or obstructed viewpoint.
- Video duration shorter than 8 seconds.
"""
            },
            {
                "id": "task_drawer_storage_v1",
                "title": "Cabinet Drawer Pull & Storage",
                "category": "household_manipulation",
                "expected_duration_min": 10,
                "expected_duration_max": 45,
                "reward_amount": 200.0,
                "description": "Grasp a kitchen or office drawer handle, pull open smoothly, place a small household item inside, and close the drawer.",
                "instructions_md": """## Objective
Capture articulated mechanism interaction (prismatic joint dynamics) and object insertion.

### Requirements
- A functional drawer (kitchen, desk, or dresser).
- A small target object (e.g. wooden block, stapler, or TV remote).

### Instructions
1. Stand or position camera so the entire drawer face and handle are visible.
2. Reach forward and grasp handle. Pull drawer out approximately 20-30 cm.
3. With other hand or sequentially, place the object into the drawer interior.
4. Push drawer completely shut until closed.
"""
            },
            {
                "id": "task_peg_alignment_v1",
                "title": "Peg-in-Hole Precision Alignment",
                "category": "precision_assembly",
                "expected_duration_min": 12,
                "expected_duration_max": 60,
                "reward_amount": 280.0,
                "description": "Pick up a cylindrical or square peg and insert it vertically into a matching hole receptacle with controlled precision.",
                "instructions_md": """## Objective
Train high-precision contact insertion and tactile alignment demonstrations.

### Setup
- Peg and matching receptacle (e.g. kids shape sorter, machined peg block, or marker into holder).
- Camera focused tightly on insertion zone (macro / close-up framing).

### Recording Tips
- Avoid blocking the hole with palm or wrist.
- Align peg axis perpendicular to receptacle surface before inserting.
"""
            },
            {
                "id": "task_tool_handover_v1",
                "title": "Tool Handover Demonstration",
                "category": "human_robot_collaboration",
                "expected_duration_min": 10,
                "expected_duration_max": 40,
                "reward_amount": 250.0,
                "description": "Pick up a screwdriver, wrench, or pliers by the handle and present the tool safely oriented for collaborative handover.",
                "instructions_md": """## Objective
Capture safe human tool presentation for collaborative robots.

### Guidelines
- Always present tool with working tip facing away from the receiver.
- Grip tool handle leaving the top half exposed for gripper acquisition.
"""
            },
            {
                "id": "task_cable_insertion_v1",
                "title": "USB Cable Route & Insertion",
                "category": "deformable_object_manipulation",
                "expected_duration_min": 15,
                "expected_duration_max": 75,
                "reward_amount": 320.0,
                "description": "Grasp a flexible USB or power cable near connector head, route around obstacle, and insert into device port.",
                "instructions_md": """## Objective
Train deformable linear object (DLO) routing and insertion models.

### Guidelines
- Grip cable within 3-5 cm of plug connector.
- Align plug orientation correctly with port before inserting.
"""
            }
        ]

        for t in tasks_data:
            existing = db.query(Task).filter(Task.id == t["id"]).first()
            if not existing:
                task = Task(
                    id=t["id"],
                    title=t["title"],
                    category=t["category"],
                    description=t["description"],
                    instructions_md=t["instructions_md"],
                    expected_duration_min=t["expected_duration_min"],
                    expected_duration_max=t["expected_duration_max"],
                    reward_amount=t["reward_amount"],
                    status=TaskStatus.ACTIVE,
                    version=1,
                    max_submissions=1000
                )
                db.add(task)
                print(f"Created task: {t['title']} [{t['category']}]")
            else:
                print(f"Task already exists: {t['title']}")

        # ---------------------------------------------------------------------
        # 3. Seed Dataset
        # ---------------------------------------------------------------------
        print("\n--- Seeding Datasets ---")
        dataset_slug = "robolens-manipulation-benchmark-v1"
        ds = db.query(Dataset).filter(Dataset.slug == dataset_slug).first()
        if not ds:
            ds = Dataset(
                name="RoboLens Tabletop Manipulation Benchmark v1",
                slug=dataset_slug,
                description="High-fidelity human demonstration episodes for tabletop robotic arm policy training (compatible with LeRobot & RLDS).",
                license="CC-BY-NC-SA-4.0"
            )
            db.add(ds)
            db.flush()

            version = DatasetVersion(
                dataset_id=ds.id,
                version_tag="v1.0.0",
                status=DatasetVersionStatus.PUBLISHED,
                manifest_s3_key=f"datasets/{dataset_slug}/v1.0.0/manifest.json",
                total_episodes=0
            )
            db.add(version)
            print(f"Created dataset: {ds.name} [{version.version_tag}]")
        else:
            print(f"Dataset already exists: {ds.name}")

        db.commit()
        print("\n Seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
