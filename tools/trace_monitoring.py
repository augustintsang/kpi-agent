from langtrace_python_sdk import langtrace # Must precede any llm module imports

langtrace.init(api_key = 'API_KEY_HERE')

from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "Tell me about Emperor Caracalla"
        }
    ]
)

print(completion.choices[0].message.content)