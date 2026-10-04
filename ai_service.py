import os
from typing import List, Dict, Any

try:
    from backboard import BackboardClient
except ImportError:
    BackboardClient = None

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY", "")

# Cached assistant ID for reuse to ensure fast performance
_assistant_id = None

async def get_or_create_assistant(client: BackboardClient):
    global _assistant_id
    if _assistant_id:
        return _assistant_id
    try:
        assistants = await client.list_assistants()
        for a in getattr(assistants, "assistants", []):
            if getattr(a, "name", "") == "HealthTuner AI":
                _assistant_id = a.assistant_id
                return _assistant_id
    except Exception:
        pass

    system_prompt = (
        "You are HealthTuner's Chief Sports & Health Intelligence AI. Analyze the user's daily health and workout logs. "
        "Provide your analysis in exactly two distinct markdown sections:\n\n"
        "### Part 1: Comprehensive Behavioral Summary\n"
        "Analyze workload distribution, intensity, volume, consistency, nutrition/hydration trends, and recovery markers.\n\n"
        "### Part 2: Actionable Recommendations & Goal Suggestions\n"
        "Give 3-5 prioritized, concrete, and motivating health/fitness adjustments, recovery strategies, and targets for the remainder of the month."
    )
    assistant = await client.create_assistant(
        name="HealthTuner AI",
        description="Health & Workout Intelligence Analyst",
        system_prompt=system_prompt
    )
    _assistant_id = assistant.assistant_id
    return _assistant_id


async def generate_health_summary(logs: List[Dict[str, Any]], start_date: str, end_date: str) -> str:
    """
    Generates a structured health summary from logs using official Backboard.io SDK.
    If API key is missing or call fails, returns an intelligent local synthetic assessment
    to maintain seamless fallback and high reliability.
    """
    if not logs:
        return (
            "### Part 1: Performance Summary\n"
            f"No workout or health logs were recorded between {start_date} and {end_date}.\n\n"
            "### Part 2: Actionable Recommendations\n"
            "- Begin logging with even quick 'Easy' notes to build consistency.\n"
            "- Establish a base hydration target (2-3 Liters daily).\n"
            "- Schedule 20-30 minutes of low-impact walking or movement."
        )

    # Format user logs cleanly
    logs_formatted_text = ""
    for log in logs:
        logs_formatted_text += f"\n- Date: {log['date']} | Workload: {log['workload_type'].upper()}\n"
        content = log.get("content_json", {})
        if isinstance(content, dict):
            for k, v in content.items():
                if v:
                    logs_formatted_text += f"    * {k.replace('_', ' ').capitalize()}: {v}\n"
        else:
            logs_formatted_text += f"    * Details: {content}\n"

    user_prompt = (
        f"Health Logs from {start_date} to {end_date}:\n"
        f"{logs_formatted_text}\n\n"
        "Please provide your 2-part Health Summary:\n"
        "### Part 1: Comprehensive Behavioral Summary\n"
        "### Part 2: Actionable Recommendations & Goal Suggestions"
    )

    api_key = os.getenv("BACKBOARD_API_KEY", "").strip()

    if api_key and BackboardClient is not None:
        try:
            client = BackboardClient(api_key=api_key)
            assistant_id = await get_or_create_assistant(client)
            thread = await client.create_thread(assistant_id=assistant_id)
            response = await client.add_message(
                thread_id=thread.thread_id,
                content=user_prompt,
                stream=False
            )
            if response and getattr(response, "content", None):
                return response.content.strip()
        except Exception as e:
            print(f"Backboard.io SDK generation error: {e}")

    # Heuristic fallback if API key is not present or network issues occur
    total_days = len(logs)
    max_count = sum(1 for l in logs if l.get('workload_type') == 'maximum')
    med_count = sum(1 for l in logs if l.get('workload_type') == 'medium')
    easy_count = sum(1 for l in logs if l.get('workload_type') == 'easy')

    fallback_summary = (
        f"### Part 1: Comprehensive Behavioral Summary ({start_date} to {end_date})\n"
        f"Over the selected interval, you recorded **{total_days} total logged day(s)**:\n"
        f"- **Maximum Intensity Days:** {max_count}\n"
        f"- **Medium Balanced Days:** {med_count}\n"
        f"- **Easy / Recovery Days:** {easy_count}\n\n"
        f"Your logging demonstrates proactive engagement with your health routine. "
        + ("High workload density shows strong athletic drive." if max_count > 0 else "Consistent maintenance and steady effort are clearly visible.")
        + "\n\n"
        "### Part 2: Actionable Recommendations & Goal Suggestions\n"
        "1. **Recovery Calibration:** Ensure every high-output session is paired with targeted sleep (7.5-8.5 hrs) and active recovery.\n"
        "2. **Hydration & Electrolyte Timing:** Maintain consistent 2.5L+ hydration on all training days.\n"
        "3. **Progressive Micro-Goals:** Strive to maintain at least 3 active logged days per week through the remainder of the month.\n"
        "4. **Deload Strategy:** If consecutive Maximum days occur, insert an Easy recovery day to prevent central nervous system fatigue."
    )
    if not api_key:
        fallback_summary += "\n\n*(Note: Running with HealthTuner Built-in Heuristics Engine. Set `BACKBOARD_API_KEY` in `.env` to query live Backboard.io cloud models.)*"

    return fallback_summary
