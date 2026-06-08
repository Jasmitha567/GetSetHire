# test_groq.py
from ai_service import ai_service

result = ai_service.generate_personalized_roadmap(
    missing_skills=["Docker", "Kubernetes"],
    target_role="DevOps Engineer",
    preparation_days=30,
    weekly_hours=10
)

if result:
    print("✅ Groq API called successfully!")
else:
    print("❌ Groq API failed")