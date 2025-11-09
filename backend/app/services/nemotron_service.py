import os
from openai import OpenAI
from typing import Optional
import httpx

# Initialize NVIDIA Nemotron client
# NVIDIA API is compatible with OpenAI SDK
def get_nemotron_client():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set")
    
    base_url = "https://integrate.api.nvidia.com/v1"
    
    # Explicitly create httpx client to avoid proxies compatibility issue
    # httpx 0.28+ removed proxies argument, so we create client without it
    http_client = httpx.Client(timeout=60.0)
    
    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        http_client=http_client
    )


def generate_mermaid_from_prompt(prompt: str) -> str:
    """
    Convert a text prompt to Mermaid diagram syntax using NVIDIA Nemotron.
    
    Args:
        prompt: The user's text description of what they want to draw
        
    Returns:
        Mermaid diagram syntax as a string
    """
    client = get_nemotron_client()
    
    system_prompt = """You are a Mermaid diagram generator. Convert user descriptions into valid Mermaid diagram syntax.
    
Rules:
1. Only output the Mermaid code, no explanations or markdown formatting
2. Do not wrap the output in ```mermaid code blocks
3. Choose the most appropriate diagram type (flowchart, sequenceDiagram, classDiagram, etc.)
4. Make the diagram clear and well-structured
5. Use descriptive labels and meaningful relationships

Examples:
- "A user logs in, then views dashboard" -> flowchart TD\n    A[User] -->|logs in| B[Login]\n    B -->|views| C[Dashboard]
- "Alice sends message to Bob" -> sequenceDiagram\n    Alice->>Bob: Message
"""
    
    user_prompt = f"Convert this description into a Mermaid diagram: {prompt}"
    
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        mermaid_code = response.choices[0].message.content.strip()
        
        # Clean up the response - remove markdown code blocks if present
        if mermaid_code.startswith("```"):
            lines = mermaid_code.split("\n")
            # Remove first line (```mermaid or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            mermaid_code = "\n".join(lines).strip()
        
        return mermaid_code
    except Exception as e:
        raise Exception(f"Failed to generate Mermaid diagram: {str(e)}")
