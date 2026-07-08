import time
from ecip_core.coordinator.query_coordinator import QueryCoordinator
from ecip_core.models.request import InferenceRequest
from ecip_core.output.response_formatter import ResponseFormatter


def main():

    coordinator = QueryCoordinator()
    formatter = ResponseFormatter()

    print("=" * 60)
    print("🚀 Welcome to ECIP Lite")
    print("Type 'exit' to quit.")
    print("=" * 60)

    while True:

        question = input("\nAsk ECIP > ")

        if question.lower() in {"exit", "quit"}:
            print("Goodbye 👋")
            break

        request = InferenceRequest(question=question)

        t0 = time.monotonic()
        response = coordinator.process(request)
        duration_ms = (time.monotonic() - t0) * 1000

        formatted = formatter.format(
            response=response,
            question=question,
            duration_ms=duration_ms
        )

        print(formatted.rendered)


if __name__ == "__main__":
    main()