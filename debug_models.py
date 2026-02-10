from google import genai
import os

# 1. Get Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found. Run the $env:GEMINI_API_KEY line again.")
    exit(1)

client = genai.Client(api_key=api_key)

print(f"✅ Key found: {api_key[:5]}...")
print("Listing available models...")

try:
    # 2. List models (Simplified for new SDK)
    for m in client.models.list():
        # We just print the name directly to avoid attribute errors
        print(f" - {m.name}")

except Exception as e:
    print(f"❌ Error: {e}")