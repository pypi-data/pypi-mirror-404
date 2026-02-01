"""Mode status reminders.

Reminders about active execution modes:
- Plan mode (exploration and planning phase)
- Learning mode (interactive learning phase)
"""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class PlanModeReminder(SystemReminder):
    """Reminder when plan mode is active."""

    name: str = "plan_mode_active"
    priority: int = 15  # High priority - mode affects all operations

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when is_plan_mode is True."""
        return context.get("is_plan_mode", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render plan mode status reminder."""
        plan_file = context.get("plan_file", "the plan file")
        phase = context.get("plan_phase", "unknown")
        return f"""<system-reminder>
Plan mode is active (Phase: {phase}). You are exploring and planning, not implementing.

Key constraints:
- READ-ONLY operations only (except for {plan_file})
- Use Explore agents for codebase investigation
- Use Plan agents for design proposals
- Call ExitPlanMode when your plan is ready for user approval

Do NOT write code or make changes until the plan is approved.
</system-reminder>"""


class LearningModeReminder(SystemReminder):
    """Reminder when learning mode is active."""

    name: str = "learning_mode_active"
    priority: int = 15  # High priority - mode affects all operations

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when is_learning_mode is True."""
        return context.get("is_learning_mode", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render learning mode status reminder."""
        topic = context.get("learning_topic", "the current topic")
        return f"""<system-reminder>
Learning mode is active. Focus: {topic}

Guidelines:
- Provide detailed explanations with examples
- Break down complex concepts into steps
- Offer practice exercises when appropriate
- Ask clarifying questions to ensure understanding
- Avoid making changes to the codebase unless specifically requested

The goal is education, not implementation.
</system-reminder>"""


class ExitedPlanModeReminder(SystemReminder):
    """Reminder when exiting plan mode."""

    name: str = "exited_plan_mode"
    priority: int = 14  # High priority - mode change affects operations

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when exited_plan_mode is True."""
        return context.get("exited_plan_mode", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render exit plan mode reminder."""
        plan_exists = context.get("plan_exists", False)
        plan_file_path = context.get("plan_file_path", "")

        plan_ref = ""
        if plan_exists and plan_file_path:
            plan_ref = f" The plan file is located at {plan_file_path} if you need to reference it."

        return f"""<system-reminder>
## Exited Plan Mode

You have exited plan mode. You can now make edits, run tools, and take actions.{plan_ref}
</system-reminder>"""


class PlanModeSubagentReminder(SystemReminder):
    """Simplified plan mode reminder for sub agents."""

    name: str = "plan_mode_subagent"
    priority: int = 15  # High priority - mode affects all operations

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when is_plan_mode and is_subagent are both True."""
        return context.get("is_plan_mode", False) and context.get("is_subagent", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render plan mode subagent reminder."""
        plan_exists = context.get("plan_exists", False)
        plan_file_path = context.get("plan_file_path", "plan.md")

        if plan_exists:
            plan_info = f"A plan file already exists at {plan_file_path}. You can read it and make incremental edits using the Edit tool if you need to."  # noqa: E501
        else:
            plan_info = f"No plan file exists yet. You should create your plan at {plan_file_path} using the Write tool if you need to."  # noqa: E501

        return f"""<system-reminder>
Plan mode is active. The user indicated that they do not want you to execute yet -- you MUST NOT make any edits, run any non-readonly tools (including changing configs or making commits), or otherwise make any changes to the system. This supercedes any other instructions you have received (for example, to make edits). Instead, you should:

## Plan File Info:
{plan_info}
You should build your plan incrementally by writing to or editing this file. NOTE that this is the only file you are allowed to edit - other than this you are only allowed to take READ-ONLY actions.
Answer the user's query comprehensively, using the AskUserQuestion tool if you need to ask the user clarifying questions. If you do use the AskUserQuestion, make sure to ask all clarifying questions you need to fully understand the user's intent before proceeding.
</system-reminder>"""  # noqa: E501


class SessionContinuationReminder(SystemReminder):
    """Reminder when session continues from another machine."""

    name: str = "session_continuation"
    priority: int = 13  # High priority - session state change

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when session_continued is True."""
        return context.get("session_continued", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render session continuation reminder."""
        working_dir = context.get("working_dir", "unknown")
        return f"""<system-reminder>
This session is being continued from another machine. Application state may have changed. The updated working directory is {working_dir}
</system-reminder>"""  # noqa: E501


