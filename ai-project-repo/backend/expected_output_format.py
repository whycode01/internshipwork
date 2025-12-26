"""
Expected Output Format for Technical Interview Assessment Report

When you select "Template 1" and generate questions, you should get questions like these:
"""

EXPECTED_QUESTIONS = [
    {
        "question_text": "Can you walk me through your approach to writing clean, maintainable code? Please provide a specific example where you refactored code to improve its quality and explain the metrics you used to measure improvement.",
        "question_type": "Technical Competency",
        "assessment_area": "Programming Skills - Code Quality",
        "scoring_guidance": "Look for specific examples, understanding of clean code principles, and measurable quality improvements (1-5 scale)"
    },
    {
        "question_text": "Describe a system architecture you've designed or worked on. How did you ensure it could scale to handle increased load, and what trade-offs did you consider in your design decisions?",
        "question_type": "Technical Competency", 
        "assessment_area": "System Design - Architecture Understanding & Scalability",
        "scoring_guidance": "Evaluate understanding of scalability patterns, architectural principles, and decision-making process (1-5 scale)"
    },
    {
        "question_text": "How do you handle sensitive customer data in your applications? Can you describe specific measures you've implemented to ensure data privacy and security compliance?",
        "question_type": "Policy Compliance",
        "assessment_area": "Data Privacy Awareness",
        "scoring_guidance": "Assess knowledge of data protection principles and practical implementation (Pass/Fail/Needs Improvement)"
    },
    {
        "question_text": "Tell me about a time when you had to explain a complex technical concept to a non-technical team member or stakeholder. How did you ensure they understood the implications and requirements?",
        "question_type": "Behavioral Assessment",
        "assessment_area": "Communication Skills", 
        "scoring_guidance": "Look for clarity, empathy, and effectiveness in technical communication (1-5 scale)"
    },
    {
        "question_text": "Imagine you discover a critical security vulnerability in production code just before a major release deadline. The fix would require significant changes that might delay the release. How would you handle this situation?",
        "question_type": "Situational Assessment",
        "assessment_area": "Security Best Practices & Problem-Solving Approach",
        "scoring_guidance": "Evaluate decision-making process, security prioritization, and stakeholder communication"
    }
]

def print_expected_format():
    print("=== EXPECTED QUESTION FORMAT FOR TECHNICAL INTERVIEW ASSESSMENT REPORT ===\n")
    
    print("Your questions should be structured to match the assessment areas in your template:\n")
    
    print("1. TECHNICAL COMPETENCY ASSESSMENT questions should target:")
    print("   - Programming Skills (Code Quality, Problem Solving, Algorithm Knowledge)")
    print("   - System Design (Architecture, Scalability, Database Design, Security)")
    print("   - Technology Stack Knowledge (Frontend, Backend, Database, DevOps)")
    
    print("\n2. POLICY COMPLIANCE EVALUATION questions should test:")
    print("   - Data Privacy Awareness")
    print("   - Security Best Practices") 
    print("   - Code Quality Standards")
    print("   - Documentation Practices")
    
    print("\n3. BEHAVIORAL ASSESSMENT questions should evaluate:")
    print("   - Communication Skills")
    print("   - Team Collaboration")
    print("   - Problem-Solving Approach")
    print("   - Learning Agility")
    
    print("\n4. Each question should include:")
    print("   - question_text: The actual interview question")
    print("   - question_type: Technical Competency | Policy Compliance | Behavioral Assessment | Situational Assessment")
    print("   - assessment_area: Specific area from your template")
    print("   - scoring_guidance: How to evaluate the answer (1-5 scale or Pass/Fail)")
    
    print("\n" + "="*80)
    print("SAMPLE EXPECTED QUESTIONS:")
    print("="*80)
    
    for i, question in enumerate(EXPECTED_QUESTIONS, 1):
        print(f"\nQuestion {i}:")
        print(f"Text: {question['question_text']}")
        print(f"Type: {question['question_type']}")
        print(f"Assessment Area: {question['assessment_area']}")
        print(f"Scoring: {question['scoring_guidance']}")
        print("-" * 60)
    
    print("\nIf your generated questions don't match this format, the template-specific prompt needs debugging.")

if __name__ == "__main__":
    print_expected_format()
