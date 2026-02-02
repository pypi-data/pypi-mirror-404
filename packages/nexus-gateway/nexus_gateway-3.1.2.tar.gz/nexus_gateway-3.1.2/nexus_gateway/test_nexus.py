from nexus_gateway import NexusClient

client = NexusClient(api_key="nk-your-key-here")

# Test 1: Fast Groq Inference
print("--- Llama 3 via Nexus ---")
for word in client.chat(model="llama-3.3-70b-versatile", message="Explain Go interfaces."):
    print(word, end="", flush=True)

# Test 2: BYOK Bypass
# print("\n\n--- GPT-4 via BYOK ---")
# for word in client.chat(model="gpt-4o", message="Analyze this code...", provider_key="sk-openai-key"):
#    print(word, end="", flush=True)