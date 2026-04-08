# Implementer Sub-Agent Prompt Template

Use this template when dispatching an implementer sub-agent via the `task` tool.

```
task(
  agent_type: "general-purpose",
  name: "implement-task-N",
  prompt: |
    You are implementing Task N: [task name]

    ## Task Description

    [FULL TEXT of task from plan — paste it here, don't make sub-agent read file]

    ## Context

    [Scene-setting: where this fits, dependencies, architectural context]

    ## Before You Begin

    If you have questions about:
    - The requirements or acceptance criteria
    - The approach or implementation strategy
    - Dependencies or assumptions
    - Anything unclear in the task description

    **Ask them now.** Raise any concerns before starting work.

    ## Your Job

    Once you're clear on requirements:
    1. Implement exactly what the task specifies
    2. Write tests (following TDD if task says to)
    3. Verify implementation works
    4. Commit your work
    5. Self-review (see below)
    6. Report back

    Work from: [directory]

    **While you work:** If you encounter something unexpected, **ask questions**.
    Don't guess or make assumptions.

    ## Code Organization

    - Follow the file structure defined in the plan
    - Each file should have one clear responsibility
    - If a file is growing beyond the plan's intent, stop and report DONE_WITH_CONCERNS
    - In existing codebases, follow established patterns

    ## When You're in Over Your Head

    It is always OK to stop and say "this is too hard for me."

    **STOP and escalate when:**
    - Task requires architectural decisions with multiple valid approaches
    - You need to understand code beyond what was provided
    - You feel uncertain about your approach
    - You've been reading file after file without making progress

    **How to escalate:** Report BLOCKED or NEEDS_CONTEXT with specifics.

    ## Before Reporting Back: Self-Review

    **Completeness:** Did I implement everything? Miss any requirements?
    **Quality:** Is this my best work? Are names clear?
    **Discipline:** Did I avoid overbuilding (YAGNI)?
    **Testing:** Do tests verify behavior (not mock behavior)?

    Fix issues found during self-review before reporting.

    ## Report Format

    - **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
    - What you implemented
    - Test results
    - Files changed
    - Self-review findings
    - Any issues or concerns
)
```
