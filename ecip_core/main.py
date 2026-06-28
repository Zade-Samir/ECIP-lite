from ecip_core.prompt.prompt_builder import PromptBuilder
from ecip_core.inference.providers.ollama_provider import OllamaProvider


def main():

    builder = PromptBuilder()

    provider = OllamaProvider()

    prompt = builder.build_prompt(
        question="Explain Dependency Injection."
    )

    answer = provider.generate(prompt)

    print(answer)


if __name__ == "__main__":
    main()