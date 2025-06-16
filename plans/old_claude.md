## Phase Planning Requirement

Before proceeding with any new phase or significant feature implementation:
1. Create a detailed phase plan document outlining all tasks and implementation steps
2. Document the plan in the `plans/` directory with proper naming (e.g., `phase_3.md`)
3. Update the `plans/phases_overview.md` with any new phases or modifications
4. Get user approval for the plan before beginning implementation
5. Document implementation progress and decisions in the phase-specific file

### Task Implementation Guidelines

IMPORTANT: Each task within a phase should produce a testable CLI command:
- Tasks (e.g., 1.1, 1.2, 2.1) should each add a functional command
- Don't wait until phase completion to add commands
- Commands should demonstrate the specific functionality of that task
- Include the command syntax in the task plan (e.g., "Command: `nsp process-article <url>`")
- Test the command before marking the task complete
- Document example usage in commit messages
- **ALWAYS commit changes after completing a task or significant feature**
