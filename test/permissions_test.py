import boto3
import json

session = boto3.Session(profile_name='devan2', region_name='us-east-1')
bedrock = session.client('bedrock-runtime')

try:
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}],
            "max_tokens": 10
        })
    )
    
    result = json.loads(response['body'].read())
    print("✅ SUCCESS! You have permissions!")
    print(f"Response: {result['content'][0]['text']}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    if "AccessDeniedException" in str(e):
        print("\n⚠️  You don't have IAM permissions to invoke Bedrock models.")
        print("Someone needs to add bedrock:InvokeModel permission to your IAM user/role.")