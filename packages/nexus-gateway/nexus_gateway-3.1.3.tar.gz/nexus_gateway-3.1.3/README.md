# 🐍 Nexus Gateway Python SDK (v3.1.0)

**The High-Performance Sovereign Infrastructure for AI Engineering.**

One line of code to reduce LLM latency by 95%, costs by 90%, and enforce deterministic governance at the edge.

[![PyPI version](https://badge.fury.io/py/nexus-gateway.svg)](https://badge.fury.io/py/nexus-gateway)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Infrastructure](https://img.shields.io/badge/Infrastructure-v3.1.0--Stable-indigo)](https://nexus-gateway.org)

---

## ⚡ Key Superpowers

*   **Semantic Caching (Layer 0 & 1):** Sub-5ms response times via Redis/Pinecone hybrid caching. Stop paying for the same API call twice.
*   **Adaptive Universal Router:** Intelligent failover and routing across OpenAI, Groq, and Google Gemini with a single API signature.
*   **Sovereign Shield:** Edge-level PII redaction and deterministic governance (v3.0). Ensure data privacy before it hits the provider.
*   **Multi-Provider BYOK:** Bring Your Own Key to bypass Nexus credits and utilize direct provider billing with zero overhead.

##  Installation

```bash
pip install nexus-gateway
```
##  CLI Tool: Interactive Command Center
Nexus Gateway provides a powerful interactive terminal experience.

```# Launch the Sovereign Shell
nexus
```
### Inside the CLI:
   * /model [name] - Switch engine on-the-fly (e.g., /model llama-3.3-70b)
   * /clear - Wipe session history
   * /exit - Terminate secure data plane


##  Usage (Python Implementation)

    1. Initialize the Sovereign Client
```
    from nexus_gateway import NexusClient

    # Provisioned key from https://nexus-gateway.org/dashboard
    client = NexusClient(api_key="nk-your-key-here")

```
    2. Universal Real-Time Streaming
```
# The same syntax for Groq, Gemini, or OpenAI
stream = client.chat(
    model="llama-3.3-70b-versatile", 
    message="Optimize this Go connection pool.",
    stream=True
)

for word in stream:
    print(word, end="", flush=True)

```
    3. BYOK Bypass (Zero-Cost Scaling)

```
    # Pass your own provider key to skip Nexus credit usage
    response = client.chat(
    model="gpt-4o",
    message="Summarize the legal implications of AI governance.",
    provider_key="sk-your-openai-key"
    )
```

##  Supported Model Engines
```   
    Provider	Core Models
    Groq (Ultra Fast)	llama-3.3-70b-versatile, llama-3.1-8b-instant
    Google (Adaptive)	gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash-exp
    OpenAI (Standard)	gpt-4o, gpt-4-turbo, gpt-3.5-turbo
    Anthropic (Pro)	claude-3-5-sonnet-latest, claude-3-opus-20240229
```

## Infrastructure Performance
```
    Metric	OpenAI SDK	Nexus Gateway
    Cache Latency	1200ms+	5ms (Layer 0 Hit)
    Redundant Call Cost	Full Price	$0.00
    Routing Reliability	Single Vendor	Self-Healing Failover
    Governance	None	AES-256 Sovereign Shield
```
#  Authentication & Security
Register for a protocol access key at: https://www.nexus-gateway.org

MIT License © 2025 Sunny Anand · [Documentation](https://nexus-gateway.org/docs) · [GitHub](https://github.com/ANANDSUNNY0899/NexusGateway)





    

