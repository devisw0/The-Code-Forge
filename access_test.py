import boto3
import json

# IMPORTANT: Change this to the name of the profile you want to test.
PROFILE_NAME = 'devan2'
AWS_REGION = 'us-east-1'
MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'

print(f"--- Testing model access for profile: '{PROFILE_NAME}' ---")

try:
    # Create a session using the specified profile
    session = boto3.Session(profile_name=PROFILE_NAME, region_name=AWS_REGION)

    # Create a client for the Bedrock runtime service
    bedrock_runtime = session.client('bedrock-runtime')

    # The data payload to send to the model
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hi"}]
    })

    # Invoke the model
    response = bedrock_runtime.invoke_model(modelId=MODEL_ID, body=body)

    # Read and print the successful response
    result = json.loads(response['body'].read())
    print("\n✅ SUCCESS! Your profile has the correct permissions to access this model.")

except Exception as e:
    error_message = str(e)
    if "AccessDeniedException" in error_message:
        print(f"\n❌ FAILURE: Access Denied.")
        print("   The profile is working, but the IAM role it uses does NOT have bedrock:InvokeModel permission.")
    elif "ProfileNotFound" in error_message:
        print(f"\n❌ FAILURE: Profile Not Found.")
        print(f"   The profile named '{PROFILE_NAME}' was not found in your ~/.aws/config file.")
    else:
        print(f"\n❌ An unexpected error occurred: {error_message}")