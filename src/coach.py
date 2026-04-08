"""AI Copilot — Claude-powered hockey coaching from analysis data."""

import json
import os
from anthropic import Anthropic


SYSTEM_PROMPT = """You are an experienced ice hockey skills coach analyzing video
analysis data for an adult recreational player. You have access to computer vision
data including player tracking stats, pose estimation metrics, and session comparisons.

Your job is to:
1. Interpret the raw numbers into actionable hockey-specific feedback
2. Identify the most impactful areas for improvement
3. Give specific, practical drills or focus points for the next session
4. Be encouraging but honest — celebrate real progress, flag real issues
5. Relate metrics to on-ice performance (e.g., knee bend → power, lean → speed)

Keep feedback concise and prioritized. Lead with the 1-2 most important things,
then supporting details. Use hockey terminology naturally.

Context: The player skates in adult rec leagues and attends skills classes in Colorado.
"""


class HockeyCoach:
    """AI copilot that provides coaching feedback from analysis data."""

    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def review_game(self, game_stats, previous_game_stats=None):
        """Get coaching feedback on a game analysis."""
        message = "Here's my game analysis data:\n\n"
        message += f"```json\n{json.dumps(game_stats, indent=2)}\n```\n\n"

        if previous_game_stats:
            message += "And here's my previous game for comparison:\n\n"
            message += f"```json\n{json.dumps(previous_game_stats, indent=2)}\n```\n\n"
            message += ("Compare these two games. What improved? What got worse? "
                        "What should I focus on next?")
        else:
            message += ("Review my game stats. What stands out? "
                        "What should I work on in my next skills session?")

        return self._ask(message)

    def review_skills(self, skills_stats, previous_skills_stats=None):
        """Get coaching feedback on a skills session."""
        message = "Here's my skills session pose analysis:\n\n"
        message += f"```json\n{json.dumps(skills_stats, indent=2)}\n```\n\n"

        if previous_skills_stats:
            message += "Previous session for comparison:\n\n"
            message += f"```json\n{json.dumps(previous_skills_stats, indent=2)}\n```\n\n"
            message += ("Compare my form between sessions. Am I improving? "
                        "Where am I still struggling? Be specific about what "
                        "I should focus on at my next skills class.")
        else:
            message += ("Analyze my skating form. Key areas:\n"
                        "- Knee bend (ideal: 90-120 degrees for hockey stance)\n"
                        "- Forward lean (ideal: 30-45 degrees for speed/balance)\n"
                        "- Stride width and consistency\n\n"
                        "What do these numbers tell you about my skating? "
                        "What's the #1 thing I should work on?")

        return self._ask(message)

    def ask(self, question, context_stats=None):
        """Open-ended question to the coaching copilot."""
        message = question
        if context_stats:
            message += f"\n\nRelevant data:\n```json\n{json.dumps(context_stats, indent=2)}\n```"
        return self._ask(message)

    def improvement_plan(self, all_sessions):
        """Generate an improvement plan from multiple session results."""
        message = ("Here's my analysis data from multiple sessions, oldest to newest:\n\n")
        for i, session in enumerate(all_sessions):
            message += f"### Session {i + 1}\n"
            message += f"```json\n{json.dumps(session, indent=2)}\n```\n\n"

        message += ("Based on my progression across these sessions:\n"
                     "1. What has clearly improved?\n"
                     "2. What has plateaued or gotten worse?\n"
                     "3. Give me a focused 3-week practice plan with specific drills "
                     "targeting my weakest areas.\n"
                     "4. What should I ask my skills coach to focus on in our next class?")

        return self._ask(message)

    def _ask(self, message):
        """Send a message to the coaching AI."""
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        return response.content[0].text
