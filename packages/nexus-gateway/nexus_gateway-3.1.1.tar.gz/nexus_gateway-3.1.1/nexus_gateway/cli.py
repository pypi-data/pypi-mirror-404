import os
import sys
import time
import json
from .client import NexusClient

def main():
    # --- 1. INDUSTRIAL HEADER ---
    print("\n\033[1;34m============================================")
    print("    NEXUS GATEWAY - SOVEREIGN CLI v3.1")
    print("    Inference.Control.Plane.Active")
    print("============================================\033[0m")

    # 2. KEY PROVISIONING
    api_key = os.getenv("NEXUS_API_KEY")
    if not api_key:
        try:
            api_key = input("🔑 \033[1mEnter Nexus API Key:\033[0m ").strip()
        except KeyboardInterrupt:
            sys.exit(0)

    # 3. HANDSHAKE
    print("🛰️  Establishing connection...", end="\r")
    client = NexusClient(api_key=api_key)
    
    if not client.validate_key():
        print("\n\033[1;31m❌ Access Denied: Invalid Infrastructure Key.")
        print("Provision a key at: https://nexus-gateway.org/dashboard\033[0m")
        return

    print("✅ \033[1;32mGateway Connected! Protocol v3.1 Active.\033[0m")
    print("\033[90mCommands: /model [name], /exit, /clear\033[0m\n")

    # 4. SESSION STATE
    active_model = "gpt-3.5-turbo"

    # 5. INTERACTIVE COMMAND LOOP
    while True:
        try:
            user_input = input(f"\033[1;32m[ {active_model} ] > \033[0m").strip()
            
            # Internal Commands
            if user_input.lower() in ["/exit", "exit", "quit"]:
                print("\033[1;34mTerminating Session. Secure Data Plane Closed. 👋\033[0m")
                break
            
            if user_input.lower() == "/clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            if user_input.lower().startswith("/model"):
                parts = user_input.split(" ")
                if len(parts) > 1:
                    active_model = parts[1]
                    print(f"🔄 Switched to Engine: \033[1;36m{active_model}\033[0m\n")
                else:
                    print("Usage: /model [gpt-4o | llama-3.3-70b | gemini-1.5-flash]\n")
                continue

            if not user_input:
                continue

            # 6. INFERENCE EXECUTION
            print("\033[1;34mNexus:\033[0m ", end="", flush=True)
            
            start_time = time.time()
            full_response = ""

            try:
                # Direct Stream from Sovereign Bridge
                for chunk in client.chat(user_input, model=active_model, stream=True):
                    print(chunk, end="", flush=True)
                    full_response += chunk
                
                # Telemetry Calculation
                latency = int((time.time() - start_time) * 1000)
                print(f"\n\n\033[90m[ {latency}ms | {len(full_response)//4} tokens | Layer: Infrastructure ]\033[0m\n")
                
            except Exception as e:
                # Handle Sovereign Shield blocks (403) or Quota limits (402)
                print(f"\n\033[1;31m{e}\033[0m\n")

        except KeyboardInterrupt:
            print("\n\033[1;34mEmergency Shutdown Initiated. Goodbye! 👋\033[0m")
            break

if __name__ == "__main__":
    main()