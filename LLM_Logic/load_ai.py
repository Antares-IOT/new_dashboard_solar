import requests
import json

def ask_ai(prompt: str):
    """
    Fungsi untuk berkomunikasi dengan AI model Gemma3:1b
    
    Args:
        prompt: Pertanyaan atau prompt dari user
    
    Returns:
        Response dari AI dalam bentuk string
    """
    try:
        url = "http://36.92.47.218:14334/api/chat"
        
        payload = {
            "model": "gemma3:1b",
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": "Kamu adalah chatbot yang menjawab singkat, jelas, dan dalam bahasa Indonesia."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        print(f"[AI] Sending request to: {url}")
        print(f"[AI] Prompt: {prompt}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"[AI] Response status: {response.status_code}")
        
        response.raise_for_status()
        
        data = response.json()
        
        print(f"[AI] Response data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # Extract content dari response
        if "message" in data and "content" in data["message"]:
            content = data["message"]["content"]
            print(f"[AI] Extracted content: {content}")
            return content
        else:
            print(f"[AI] Unexpected response structure: {data}")
            return "Maaf, saya tidak dapat memproses pertanyaan Anda saat ini."
            
    except requests.exceptions.Timeout:
        print("[AI] Timeout error")
        return "Maaf, permintaan timeout. Silakan coba lagi."
    except requests.exceptions.RequestException as e:
        print(f"[AI] Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[AI] Response text: {e.response.text}")
        return "Maaf, terjadi kesalahan saat memproses AI."
    except json.JSONDecodeError as e:
        print(f"[AI] JSON decode error: {e}")
        return "Maaf, response dari AI tidak valid."
    except Exception as e:
        print(f"[AI] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return "Maaf, terjadi kesalahan yang tidak terduga."