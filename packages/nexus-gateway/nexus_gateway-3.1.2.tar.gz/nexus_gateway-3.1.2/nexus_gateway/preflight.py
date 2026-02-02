from client import NexusClient
import time

# 1. Initialize with your LIVE Nexus Key
# Pointing to your production URL
client = NexusClient(
    api_key="nk-your-real-key-here", 
    base_url="https://nexusgateway.onrender.com/api"
)

def run_tests():
    print("🚀 Nexus Gateway v3.1 Pre-flight starting...")

    # --- TEST 1: SYNC CHAT (GPT-3.5) ---
    print("\n[TEST 1] Testing Sync Chat (OpenAI)...")
    try:
        response = client.chat(message="Hii", model="gpt-3.5-turbo", stream=False)
        print(f"✅ Success: {response[:50]}...")
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")

    # --- TEST 2: STREAMING + REDIS HIT (Groq) ---
    print("\n[TEST 2] Testing Streaming & Cache Hit (Groq)...")
    prompt = "What is the speed of light?"
    
    print("Phase A: Cold Request (Miss)...")
    for chunk in client.chat(message=prompt, model="llama-3.3-70b-versatile", stream=True):
        print(chunk, end="", flush=True)
    
    print("\nPhase B: Hot Request (Redis Hit)...")
    start = time.time()
    for chunk in client.chat(message=prompt, model="llama-3.3-70b-versatile", stream=True):
        print(chunk, end="", flush=True)
    latency = (time.time() - start) * 1000
    print(f"\n✅ Cache Hit Latency: {latency:.2f}ms")

    # --- TEST 3: SOVEREIGN SHIELD (403 GATE) ---
    print("\n[TEST 3] Testing Sovereign Shield (PII Redaction)...")
    # Prompt jisme email ho taaki rule trigger ho
    pii_prompt = "My personal email is testuser@gmail.com, send me a summary."
    try:
        print("Executing PII Test...")
        for chunk in client.chat(message=pii_prompt, model="gpt-3.5-turbo", stream=True):
            print(chunk, end="", flush=True)
        print("\n✅ Shield Test Passed (Look for [REDACTED] in response)")
    except Exception as e:
        print(f"❌ Shield Test Error: {e}")

    # --- TEST 4: BYOK BYPASS ---
    # print("\n[TEST 4] Testing BYOK (Optional)...")
    # try:
    #     res = client.chat(message="Hii", model="gpt-4o", provider_key="sk-your-key")
    #     print("✅ BYOK Success")
    # except Exception as e:
    #     print(f"❌ BYOK Failed: {e}")

if __name__ == "__main__":
    run_tests()