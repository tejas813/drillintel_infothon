from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


def generate_recommendation(
    risk_probability,
    risk_level,
    event_type=None,
    depth=None,
):
    """
    Generate a simple drilling recommendation
    based on predicted risk.
    """

    recommendations = []

    # ---------------------------------------------------------
    # LOW RISK
    # ---------------------------------------------------------

    if risk_level == "LOW":

        recommendations.append(
            "Continue drilling under normal operating conditions."
        )

        recommendations.append(
            "Continue monitoring real-time drilling parameters."
        )

    # ---------------------------------------------------------
    # MEDIUM RISK
    # ---------------------------------------------------------

    elif risk_level == "MEDIUM":

        recommendations.append(
            "Increase monitoring of critical drilling parameters."
        )

        recommendations.append(
            "Review flow rate, torque, WOB, pump and mud-weight trends."
        )

        recommendations.append(
            "Check nearby offset-well events for similar conditions."
        )

    # ---------------------------------------------------------
    # HIGH RISK
    # ---------------------------------------------------------

    elif risk_level == "HIGH":

        recommendations.append(
            "HIGH RISK detected — closely monitor drilling conditions."
        )

        recommendations.append(
            "Review flow-out, flow-in, torque, WOB and pump behaviour."
        )

        recommendations.append(
            "Compare current conditions with historical offset-well events."
        )

        recommendations.append(
            "Consider operational review before continuing the current activity."
        )

    # ---------------------------------------------------------
    # EVENT-SPECIFIC RECOMMENDATIONS
    # ---------------------------------------------------------

    if event_type:

        event = str(event_type).lower()

        if "pressure" in event:

            recommendations.append(
                "Pressure-related event detected: review pressure and ECD trends."
            )

        if "gas" in event:

            recommendations.append(
                "Gas-related event detected: review flow and mud-system indicators."
            )

        if "well_control" in event:

            recommendations.append(
                "Well-control indicator detected: review well-control parameters and procedures."
            )

        if "stuck_pipe" in event:

            recommendations.append(
                "Stuck-pipe indicator detected: review torque, WOB and drilling response."
            )

        if "lost_circulation" in event:

            recommendations.append(
                "Lost-circulation indicator detected: review flow balance and mud-loss indicators."
            )

    # ---------------------------------------------------------
    # DEPTH INFORMATION
    # ---------------------------------------------------------

    if depth is not None:

        recommendations.append(
            f"Current evaluated depth: {depth:.1f} m."
        )

    return recommendations


def main():

    print("=" * 70)
    print("eRTMAC-NWIS | DRILLING RECOMMENDATION ENGINE")
    print("=" * 70)

    # Example prediction
    risk_probability = 72.5
    risk_level = "HIGH"

    event_type = "pressure_event"
    depth = 3510.0

    recommendations = generate_recommendation(
        risk_probability=risk_probability,
        risk_level=risk_level,
        event_type=event_type,
        depth=depth,
    )

    print("\nRisk Probability:")
    print(f"{risk_probability:.2f}%")

    print("\nRisk Level:")
    print(risk_level)

    print("\nRecommendations:")

    for i, recommendation in enumerate(
        recommendations,
        start=1
    ):
        print(f"{i}. {recommendation}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
