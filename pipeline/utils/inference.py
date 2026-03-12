import openai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key = api_key)

def LM(model, messages):
  """
  Send a chat completion request to an LLM and return the generated response text.

  Args:
      model (str): Name of the language model to use.
      messages (list): List of chat messages formatted as dictionaries
                        with roles (e.g., "system", "user", "assistant").

  Returns:
      str: The content of the model's response message.

  Notes:
      - For models other than GPT-5, the function sets temperature=0.0
        for deterministic outputs and limits the response to 1024 tokens.
      - Assumes a global `client` object is available for making API calls.
  """
  
  params = {
  "model": model,
  "messages": messages,
  }

  if "gpt-5" not in model.lower():
    params["temperature"] = 0.0
    params["max_tokens"] = 1024

  response = client.chat.completions.create(**params)
  return response.choices[0].message.content
        
if __name__ == "__main__":
  # Models -----------------------------------------------------------------
  m1 = "gpt-4o-mini"
  m2 = "gpt-5-mini"

  message = [{"role": "user", "content": "Tell me a joke."}]
  resp = LM(model=m2, messages=message)