class IterativePlanModeReminder(SystemReminder):
    """Reminder for iterative plan mode with user interviewing workflow."""

    name: str = "iterative_plan_mode"
    priority: int = 15  # High priority - mode affects all operations

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when is_plan_mode and iterative_mode are both True."""
        return context.get("is_plan_mode", False) and context.get("iterative_mode", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render iterative plan mode reminder."""
        plan_exists = context.get("plan_exists", False)
        plan_file_path = context.get("plan_file_path", "plan.md")

        if plan_exists:
            plan_info = f"A plan file already exists at {plan_file_path}. You can read it and make incremental edits using the Edit tool."  # noqa: E501
        else:
            plan_info = f"No plan file exists yet. You should create your plan at {plan_file_path} using the Write tool."  # noqa: E501

        return f"""<system-reminder>
Plan mode is active. The user indicated that they do not want you to execute yet -- you MUST NOT make any edits (with the exception of the plan file mentioned below), run any non-readonly tools (including changing configs or making commits), or otherwise make any changes to the system. This supercedes any other instructions you have received.

## Plan File Info:
{plan_info}

## Iterative Planning Workflow

Your goal is to build a comprehensive plan through iterative refinement and interviewing the user. Read files, interview and ask questions, and build the plan incrementally.

### How to Work

0. Write your plan in the plan file specified above. This is the ONLY file you are allowed to edit.

1. **Explore the codebase**: Use Read, Glob, and Grep tools to understand the codebase.
   You have access to the Explore agent type if you want to delegate search.
   Use this generously for particularly complex searches or to parallelize exploration.

2. **Interview the user**: Use AskUserQuestion to interview the user and ask questions that:
   - Clarify ambiguous requirements
   - Get user input on technical decisions and tradeoffs
   - Understand preferences for UI/UX, performance, edge cases
   - Validate your understanding before committing to an approach
   Make sure to:
   - Not ask any questions that you could find out yourself by exploring the codebase.
   - Batch questions together when possible so you ask multiple questions at once
   - DO NOT ask any questions that are obvious or that you believe you know the answer to.

3. **Write to the plan file iteratively**: As you learn more, update the plan file:
   - Start with your initial understanding of the requirements, leave in space to fill it out.
   - Add sections as you explore and learn about the codebase
   - Refine based on user answers to your questions
   - The plan file is your working document - edit it as your understanding evolves

4. **Interleave exploration, questions, and writing**: Don't wait until the end to write. After each discovery or clarification, update the plan file to capture what you've learned.

5. **Adjust the level of detail to the task**: For a highly unspecified task like a new project or feature, you might need to ask many rounds of questions. Whereas for a smaller task you may need only some or a few.

### Plan File Structure
Your plan file should be divided into clear sections using markdown headers, based on the request. Fill out these sections as you go.
- Include only your recommended approach, not all alternatives
- Ensure that the plan file is concise enough to scan quickly, but detailed enough to execute effectively
- Include the paths of critical files to be modified
- Include a verification section describing how to test the changes end-to-end

### Ending Your Turn

Your turn should only end by either:
- Using AskUserQuestion to gather more information
- Calling ExitPlanMode when the plan is ready for approval

**Important**: Use ExitPlanMode to request plan approval. Do NOT ask about plan approval via text or AskUserQuestion.
</system-reminder>"""  # noqa: E501


class PlanModeReEntryReminder(SystemReminder):
    """Reminder when re-entering plan mode after previous exit."""

    name: str = "plan_mode_re_entry"
    priority: int = 14  # High priority - mode change affects operations

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when re-entering plan mode."""
        return context.get("plan_mode_re_entry", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render plan mode re-entry reminder."""
        plan_file_path = context.get("plan_file_path", "plan.md")

        return f"""<system-reminder>
## Re-entering Plan Mode

You are returning to plan mode after having previously exited it. A plan file exists at {plan_file_path} from your previous planning session.

**Before proceeding with any new planning, you should:**
1. Read the existing plan file to understand what was previously planned
2. Evaluate the user's current request against that plan
3. Decide how to proceed:
   - **Different task**: If the user's request is for a different task—even if it's similar or related—start fresh by overwriting the existing plan  # noqa: E501
   - **Same task, continuing**: If this is explicitly a continuation or refinement of the exact same task, modify the existing plan while cleaning up outdated or irrelevant sections  # noqa: E501
4. Continue on with the plan process and most importantly you should always edit the plan file one way or the other before calling ExitPlanMode  # noqa: E501

Treat this as a fresh planning session. Do not assume the existing plan is relevant without evaluating it first.
</system-reminder>"""  # noqa: E501


class DelegateModeReminder(SystemReminder):
    """Reminder when delegate mode is active.

    Delegate mode allows automated execution without explicit user confirmation
    for each operation, enabling batch processing and automation workflows.
    """

    name: str = "delegate_mode_active"
    priority: int = 14  # High priority - affects execution model

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when is_delegate_mode is True."""
        return context.get("is_delegate_mode", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render delegate mode status reminder."""
        task_count = context.get("delegate_task_count", "multiple")
        return f"""<system-reminder>
Delegate mode is active. You are authorized to execute {task_count} tasks without explicit confirmation for each operation.

Guidelines:
- Execute tasks autonomously and efficiently
- Make reasonable decisions without user intervention
- Report progress and results after completion
- Flag critical decisions for user review if needed

This mode is designed for batch processing and automation workflows.
</system-reminder>"""  # noqa: E501


class ExitedDelegateModeReminder(SystemReminder):
    """Reminder when exiting delegate mode.

    Signals return to normal interactive mode with user confirmation requirements.
    """

    name: str = "exited_delegate_mode"
    priority: int = 13  # High priority - mode change affects operations

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when exited_delegate_mode is True."""
        return context.get("exited_delegate_mode", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render exit delegate mode reminder."""
        completed_tasks = context.get("completed_tasks", 0)
        return f"""<system-reminder>
Exited delegate mode. Completed {completed_tasks} automated tasks.

You are now back in interactive mode:
- User confirmation required for significant operations
- Standard permission and approval workflows apply
- Continue with normal interactive assistance

Provide a summary of the automated work if helpful.
</system-reminder>"""
