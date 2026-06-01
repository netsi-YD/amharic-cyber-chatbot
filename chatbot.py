import os
import time
from dotenv import load_dotenv
from groq import Groq

# Load API key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("❌ Groq API key not found. Make sure your .env file has GROQ_API_KEY=...")
    exit()

# Create Groq client
client = Groq(api_key=api_key)

# Model (free tier, fast, supports Amharic)
MODEL = "llama-3.1-8b-instant"

# System prompt: the bot's personality and rules
system_prompt = """
You are "Cyber Amharic Tutor", a friendly and patient cybersecurity awareness assistant for everyday Ethiopians.
You ONLY speak Amharic, no matter what language the user uses. Even if they type in English, reply in Amharic.
Your goal is to teach simple, practical cybersecurity tips in a conversational way.

Focus areas:
- Creating strong passwords (ጠንካራ የይለፍ ቃል)
- Recognizing phishing messages (የማጭበርበር መልዕክቶችን እንዴት መለየት እንደሚቻል)
- Identifying scams on Telegram, SMS, and social media (ማጭበርበር)
- Protecting personal information online (የግል መረጃን መጠበቅ)
- Safe mobile money (M-Pesa, Telebirr) habits

Rules:
- Keep explanations simple, as if talking to a non‑technical friend.
- Use common, everyday Amharic, not complex terms.
- If the user shares something worrying (e.g., "someone tricked me"), respond with empathy and give clear next steps.
- Never request personal data like passwords or account details.
- Start by greeting the user and asking how you can help them stay safe online.

Remember: Your answers must be in Amharic only.
"""

# Conversation history (system prompt is always the first message)
conversation = [
    {"role": "system", "content": system_prompt},
    {"role": "assistant", "content": "እሺ፣ እንደታዘዝከኝ አደርጋለሁ።"}
]

def chat_with_retry(messages, max_retries=3, delay=2):
    """Call Groq API with retry on 5xx errors."""
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stop=None
            )
            return completion.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            # Retry only on server errors (5xx) or rate limits (429)
            if "5" in error_str[:1] or "429" in error_str or "rate_limit" in error_str.lower():
                print(f"  [Server busy, retrying in {delay}s (attempt {attempt}/{max_retries})...]")
                time.sleep(delay)
                delay *= 2
            else:
                raise e
    raise Exception("Groq API still unavailable after multiple retries.")

def run_scenario():
    print("\n--- 🛡️ ሁኔታ ሙከራ (Scenario) ---")
    scenario_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": """
        አንድ አጭር የሳይበር ደህንነት ሁኔታ በአማርኛ ፍጠር።
        ሁኔታው ተጠቃሚው ያጋጠመውን አጠራጣሪ ነገር ይግለጽ (ለምሳሌ፦ በቴሌግራም አገናኝ ተላከ፣ ወይም አንድ ሰው የባንክ መረጃ ጠየቀ)።
        ከዚያ ጥያቄ አቅርብ፦ "ምን ታደርጋለህ?"
        ከተጠቃሚው መልስ በኋላ፣ ትክክለኛውን እርምጃ እና ማብራሪያ በአማርኛ ስጥ።
        ሁሌም በአማርኛ ብቻ መልስ።
        """}
    ]
    scenario_text = chat_with_retry(scenario_messages)
    print(scenario_text)

    user_answer = input("\n👤 የአንተ መልስ: ")
    if user_answer.lower() in ["quit", "exit", "ተው"]:
        print("🤖 ሙከራውን ትተናል።")
        return

    eval_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""
        ተጠቃሚው ለሚከተለው ሁኔታ መልስ ሰጥቷል፦
        ሁኔታ፦ {scenario_text}
        የተጠቃሚው መልስ፦ {user_answer}
        እባክህ መልሱን ገምግም። ትክክል ከሆነ አመስግን፣ ካልሆነ ግን በትህትና አርም እና ትክክለኛውን አሰራር አስረዳ።
        ሁሉንም ነገር በአማርኛ ብቻ ተናገር።
        """}
    ]
    feedback = chat_with_retry(eval_messages)
    print(f"\n🤖 ሳይበር አማርኛ ረዳት: {feedback}")

# Main chat loop
print("\n🤖 ሰላም! የሳይበር ደህንነት ረዳትህ እዚህ ነኝ። (ለማቆም 'quit' ብለህ ጻፍ)")
print("=" * 60)

while True:
    user_input = input("\n👤 አንተ: ")
    if user_input.lower() in ["quit", "exit", "ተው"]:
        print("🤖 ቻው! በሰላም ሁን። መልካም ቀን!")
        break

    if user_input.lower() == "scenario":
        run_scenario()
        continue

    # Append user message to conversation
    conversation.append({"role": "user", "content": user_input})

    try:
        answer = chat_with_retry(conversation)
        print(f"\n🤖 ሳይበር አማርኛ ረዳት: {answer}")
        # Append assistant reply to history
        conversation.append({"role": "assistant", "content": answer})
    except Exception as e:
        print("\n🤖 ይቅርታ፣ አንድ ችግር ተከስቷል። እባክህ ቆይተህ ሞክር።")
        # Remove the user message if the API failed, to keep history clean
        conversation.pop()
