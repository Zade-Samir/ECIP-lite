from ollama import chat

def main():
    print("=" * 60)
    print("🚀 ECIP Lite - AI Connectivity Test")
    print("=" * 60)

    question = "Write a Java method to reverse a string."

    response = chat(
        model="qwen3.5:9b",
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )

    print("\nQuestion:")
    print(question)

    print("\nAnswer:\n")
    print(response.message.content)


if __name__ == "__main__":
    main()