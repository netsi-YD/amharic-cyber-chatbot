import os
import time
from dotenv import load_dotenv
from groq import Groq
from chatbot_core import get_response, run_scenario, evaluate_answer

def main():
    language = "am"  # default to Amharic
    conversation = []   # list of {"role": "...", "content": "..."}

    print("\n🤖 ሰላም! /en for English, /am for Amharic, 'scenario' for a test, 'quit' to exit.")
    print("=" * 60)

    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() in ["quit", "exit", "ተው"]:
            print("🤖 Goodbye! / ቻው!")
            break

        # Language switching
        if user_input.lower() == "/am":
            language = "am"
            print("🤖 አማርኛ ተመርጧል።")
            continue
        elif user_input.lower() == "/en":
            language = "en"
            print("🤖 English selected.")
            continue

        # Scenario mode
        if user_input.lower() == "scenario":
            try:
                scenario_text = run_scenario(language)
                print(f"\n🤖 {scenario_text}")
                answer = input("\n👤 Your answer: ").strip()
                if answer.lower() in ["quit", "exit", "ተው"]:
                    break
                feedback = evaluate_answer(scenario_text, answer, language)
                print(f"\n🤖 {feedback}")
            except Exception as e:
                print(f"\n🤖 Something went wrong: {e}")
            continue

        # Normal chat
        try:
            reply = get_response(user_input, language, conversation)
            print(f"\n🤖 {reply}")
            # Update conversation history
            conversation.append({"role": "user", "content": user_input})
            conversation.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"\n🤖 Error: {e}")

if __name__ == "__main__":
    main()