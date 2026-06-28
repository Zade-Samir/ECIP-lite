from ecip_core.inference.inference_service import InferenceService


def main():

    service = InferenceService()

    while True:

        question = input("\nAsk ECIP > ")

        if question.lower() in ["exit", "quit"]:

            print("Goodbye 👋")

            break

        answer = service.ask(question)

        print("\nECIP:\n")

        print(answer)


if __name__ == "__main__":
    main()