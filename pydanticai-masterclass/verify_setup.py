#!/usr/bin/env python3
"""Verification script to check PydanticAI Masterclass setup.

Run this script to verify:
- Dependencies are installed
- API keys are configured via Pydantic Settings
- Logfire is set up
- Mock database works
"""

import asyncio
import sys


async def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    try:
        import pydantic_ai
        print(f"  ✓ pydantic-ai: {pydantic_ai.__version__}")
    except ImportError:
        print("  ✗ pydantic-ai not installed")
        print("    Run: uv add pydantic-ai")
        return False
    
    try:
        import logfire
        print(f"  ✓ logfire: installed")
    except ImportError:
        print("  ✗ logfire not installed")
        print("    Run: uv add 'pydantic-ai[logfire]'")
        return False
    
    try:
        import pydantic_settings
        print(f"  ✓ pydantic-settings: installed")
    except ImportError:
        print("  ✗ pydantic-settings not installed")
        print("    Run: uv add pydantic-settings")
        return False
    
    return True


def check_environment():
    """Check if environment variables are set via Pydantic Settings."""
    print("\n🔑 Checking environment variables (via Pydantic Settings)...")
    
    try:
        from common.settings import settings
        
        # Try to access the API key - this will raise an error if not set
        api_key = settings.openai_api_key
        
        if api_key and not api_key.startswith("sk-proj-your"):
            print(f"  ✓ OPENAI_API_KEY: configured (starts with {api_key[:15]}...)")
            return True
        else:
            print("  ✗ OPENAI_API_KEY: using example value")
            print("    Create .env file with: OPENAI_API_KEY=sk-proj-your-actual-key")
            return False
            
    except Exception as e:
        print(f"  ✗ Settings error: {e}")
        print("    Create .env file with: OPENAI_API_KEY=sk-proj-your-actual-key")
        return False


def check_logfire():
    """Check if Logfire is configured."""
    print("\n📊 Checking Logfire configuration...")
    
    from pathlib import Path
    
    logfire_dir = Path(".logfire")
    if logfire_dir.exists():
        print(f"  ✓ .logfire/ directory exists")
        return True
    else:
        print("  ⚠ .logfire/ directory not found")
        print("    Run: uv run logfire auth")
        print("    Then: uv run logfire projects use")
        return False


async def check_mock_database():
    """Check if mock database works."""
    print("\n🗄️  Checking mock database...")
    
    try:
        from common.database import mock_db
        
        # Test database operations
        user = await mock_db.get_user(1)
        assert user is not None, "Failed to get user"
        print(f"  ✓ Mock database works (loaded {len(mock_db.users)} users)")
        
        products = await mock_db.list_products()
        print(f"  ✓ Products loaded ({len(products)} products)")
        
        return True
    except Exception as e:
        print(f"  ✗ Mock database error: {e}")
        return False


async def test_simple_agent():
    """Test a simple agent execution."""
    print("\n🤖 Testing simple agent...")
    
    try:
        import os
        
        import logfire
        from pydantic_ai import Agent
        
        from common.settings import settings
        
        # Set API key from settings
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        
        # Configure logfire quietly
        logfire.configure(console=False)
        logfire.instrument_pydantic_ai()
        
        # Create simple agent
        agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt="You are a test assistant. Respond with exactly: 'Test successful!'",
        )
        
        # Run test
        result = await agent.run("Please confirm the test is working.")
        
        print(f"  ✓ Agent executed successfully")
        print(f"  ✓ Response: {result.output[:50]}...")
        
        return True
    except Exception as e:
        print(f"  ✗ Agent test failed: {e}")
        return False


async def main():
    """Run all checks."""
    print("=" * 60)
    print("PydanticAI Masterclass - Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Check dependencies
    results.append(await check_dependencies())
    
    # Check environment
    results.append(check_environment())
    
    # Check Logfire (warning only)
    logfire_ok = check_logfire()
    
    # Check mock database
    results.append(await check_mock_database())
    
    # Test agent if everything else works
    if all(results):
        results.append(await test_simple_agent())
    else:
        print("\n⚠️  Skipping agent test due to setup issues")
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All checks passed! You're ready to start learning.")
        print("\nNext steps:")
        print("  1. Start with: lessons/01_foundations/00_basics/")
        print("  2. Run: uv run lessons/01_foundations/00_basics/01_simple_agent.py")
        if not logfire_ok:
            print("  3. Optional: Set up Logfire for observability")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
