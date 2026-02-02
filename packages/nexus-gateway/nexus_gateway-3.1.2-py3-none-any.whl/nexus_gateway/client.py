import requests
import json

class NexusClient:
    def __init__(self, api_key: str, base_url: str = "https://nexusgateway.onrender.com/api"):
        """
        Initialize the Nexus Sovereign Gateway.
        :param api_key: Your unique Nexus API Key (nk-...)
        :param base_url: The production endpoint of your Go backend
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def validate_key(self) -> bool:
        """Verifies if the Nexus API Key is authorized."""
        if not self.api_key.startswith("nk-"):
            return False
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            res = requests.get(f"{self.base_url}/stats", headers=headers, timeout=5)
            return res.status_code == 200
        except:
            return False

    def chat(self, message: str, model: str = "gpt-3.5-turbo", stream: bool = True, provider_key: str = None):
        """
        Execute universal inference with Adaptive Routing.
        
        :param message: The user prompt.
        :param model: The target model ID (gpt-4o, llama-3.3-70b, gemini-1.5-flash).
        :param stream: Boolean to enable Server-Sent Events (SSE).
        :param provider_key: (Optional) Your own provider key for BYOK bypass.
        """
        endpoint = "/chat/stream" if stream else "/chat"
        url = f"{self.base_url}{endpoint}"
        
        # Base Headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 🚀 THE BYOK SHIELD: Auto-map keys to correct headers
        if provider_key:
            m = model.lower()
            if "gpt" in m:
                headers["x-nexus-openai-key"] = provider_key
            elif "llama" in m or "mixtral" in m:
                headers["x-nexus-groq-key"] = provider_key
            elif "gemini" in m:
                headers["x-nexus-gemini-key"] = provider_key
            elif "claude" in m:
                headers["x-nexus-anthropic-key"] = provider_key

        payload = {"message": message, "model": model}

        if stream:
            return self._handle_stream(url, payload, headers)
        
        # Handle Synchronous Request
        response = requests.post(url, json=payload, headers=headers)
        self._check_error(response)
        
        # Extract response content
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def _handle_stream(self, url, payload, headers):
        """Internal helper to decode Nexus SSE Protocol chunks."""
        response = requests.post(url, json=payload, headers=headers, stream=True)
        self._check_error(response)

        for line in response.iter_lines():
            if not line:
                continue
            
            decoded_line = line.decode('utf-8')
            
            if decoded_line.startswith("data: "):
                content_raw = decoded_line[6:].strip()
                
                # Check for protocol termination
                if content_raw == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(content_raw)
                    # Extract the word/token from the standard OpenAI format
                    delta_content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta_content:
                        yield delta_content
                except json.JSONDecodeError:
                    # Handle raw error messages if they aren't JSON
                    if "error" in content_raw.lower():
                        yield f"\n[Nexus Error]: {content_raw}"
                    continue

    def _check_error(self, response):
        """Standardized Error Handling for Infrastructure failures."""
        if response.status_code == 401:
            raise Exception("❌ Unauthorized: Invalid Nexus API Key")
        if response.status_code == 402:
            raise Exception("⛔ Quota Exceeded: Upgrade to Pro or use a BYOK provider key.")
        if response.status_code == 403:
            raise Exception("🛡️ Sovereign Shield: Request blocked by governance policy.")
        if response.status_code >= 400:
            raise Exception(f"🚨 Infrastructure Error {response.status_code}: {response.text}")