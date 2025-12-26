#!/usr/bin/env python3
"""
Quick fix: Disable adaptive policy in main.py
Use this when the agent gets stuck
"""

def disable_adaptive_policy():
    """
    Quick script to disable adaptive policy in GroqIntelligence
    """
    
    file_path = "intelligence/groq_intelligence.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Look for adaptive policy initialization
        if "adaptive_policy_enabled = True" in content:
            # Replace with False
            content = content.replace("adaptive_policy_enabled = True", "adaptive_policy_enabled = False")
            print("✅ Found and disabled adaptive policy")
        elif "self.adaptive_policy_enabled = True" in content:
            content = content.replace("self.adaptive_policy_enabled = True", "self.adaptive_policy_enabled = False")
            print("✅ Found and disabled adaptive policy")
        else:
            print("❌ Adaptive policy setting not found in expected format")
            return False
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(content)
            
        print("✅ Adaptive policy disabled successfully!")
        print("🔄 Now restart the agent: python main.py questions/python_programming_questions.md")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚨 Emergency Fix: Disabling Adaptive Policy")
    print("=" * 40)
    print("This will make the agent respond faster by bypassing complex processing")
    print()
    
    success = disable_adaptive_policy()
    
    if success:
        print()
        print("🎯 NEXT STEPS:")
        print("1. Restart the agent with: python main.py questions/python_programming_questions.md")
        print("2. The agent should now respond much faster")
        print("3. If you want to re-enable adaptive policy later, change False back to True")
    else:
        print()
        print("🔧 MANUAL FIX:")
        print("1. Open intelligence/groq_intelligence.py")
        print("2. Find 'adaptive_policy_enabled = True'") 
        print("3. Change it to 'adaptive_policy_enabled = False'")
        print("4. Save and restart the agent")
