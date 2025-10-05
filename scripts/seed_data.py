#!/usr/bin/env python3
"""Seed data script for development environment.

Creates sample users with different experience levels and rate calculations.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User, UserProfile
from app.models.rate_calculation import RateCalculation
from app.services.user_service import UserService
from app.schemas.auth import UserRegisterRequest
from app.core.security import hash_password


def create_sample_users():
    """Create sample users with different experience levels."""
    
    sample_users = [
        {
            "email": "junior@example.com",
            "password": "password123",
            "first_name": "Ahmed",
            "last_name": "Ali",
            "profession": "Web Developer",
            "experience_years": 1,
            "skills": '["HTML", "CSS", "JavaScript", "React"]',
            "city": "Cairo",
            "hourly_rate_preference": 150
        },
        {
            "email": "midlevel@example.com", 
            "password": "password123",
            "first_name": "Sara",
            "last_name": "Hassan",
            "profession": "Full Stack Developer",
            "experience_years": 4,
            "skills": '["React", "Node.js", "Python", "PostgreSQL", "AWS"]',
            "city": "Alexandria",
            "hourly_rate_preference": 300
        },
        {
            "email": "senior@example.com",
            "password": "password123", 
            "first_name": "Mohamed",
            "last_name": "Ibrahim",
            "profession": "Senior Software Engineer",
            "experience_years": 8,
            "skills": '["Python", "Django", "FastAPI", "Docker", "Kubernetes", "Microservices", "System Design"]',
            "city": "Giza",
            "hourly_rate_preference": 500
        }
    ]
    
    db = SessionLocal()
    user_service = UserService(db)
    created_users = []
    
    try:
        for user_data in sample_users:
            # Check if user already exists
            existing_user = user_service.get_user_by_email(user_data["email"])
            if existing_user:
                print(f"User {user_data['email']} already exists, skipping...")
                created_users.append(existing_user)
                continue
            
            # Create user
            register_data = UserRegisterRequest(
                email=user_data["email"],
                password=user_data["password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"]
            )
            
            user = user_service.create_user(register_data)
            
            # Update profile with additional data
            profile_update = {
                "profession": user_data["profession"],
                "experience_years": user_data["experience_years"],
                "skills": user_data["skills"],
                "city": user_data["city"],
                "hourly_rate_preference": user_data["hourly_rate_preference"]
            }
            
            from app.schemas.auth import UserProfileUpdateRequest
            profile_request = UserProfileUpdateRequest(**profile_update)
            user_service.update_user_profile(user.id, profile_request)
            
            created_users.append(user)
            print(f"✅ Created user: {user_data['email']}")
        
        db.commit()
        return created_users
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating users: {e}")
        raise
    finally:
        db.close()


def create_sample_rate_calculations(users):
    """Create sample rate calculations for users."""
    
    sample_calculations = [
        {
            "user_email": "junior@example.com",
            "project_type": "web_development",
            "project_complexity": "simple",
            "estimated_hours": 20,
            "experience_years": 1,
            "skills_count": 4,
            "location": "Cairo, Egypt",
            "client_region": "egypt",
            "urgency": "normal"
        },
        {
            "user_email": "junior@example.com", 
            "project_type": "web_development",
            "project_complexity": "moderate",
            "estimated_hours": 40,
            "experience_years": 1,
            "skills_count": 4,
            "location": "Cairo, Egypt",
            "client_region": "mena",
            "urgency": "normal"
        },
        {
            "user_email": "midlevel@example.com",
            "project_type": "web_development", 
            "project_complexity": "moderate",
            "estimated_hours": 60,
            "experience_years": 4,
            "skills_count": 5,
            "location": "Alexandria, Egypt",
            "client_region": "europe",
            "urgency": "normal"
        },
        {
            "user_email": "midlevel@example.com",
            "project_type": "mobile_development",
            "project_complexity": "complex", 
            "estimated_hours": 80,
            "experience_years": 4,
            "skills_count": 5,
            "location": "Alexandria, Egypt",
            "client_region": "usa",
            "urgency": "rush"
        },
        {
            "user_email": "senior@example.com",
            "project_type": "consulting",
            "project_complexity": "enterprise",
            "estimated_hours": 100,
            "experience_years": 8,
            "skills_count": 7,
            "location": "Giza, Egypt", 
            "client_region": "global",
            "urgency": "normal"
        },
        {
            "user_email": "senior@example.com",
            "project_type": "data_analysis",
            "project_complexity": "complex",
            "estimated_hours": 50,
            "experience_years": 8,
            "skills_count": 7,
            "location": "Giza, Egypt",
            "client_region": "usa",
            "urgency": "normal"
        }
    ]
    
    db = SessionLocal()
    
    try:
        # Create email to user mapping
        email_to_user = {user.email: user for user in users}
        
        for calc_data in sample_calculations:
            user = email_to_user.get(calc_data["user_email"])
            if not user:
                print(f"⚠️  User {calc_data['user_email']} not found, skipping calculation...")
                continue
            
            # Calculate rates using the service
            from app.schemas.rates import RateRequest
            from app.services.rates import calculate_compensation_tiers
            
            rate_request = RateRequest(
                project_type=calc_data["project_type"],
                project_complexity=calc_data["project_complexity"],
                estimated_hours=calc_data["estimated_hours"],
                experience_years=calc_data["experience_years"],
                skills_count=calc_data["skills_count"],
                location=calc_data["location"],
                client_region=calc_data["client_region"],
                urgency=calc_data["urgency"]
            )
            
            # Calculate rates
            tiers = calculate_compensation_tiers(rate_request, db=db, user_id=user.id)
            
            print(f"✅ Created rate calculation for {calc_data['user_email']}: "
                  f"Competitive rate: {tiers['competitive_rate']} EGP/hour")
        
        db.commit()
        print(f"✅ Created {len(sample_calculations)} rate calculations")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating rate calculations: {e}")
        raise
    finally:
        db.close()


def print_credentials(users):
    """Print login credentials for created users."""
    print("\n" + "="*60)
    print("🔑 LOGIN CREDENTIALS")
    print("="*60)
    
    for user in users:
        print(f"Email: {user.email}")
        print(f"Password: password123")
        print(f"Name: {user.profile.first_name if user.profile else 'N/A'} {user.profile.last_name if user.profile else 'N/A'}")
        print("-" * 40)
    
    print("\n💡 You can use these credentials to test the authentication system!")
    print("="*60)


def main():
    """Main seed data function."""
    print("🌱 Starting seed data creation...")
    
    # Check if we're in development mode
    if os.getenv("ENVIRONMENT", "development") != "development":
        print("❌ Seed data should only be run in development environment!")
        sys.exit(1)
    
    try:
        # Create sample users
        print("\n👥 Creating sample users...")
        users = create_sample_users()
        
        # Create sample rate calculations
        print("\n📊 Creating sample rate calculations...")
        create_sample_rate_calculations(users)
        
        # Print credentials
        print_credentials(users)
        
        print("\n✅ Seed data creation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Seed data creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
