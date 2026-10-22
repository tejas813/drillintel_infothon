from rag_search import search_events


def generate_rag_response(query, top_k=5):
    results = search_events(query, top_k=top_k)

    if not results:
        return "No relevant historical drilling events found."

    print("\n" + "=" * 70)
    print("NWIS HISTORICAL EVENT INTELLIGENCE")
    print("=" * 70)

    print(f"\nQuery:\n{query}\n")

    print("Historical Similar Events:\n")

    for i, result in enumerate(results, start=1):
        print("-" * 70)
        print(f"Match #{i}")
        print(f"Similarity : {result['similarity_score']:.4f}")
        print(f"Well       : {result['well_id']}")
        print(f"Event      : {result['event_type']}")
        print(f"Depth      : {result['event_md']} m")
        print(f"Timestamp  : {result['timestamp']}")
        print(f"Description: {result['description']}")

    print("\n" + "=" * 70)
    print("NWIS DECISION SUPPORT")
    print("=" * 70)

    top_event = results[0]

    if top_event["event_type"] == "pressure_event":
        recommendation = (
            "Historical pressure-related events were found. "
            "Review pump pressure, flow behaviour, mud parameters and "
            "previous offset-well responses before continuing operations."
        )

    elif top_event["event_type"] == "gas_event":
        recommendation = (
            "Historical gas-related activity was found. "
            "Increase well-control monitoring and review flow and pressure trends."
        )

    elif top_event["event_type"] == "well_control":
        recommendation = (
            "Historical well-control activity was found. "
            "Perform enhanced well-control monitoring and review offset-well events."
        )

    else:
        recommendation = (
            "Similar historical drilling events were found. "
            "Review the matching offset-well operations and monitor drilling parameters."
        )

    print(f"\nRecommendation:\n{recommendation}")

    return results


if __name__ == "__main__":

    query = (
        "pressure event during drilling "
        "high pump pressure and flow changes"
    )

    generate_rag_response(query)
