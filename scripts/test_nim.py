import asyncio
import os

from groq import AsyncGroq


async def test():
    load_env = os.path.exists(".env")
    if load_env:
        try:
            from dotenv import load_dotenv

            load_dotenv(".env")
        except Exception:
            pass

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("MODEL_MODEL2", "openai/gpt-oss-20b")

    print("Using model:", model)
    if not api_key:
        print("No GROQ_API_KEY found in environment.")
        return

    client = AsyncGroq(api_key=api_key)
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hi in one short sentence."}],
            max_completion_tokens=20,
            temperature=0.0,
        )
        choice = resp.choices[0]
        msg = getattr(choice, "message", None)
        content = getattr(msg, "content", "") if msg else str(choice)
        print("SUCCESS:", content)
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))


if __name__ == '__main__':
    asyncio.run(test())
