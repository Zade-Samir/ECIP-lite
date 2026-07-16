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

        print(f"\nQ: {question}")
        print("─" * 60)
        print()

        t0 = time.monotonic()
        
        # Callback to print each token as it is generated
        def token_callback(token: str):
            print(token, end="", flush=True)

        response = coordinator.process(request, callback=token_callback)
        print()  # Add a newline when the stream finishes
        duration_ms = (time.monotonic() - t0) * 1000

        # Render only the citations, warnings, and execution footer
        rendered_footer = formatter.format_stream_footer(
            response=response,
            duration_ms=duration_ms
        )
        print(rendered_footer)


if __name__ == "__main__":
    main()