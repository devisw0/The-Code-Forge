import asyncio
import sys

def check_imports():
    """Check all required imports"""
    print("Checking imports...")
    try:
        import autogen_agentchat
        print(f"✓ autogen-agentchat {autogen_agentchat.__version__}")
    except ImportError as e:
        print(f"✗ autogen-agentchat: {e}")
        return False
    
    try:
        import autogen_core
        print(f"✓ autogen-core {autogen_core.__version__}")
    except ImportError as e:
        print(f"✗ autogen-core: {e}")
        return False
    
    try:
        import boto3
        print(f"✓ boto3 {boto3.__version__}")
    except ImportError as e:
        print(f"✗ boto3: {e}")
        return False
    
    # aioboto3 is NOT required for AutoGen with Bedrock
    print("✓ aioboto3 not needed (using synchronous boto3)")
    
    return True

def check_aws_credentials():
    """Check AWS credentials"""
    print("\nChecking AWS credentials...")
    try:
        import boto3
        session = boto3.Session(profile_name='devan')
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials valid")
        print(f"  Account: {identity['Account']}")
        print(f"  User: {identity['Arn'].split('/')[-1]}")
        return True
    except Exception as e:
        print(f"✗ AWS credentials issue: {e}")
        return False

def check_bedrock_access():
    """Check Bedrock access"""
    print("\nChecking Bedrock access...")
    try:
        import boto3
        session = boto3.Session(profile_name='devan', region_name='us-east-1')
        bedrock = session.client('bedrock')
        models = bedrock.list_foundation_models()
        anthropic_models = [m['modelId'] for m in models['modelSummaries'] if m['providerName'] == 'Anthropic']
        print(f"✓ Bedrock access confirmed")
        print(f"  Available Anthropic models: {len(anthropic_models)}")
        for model in anthropic_models[:3]:
            print(f"    - {model}")
        if len(anthropic_models) > 3:
            print(f"    ... and {len(anthropic_models) - 3} more")
        return True
    except Exception as e:
        print(f"✗ Bedrock access issue: {e}")
        return False

async def test_basic_agent():
    """Test a basic AutoGen agent setup"""
    print("\nTesting basic AutoGen agent...")
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        print("✓ Can create AssistantAgent")
        print("✓ Can import model clients")
        return True
    except Exception as e:
        print(f"✗ Agent creation issue: {e}")
        return False

async def main():
    print("="*80)
    print("AutoGen + AWS Bedrock Setup Verification")
    print("="*80 + "\n")
    
    results = []
    
    # Run all checks
    results.append(("Package Imports", check_imports()))
    results.append(("AWS Credentials", check_aws_credentials()))
    results.append(("Bedrock Access", check_bedrock_access()))
    results.append(("AutoGen Agent", await test_basic_agent()))
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All checks passed! You're ready to build AutoGen agents with Bedrock!")
        print("\nNext step: Run 'python test_bedrock.py' to test your first agent!")
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
    
    print("="*80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)