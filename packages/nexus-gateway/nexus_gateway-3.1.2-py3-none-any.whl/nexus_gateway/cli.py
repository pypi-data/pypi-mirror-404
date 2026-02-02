import os
import sys
import time
import json
from .client import NexusClient

# 🚀 THE ALIAS MAP
MODEL_ALIASES = {
    "gpt": "gpt-3.5-turbo",
    "gpt4": "gpt-4o",
    "pro": "gpt-4o",
    "llama": "llama-3.3-70b-versatile",
    "groq": "llama-3.3-70b-versatile",
    "gemini": "gemini-1.5-flash",
    "google": "gemini-1.5-flash",
}

def main():
    print("\n\033[1;34m============================================")
    print("    NEXUS GATEWAY - SOVEREIGN CLI v3.1")
    print("    Inference.Control.Plane.Active")
    print("============================================\033[0m")

    api_key = os.getenv("NEXUS_API_KEY")
    if not api_key:
        api_key = input("🔑 \033[1mEnter Nexus API Key:\033[0m ").strip()

    client = NexusClient(api_key=api_key)
    if not client.validate_key():
        print("\n\033[1;31m❌ Access Denied: Invalid Key.\033[0m")
        return

    print("✅ \033[1;32mGateway Connected! Protocol v3.1 Active.\033[0m")
    print("\033[90mShortcuts: model=llama, model=gemini, /clear, /exit\033[0m\n")

    active_model = "gpt-3.5-turbo"

    while True:
        try:
            user_input = input(f"\033[1;32m[ {active_model} ] > \033[0m").strip()
            if not user_input: continue

            # --- 🚀 1. HIGH-PRIORITY COMMAND PARSER ---
            cmd = user_input.lower()
            
            # Handling model switch (model=, /model, model )
            if "=" in cmd and "model" in cmd:
                val = user_input.split("=")[1].strip()
                active_model = MODEL_ALIASES.get(val.lower(), val)
                print(f"🔄 \033[1;36mEngine Switched -> {active_model}\033[0m\n")
                continue

            if cmd.startswith("/model "):
                val = user_input.split(" ")[1].strip()
                active_model = MODEL_ALIASES.get(val.lower(), val)
                print(f"🔄 \033[1;36mEngine Switched -> {active_model}\033[0m\n")
                continue

            # System Commands
            if cmd in ["/exit", "exit", "quit", "/quit"]:
                print("\033[1;34mTerminating Session. 👋\033[0m")
                break
            if cmd in ["/clear", "clear"]:
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            # --- 🚀 2. INFERENCE EXECUTION ---
            print("\033[1;34mNexus:\033[0m ", end="", flush=True)
            start_time = time.time()
            full_response = ""

            try:
                for chunk in client.chat(user_input, model=active_model, stream=True):
                    print(chunk, end="", flush=True)
                    full_response += chunk
                
                latency = int((time.time() - start_time) * 1000)
                # Token count logic (chars / 4)
                tokens = len(full_response) // 4
                print(f"\n\n\033[90m[ {latency}ms | {tokens} tokens | Layer: Infrastructure ]\033[0m\n")
                
            except Exception as e:
                print(f"\n\033[1;31m{e}\033[0m\n")

        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break

if __name__ == "__main__":
    main()