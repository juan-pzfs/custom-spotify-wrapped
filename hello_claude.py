from dotenv import load_dotenv
import anthropic

MODEL = "claude-haiku-5-5"
PRICE_INPUT = 0.10    # dollars per million input tokens
PRICE_OUTPUT = 0.50   # dollars per million output tokens

# 1. Load the API key from the .env file
load_dotenv()

# 2. Create the client: the connection to the Claude API
client = anthropic.Anthropic()

# 3. Send the message
response = client.messages.create(
    model=MODEL,
    max_tokens=200,
    messages=[
        {"role": "user", "content": "In one sentence, what is Spotify Wrapped?"}
    ],
)

# 4. Read the answer (only text blocks, skip any thinking blocks)
text = "".join(block.text for block in response.content if block.type == "text")
print(text)

# 5. Usage and cost (the "receipt")
usage = response.usage
cost = (usage.input_tokens * PRICE_INPUT + usage.output_tokens * PRICE_OUTPUT) / 1_000_000
print(f"Tokens: {usage.input_tokens} input / {usage.output_tokens} output | Cost: ${cost:.6f}")