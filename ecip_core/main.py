from ecip_core.coordinator.query_coordinator import QueryCoordinator
from ecip_core.models.request import InferenceRequest


def main():

    coordinator = QueryCoordinator()

    print("=" * 60)
    print("🚀 Welcome to ECIP Lite")
    print("Type 'exit' to quit.")
    print("=" * 60)

    while True:

        question = input("\nAsk ECIP > ")

        if question.lower() in {"exit", "quit"}:
            print("Goodbye 👋")
            break

        request = InferenceRequest(
            question=question
        )

        response = coordinator.process(request)

        print("\nECIP:\n")
        print(response.answer)


if __name__ == "__main__":
    main()