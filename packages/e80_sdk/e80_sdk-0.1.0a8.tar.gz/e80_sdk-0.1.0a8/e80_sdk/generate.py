from e80_sdk import Eighty80


def generate(
    prompt: str,
    model: str = "8080/8080",
    stream: bool = False,
):
    client = Eighty80().completion_sdk()
    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions(messages, model=model, stream=stream)

    content = response["choices"][0]["message"]["content"]
    return content
