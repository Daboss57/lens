from __future__ import annotations

import os
import uuid


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY or GOOGLE_API_KEY before running this script.")

    os.environ.setdefault("LENS_API_URL", "http://localhost:8100")
    os.environ.setdefault("LENS_ENABLED", "true")

    import lens.gemini  # noqa: F401  # Patches Gemini clients for LENS tracing.
    from google import genai

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    session_id = f"gemini-test-{uuid.uuid4().hex[:8]}"
    prompt = "Write a short haiku about observability tooling, then add one line about why traces matter."

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        lens_session_id=session_id,
        lens_user_id="manual-gemini-test",
        lens_metadata={"source": "scripts/test_gemini_sdk.py"},
    )

    text = getattr(response, "text", None)
    print("Gemini response:\n")
    if text:
        print(text)
    elif hasattr(response, "model_dump"):
        print(response.model_dump())
    else:
        print(response)

    print("\nLENS trace info:")
    print(f"- LENS API URL: {os.environ['LENS_API_URL']}")
    print(f"- Session ID: {session_id}")
    print(f"- Model: {model}")
    print("- This script passes LENS-only kwargs that are stripped before the Gemini SDK call,")
    print("  so the trace should appear under the same session in the dashboard.")
    print("- If the LENS server is running, this call should now appear in the dashboard.")


if __name__ == "__main__":
    main()
