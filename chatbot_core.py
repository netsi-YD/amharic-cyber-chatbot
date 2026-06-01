import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)
MODEL = "llama-3.1-8b-instant"

# System prompts for both languages
SYSTEM_PROMPTS = {
    "am": """
You are "Cyber Amharic Tutor", a friendly and patient cybersecurity awareness assistant for everyday Ethiopians.
You ONLY speak Amharic. Your goal is to teach simple, practical cybersecurity tips in a conversational way.

Focus areas:
- Creating strong passwords (ጠንካራ የይለፍ ቃል)
- Recognizing phishing messages (የማጭበርበር መልዕክቶች)
- Identifying scams on Telegram, SMS, and social media (ማጭበርበር)
- Protecting personal information online (የግል መረጃ መጠበቅ)
- Safe mobile money habits (M-Pesa, Telebirr)

Rules:
- Keep explanations simple, as if talking to a non‑technical friend.
- Use everyday Amharic, not complex terms.
- If the user shares something worrying, respond with empathy and give clear next steps.
- Never request personal data like passwords or account details.
""",
    "en": """
You are "Cyber Security Buddy", a friendly and patient cybersecurity awareness assistant.
You speak English clearly and simply. Your goal is to teach practical online safety tips.

Focus areas:
- Creating strong passwords
- Recognizing phishing emails and messages
- Identifying scams on social media, SMS, and messaging apps
- Protecting personal information online
- Safe mobile money and banking habits

Rules:
- Keep explanations simple, like talking to a non‑technical friend.
- If the user shares something worrying, respond with empathy and give clear next steps.
- Never ask for personal data like passwords or bank details.
"""
}

def generate_with_retry(messages, max_retries=3, delay=2):
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
            if "5" in error_str[:1] or "429" in error_str or "rate_limit" in error_str.lower():
                print(f"  [Retry {attempt}/{max_retries} in {delay}s...]")
                time.sleep(delay)
                delay *= 2
            else:
                raise e
    raise Exception("Groq API still unavailable after retries.")

def run_scenario(language):
    """
    Generate a cybersecurity scenario and evaluate the user's answer.
    Returns (scenario_text, None) first, then after user answers,
    call evaluate_answer(scenario_text, user_answer, language) to get feedback.
    """
    prompt = ""
    if language == "am":
        prompt = """
        አንድ አጭር የሳይበር ደህንነት ሁኔታ በአማርኛ ፍጠር።
        ሁኔታው ተጠቃሚው ያጋጠመውን አጠራጣሪ ነገር ይግለጽ።
        ከዚያ ጥያቄ አቅርብ፦ "ምን ታደርጋለህ?"
        ከተጠቃሚው መልስ በኋላ ትክክለኛውን እርምጃ እና ማብራሪያ በአማርኛ ስጥ።
        """
    else:
        prompt = """
        Create a short cybersecurity scenario in simple English.
        Describe a suspicious situation (e.g., a strange link, a request for personal info).
        Ask: "What would you do?"
        After the user answers, provide the correct action and explanation.
        """
    messages = [{"role": "system", "content": SYSTEM_PROMPTS[language]},
                {"role": "user", "content": prompt}]
    scenario_text = generate_with_retry(messages)
    return scenario_text

def evaluate_answer(scenario_text, user_answer, language):
    if language == "am":
        prompt = f"""
        ተጠቃሚው ለሚከተለው ሁኔታ መልስ ሰጥቷል፦
        ሁኔታ፦ {scenario_text}
        የተጠቃሚው መልስ፦ {user_answer}
        መልሱን ገምግም። ትክክል ከሆነ አመስግን፣ ካልሆነ በትህትና አርምና ትክክለኛውን አሰራር አስረዳ።
        """
    else:
        prompt = f"""
        The user answered the following scenario:
        Scenario: {scenario_text}
        User answer: {user_answer}
        Evaluate the answer. If correct, congratulate. If not, gently correct and explain the right approach.
        """
    messages = [{"role": "system", "content": SYSTEM_PROMPTS[language]},
                {"role": "user", "content": prompt}]
    return generate_with_retry(messages)

def get_response(user_message, language, conversation_history=None):
    """
    Returns the assistant's reply using the given language and conversation history.
    """
    if conversation_history is None:
        conversation_history = []

    # Build messages list: system prompt + history + current message
    messages = [{"role": "system", "content": SYSTEM_PROMPTS[language]}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    reply = generate_with_retry(messages)
    return reply