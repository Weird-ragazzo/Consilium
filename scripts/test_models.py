import asyncio
import os

from groq import AsyncGroq


async def test_model_a():
    """Test openai/gpt-oss-120b"""
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("MODEL_MODEL1", "openai/gpt-oss-120b")

    print(f"\n=== Testing Model A: {model} ===")
    client = AsyncGroq(api_key=api_key)
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_completion_tokens=100,
            temperature=0.7,
        )
        print(f"✓ SUCCESS: {resp.choices[0].message.content[:100]}")
        return True
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)[:150]}")
        return False


async def test_model_b():
    """Test openai/gpt-oss-20b"""
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("MODEL_MODEL2", "openai/gpt-oss-20b")

    print(f"\n=== Testing Model B: {model} ===")
    client = AsyncGroq(api_key=api_key)
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_completion_tokens=100,
            temperature=0.7,
        )
        print(f"✓ SUCCESS: {resp.choices[0].message.content[:100]}")
        return True
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)[:150]}")
        return False


async def main():
    print("Testing Groq endpoints with configured models...")
    result_a = await test_model_a()
    result_b = await test_model_b()

    print("\n=== Summary ===")
    print(f"Model A (GPT-OSS-120B): {'✓ PASS' if result_a else '✗ FAIL'}")
    print(f"Model B (GPT-OSS-20B): {'✓ PASS' if result_b else '✗ FAIL'}")

    if result_a and result_b:
        print("\n✓ Both models are working! Ready to run the full pipeline.")
    else:
        print("\n✗ One or more models failed. Check API key and model names.")


if __name__ == '__main__':
    asyncio.run(main())
