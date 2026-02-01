import instructor

from openai import OpenAI
from pydantic import BaseModel
from collections.abc import Callable
import ollama

def create_ollama_client(base_url="http://localhost:11434/v1", api_key="ollama"):
    client  = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    return client


def create_instructor(base_url="http://localhost:11434/v1", api_key="instructor"):
    client = instructor.from_openai(
        OpenAI(
            base_url=base_url,
            api_key=api_key,
        ),
        mode=instructor.Mode.JSON,
    )

    return client

def call_ollama(client, prompt, model):
    try: 

        res = client.chat(
            #model="phi4:latest",
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ]
        )

        return res['message']['content']
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None



def call_ollama_vision(image_path, prompt, model, api_url):
    """
    Call Ollama vision model with an image and prompt.
    
    Args:
        image_path: Path to the image file
        prompt: Text prompt to send with the image
        model: Ollama model name to use
        api_url: Base URL for the Ollama API
    
    Returns:
        dict: Response from the Ollama API
    """
    # # Encode the image as base64
    # base64_image = encode_image_base64(image_path)
    
    # # Prepare the API payload
    # payload = {
    #     "model": model,
    #     "prompt": prompt,
    #     "images": [base64_image],
    #     "stream": False
    # }
    
    # # Make the API call
    # try:
    #     response = requests.post(f"{api_url}/api/generate", json=payload)
    #     response.raise_for_status()
    #     return response.json()
    # except requests.exceptions.RequestException as e:
    #     print(f"Error calling Ollama API: {e}")
    #     return None
    try: 
        print("imagePath")
        print(f"./{image_path}")
        res = ollama.chat(
            #model="phi4:latest",
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                    'images': [f"./{image_path}"]
                }
            ]
        )

        return res['message']['content']

    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None



def set_up_task(client, model:str, reply_type:BaseModel, assistant_role="assistant", assistant_prompt:str="You are a helpful assistant.") -> Callable:
    def run(content_input:str) -> type(reply_type):
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": assistant_role,
                    "content": assistant_prompt
                },
                {
                    "role": "user",
                    "content": content_input
                }
            ],
            response_model=reply_type,
        )

        return resp
    return run


