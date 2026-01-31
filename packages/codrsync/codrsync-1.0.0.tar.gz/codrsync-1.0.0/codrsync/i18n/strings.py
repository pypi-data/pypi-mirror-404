"""
Built-in translation strings for codrsync.

Keys follow: module.context.identifier
Built-in languages: EN (English), PT_BR (Brazilian Portuguese)
"""

# ---------------------------------------------------------------------------
# English (default)
# ---------------------------------------------------------------------------
EN: dict[str, str] = {
    # === CLI: app-level ===
    "cli.app.help": "Turn any dev into jedi ninja codr",
    "cli.app.description": (
        "[bold cyan]codrsync[/bold cyan] - Turn any dev into jedi ninja codr\n\n"
        "AI-powered development orchestrator with guided development,\n"
        "interactive validation, and persistent context."
    ),
    "cli.version.help": "Show version and exit",
    "cli.version.show": "[bold cyan]codrsync[/bold cyan] version {version}",

    # === CLI: help panels ===
    "cli.panel.local": "Local (no AI needed)",
    "cli.panel.ai": "AI-powered",
    "cli.panel.config": "Configuration",

    # === CLI: status command ===
    "cli.status.help": "Show project status dashboard.\n\nWorks offline - reads local JSON files.",
    "cli.status.mini_help": "One-line status",
    "cli.status.prp_help": "Status of specific PRP",
    "cli.status.executive_help": "Executive summary",

    # === CLI: roadmap command ===
    "cli.roadmap.help": "Show project roadmap and timeline.\n\nWorks offline - reads local JSON files.",
    "cli.roadmap.current_help": "Show only current sprint",
    "cli.roadmap.epics_help": "Focus on epics",
    "cli.roadmap.mermaid_help": "Output as Mermaid diagram",
    "cli.roadmap.json_help": "Output as JSON",

    # === CLI: export command ===
    "cli.export.help": (
        "Export project to different formats.\n\n"
        "Formats:\n"
        "  - excel: Full report with all tabs (recommended)\n"
        "  - jira: CSV for Jira import\n"
        "  - trello: JSON for Trello import\n"
        "  - notion: Markdown for Notion\n"
        "  - json: Structured data for integrations\n\n"
        "Works offline - reads local JSON files."
    ),
    "cli.export.format_help": "Format: excel, jira, trello, notion, json",
    "cli.export.output_help": "Output directory",

    # === CLI: sprint commands ===
    "cli.sprint.help": "Manage development sprints",
    "cli.sprint.status_help": "Show current sprint status (default when no subcommand).",
    "cli.sprint.start_help": "Start a new sprint.",
    "cli.sprint.duration_help": "Sprint duration in weeks",
    "cli.sprint.goal_help": "Sprint goal",
    "cli.sprint.plan_help": "Interactive sprint planning.",
    "cli.sprint.review_help": "Sprint review - summarize deliveries.",
    "cli.sprint.retro_help": "Sprint retrospective - capture learnings.",
    "cli.sprint.close_help": "Close current sprint.",

    # === CLI: init command ===
    "cli.init.help": (
        "Initialize a new project with AI-guided kickstart.\n\n"
        "This is the main wizard that:\n"
        "- Gets to know you\n"
        "- Understands your project\n"
        "- Researches best practices\n"
        "- Creates project structure\n"
        "- Generates first PRP\n\n"
        "Requires: Claude Code or ANTHROPIC_API_KEY"
    ),
    "cli.init.name_help": "Project name",
    "cli.init.skip_research_help": "Skip market research",

    # === CLI: build command ===
    "cli.build.help": (
        "Execute development with AI guidance.\n\n"
        "Semi-autonomous mode: AI implements, pauses for important decisions.\n\n"
        "Requires: Claude Code or ANTHROPIC_API_KEY"
    ),
    "cli.build.prp_help": "PRP file to execute",
    "cli.build.story_help": "Specific story to work on",

    # === CLI: prp command ===
    "cli.prp.help": (
        "Manage PRPs (Product Requirement Prompts).\n\n"
        "Actions:\n"
        "  - list: Show all PRPs and their status\n"
        "  - generate: Create PRP from INITIAL.md\n"
        "  - validate: Start interactive validation\n"
        "  - execute: Execute approved PRP\n\n"
        "'list' works offline, others require AI."
    ),
    "cli.prp.action_help": "Action: list, generate, validate, execute",
    "cli.prp.file_help": "INITIAL.md or PRP file",

    # === CLI: auth command ===
    "cli.auth.help": (
        "Configure AI backend authentication.\n\n"
        "Options:\n"
        "  1. Use Claude Code (auto-detected)\n"
        "  2. Use Anthropic API key\n"
        "  3. Offline mode (limited features)"
    ),
    "cli.auth.show_help": "Show current auth status",
    "cli.auth.cloud_help": "Login to codrsync cloud (device flow)",
    "cli.auth.logout_help": "Logout from codrsync cloud",

    # === CLI: doctor command ===
    "cli.doctor.help": (
        "Check codrsync installation and configuration.\n\n"
        "Verifies:\n"
        "  - Python version\n"
        "  - Dependencies\n"
        "  - AI backend availability\n"
        "  - Project structure"
    ),

    # === Common ===
    "common.error": "[red]Error:[/red]",
    "common.warning": "[yellow]Warning:[/yellow]",
    "common.tip": "[dim]Tip:[/dim]",
    "common.note": "[yellow]Note:[/yellow]",
    "common.success": "[green]✓[/green]",
    "common.cancelled": "Cancelled.",
    "common.ai_required": (
        "[yellow]AI backend not configured.[/yellow]\n\n"
        "To use this command, you need one of:\n"
        "  1. Claude Code installed (recommended)\n"
        "  2. ANTHROPIC_API_KEY environment variable\n\n"
        "Run [bold]codrsync auth[/bold] to configure."
    ),
    "common.ai_required_title": "Authentication Required",
    "common.ai_required_short": "AI backend required. Run 'codrsync auth' to configure.",
    "common.no_project": (
        "No codrsync project found in current directory.\n"
        "Run [bold]codrsync init[/bold] to create a new project."
    ),

    # === Auth ===
    "auth.setup_title": "[bold cyan]codrsync Authentication Setup[/bold cyan]",
    "auth.backend_question": "How do you want to use codrsync?",
    "auth.claude_detected": "Use Claude Code (detected) - Recommended",
    "auth.claude_not_installed": "Use Claude Code (not installed)",
    "auth.claude_install_hint": "Install from: https://claude.ai/download",
    "auth.api_detected": "Use Anthropic API (key detected)",
    "auth.api_enter": "Use Anthropic API (enter key)",
    "auth.offline_option": "Offline mode (limited features)",
    "auth.enter_api_key": "Enter your Anthropic API key:",
    "auth.api_key_saved": "API key saved to ~/.codrsync/config.json",
    "auth.api_key_tip": "You can also set ANTHROPIC_API_KEY env variable",
    "auth.config_saved": "Configuration saved!",
    "auth.backend_label": "Backend:",
    "auth.offline_note": "Offline mode only supports:",
    "auth.offline_commands": "  - codrsync status\n  - codrsync roadmap\n  - codrsync export\n  - codrsync sprint",
    "auth.status_title": "codrsync Authentication Status",
    "auth.current_backend": "[bold]Current Backend:[/bold]",
    "auth.available_backends": "[bold]Available Backends:[/bold]",
    "auth.claude_code_label": "Claude Code:",
    "auth.anthropic_api_label": "Anthropic API:",
    "auth.config_label": "[bold]Config:[/bold]",
    "auth.installed": "Installed",
    "auth.not_found": "Not found",
    "auth.configured": "configured",
    "auth.not_set": "not set",
    "auth.warning_claude_fallback": "Claude Code not found, falling back...",
    "auth.warning_api_fallback": "API key not found, falling back...",

    # === Status ===
    "status.header": "PROJECT STATUS",
    "status.project_label": "Project:",
    "status.phase_label": "Phase:",
    "status.health_label": "Health:",
    "status.quick_stats": "QUICK STATS",
    "status.overall_progress": "Overall Progress",
    "status.epics_label": "Epics",
    "status.stories_label": "Stories",
    "status.total": "total",
    "status.done": "done",
    "status.active": "active",
    "status.pending": "pending",
    "status.current_focus": "CURRENT FOCUS",
    "status.active_prp": "Active PRP:",
    "status.status_label": "Status:",
    "status.blockers": "[red]Blockers:[/red]",
    "status.no_blockers": "[green]No blockers[/green]",
    "status.milestones": "MILESTONES",
    "status.recent_activity": "RECENT ACTIVITY",
    "status.footer": "Last updated: {timestamp} | Commands: /roadmap /sprint /export",
    "status.prp_not_found": "PRP '{prp_id}' not found",
    "status.executive_header": "EXECUTIVE SUMMARY",
    "status.status_report": "Status Report",
    "status.date_label": "Date:",
    "status.status_text": "STATUS:",
    "status.progress_label": "Progress:",
    "status.complete": "complete",
    "status.upcoming_milestones": "Upcoming Milestones:",
    "status.health_good": "GOOD",
    "status.health_warning": "WARNING",
    "status.health_at_risk": "AT RISK",
    "status.health_critical": "CRITICAL",
    "status.blocker_singular": "blocker",
    "status.blocker_plural": "blockers",
    "status.no_blockers_mini": "no blockers",
    "status.decisions_label": "Decisions:",
    "status.approved_label": "Approved:",

    # === Roadmap ===
    "roadmap.header": "ROADMAP",
    "roadmap.phases_header": "PHASES",
    "roadmap.epics_header": "EPICS",
    "roadmap.milestones_header": "MILESTONES",
    "roadmap.epic_col": "Epic",
    "roadmap.status_col": "Status",
    "roadmap.progress_col": "Progress",
    "roadmap.dependencies_col": "Dependencies",
    "roadmap.no_active_sprint": "[yellow]No active sprint.[/yellow]",
    "roadmap.start_sprint_hint": "Run [bold]codrsync sprint start[/bold] to begin a sprint.",
    "roadmap.sprint_header": "SPRINT {number}",
    "roadmap.period_label": "Period:",
    "roadmap.goal_label": "Goal:",
    "roadmap.stories_label": "Stories:",
    "roadmap.epics_overview": "EPICS OVERVIEW",
    "roadmap.dependencies_label": "Dependencies:",
    "roadmap.phase_discovery": "Discovery",
    "roadmap.phase_design": "Design",
    "roadmap.phase_development": "Development",
    "roadmap.phase_testing": "Testing",
    "roadmap.phase_deploy": "Deploy",
    "roadmap.phase_launch": "Launch",

    # === Sprint ===
    "sprint.no_active": "[yellow]No active sprint.[/yellow]",
    "sprint.start_hint": "Run [bold]codrsync sprint start[/bold] to begin a new sprint.",
    "sprint.status_header": "SPRINT {number} STATUS",
    "sprint.period": "Period: {start} - {end}",
    "sprint.goal": "Goal: {goal}",
    "sprint.goal_not_set": "Not set",
    "sprint.points_delivered": "Points: {done}/{total} delivered",
    "sprint.stories_label": "Stories:",
    "sprint.started": "Sprint {number} started!",
    "sprint.started_period": "Period: {start} - {end} ({duration} weeks)",
    "sprint.started_goal": "Goal: {goal}",
    "sprint.plan_next": "Next: Run [bold]codrsync sprint plan[/bold] to select stories.",
    "sprint.close_active_confirm": "Sprint {number} is active. Close it and start new?",
    "sprint.goal_prompt": "Sprint goal",
    "sprint.no_active_error": "No active sprint. Run [bold]codrsync sprint start[/bold] first.",
    "sprint.no_stories": "[yellow]No stories available in backlog.[/yellow]",
    "sprint.planning_header": "SPRINT PLANNING",
    "sprint.planning_info": "Sprint {number} | Goal: {goal}",
    "sprint.available_stories": "Available Stories:",
    "sprint.select_stories": "Select stories for this sprint:",
    "sprint.no_selection": "No stories selected.",
    "sprint.planned": "Sprint planned with {count} stories ({points} points)",
    "sprint.no_active_review": "No active sprint.",
    "sprint.review_header": "SPRINT {number} REVIEW",
    "sprint.delivered": "Delivered: {done}/{total} points ({completion}%)",
    "sprint.completed_label": "[green]Completed:[/green]",
    "sprint.not_completed_label": "[yellow]Not Completed:[/yellow]",
    "sprint.retro_header": "SPRINT {number} RETROSPECTIVE",
    "sprint.retro_went_well": "[green]What went well?[/green]",
    "sprint.retro_improve": "[yellow]What could improve?[/yellow]",
    "sprint.retro_actions": "[blue]Actions for next sprint:[/blue]",
    "sprint.retro_saved": "Retrospective saved!",
    "sprint.close_confirm": "Close Sprint {number}?",
    "sprint.moving_incomplete": "Moving {count} incomplete stories back to backlog",
    "sprint.closed": "Sprint {number} closed!",
    "sprint.velocity": "Velocity: {points} points",
    "sprint.average_velocity": "Average velocity: {avg} points",

    # === Export ===
    "export.unknown_format": "Unknown format '{format}'",
    "export.available_formats": "Available: excel, jira, trello, notion, json, all",
    "export.openpyxl_missing": "openpyxl not installed. Run: pip install openpyxl",
    "export.excel_exported": "Excel exported: {filename}",
    "export.jira_exported": "Jira CSV exported: {filename}",
    "export.jira_import_hint": "Import: Project Settings > External System Import > CSV",
    "export.trello_exported": "Trello JSON exported: {filename}",
    "export.trello_import_hint": "Import: Use Trello Power-Up or API",
    "export.notion_exported": "Notion Markdown exported: {filename}",
    "export.notion_import_hint": "Import: Copy/paste or drag into Notion",
    "export.json_exported": "JSON exported: {filename}",

    # === Kickstart (init) ===
    "kickstart.wizard_title": "[bold]codrsync[/bold] - Project Kickstart Wizard",
    "kickstart.wizard_intro": "Let's create something amazing together!",
    "kickstart.project_exists": "[yellow]A project already exists in this directory.[/yellow]",
    "kickstart.overwrite_confirm": "Start fresh? (will overwrite existing project)",
    "kickstart.phase1": "[bold]Phase 1: Getting to know you[/bold]",
    "kickstart.ask_name": "What's your name?",
    "kickstart.ask_level": "What's your programming experience level?",
    "kickstart.level_beginner": "Beginner (learning to code)",
    "kickstart.level_intermediate": "Intermediate (built some projects)",
    "kickstart.level_advanced": "Advanced (professional developer)",
    "kickstart.greeting": "Nice to meet you, {name}!",
    "kickstart.phase2": "[bold]Phase 2: Understanding your project[/bold]",
    "kickstart.ask_project_name": "What do you want to build? (project name)",
    "kickstart.ask_description": "Describe it briefly",
    "kickstart.default_description": "A web application",
    "kickstart.ask_type": "What type of project is this?",
    "kickstart.type_webapp": "Web App (frontend + backend)",
    "kickstart.type_api": "API (backend only)",
    "kickstart.type_saas": "SaaS (multi-tenant web app)",
    "kickstart.type_mobile": "Mobile App",
    "kickstart.type_bot": "Bot / Automation",
    "kickstart.type_cli": "CLI Tool",
    "kickstart.phase3": "[bold]Phase 3: Technical decisions[/bold]",
    "kickstart.ask_tech_choice": "How do you want to choose the tech stack?",
    "kickstart.tech_manual": "Let me choose (I have preferences)",
    "kickstart.tech_research": "Research best practices for me (recommended)",
    "kickstart.frontend_prompt": "Frontend",
    "kickstart.backend_prompt": "Backend",
    "kickstart.database_prompt": "Database",
    "kickstart.extras_prompt": "Extras (comma-separated)",
    "kickstart.researching": "Researching best practices...",
    "kickstart.research_complete": "Research complete!",
    "kickstart.research_failed": "Research failed: {error}",
    "kickstart.recommended_stack": "[bold]Recommended Stack:[/bold]",
    "kickstart.frontend_label": "Frontend:",
    "kickstart.backend_label": "Backend:",
    "kickstart.database_label": "Database:",
    "kickstart.extras_label": "Extras:",
    "kickstart.tech_stack_title": "Tech Stack",
    "kickstart.use_stack_confirm": "Use this stack?",
    "kickstart.phase4": "[bold]Phase 4: Creating project[/bold]",
    "kickstart.create_confirm": "Create project '{name}'?",
    "kickstart.created_structure": "Created project structure",
    "kickstart.created_manifest": "Created manifest.json",
    "kickstart.created_progress": "Created progress.json",
    "kickstart.created_context": "Created context-session.md",
    "kickstart.success": "[bold green]Project created successfully![/bold green]",
    "kickstart.success_title": "Success",
    "kickstart.next_steps": "[bold]Next steps:[/bold]",
    "kickstart.next_step_1": "1. Run [bold]codrsync status[/bold] to see project dashboard",
    "kickstart.next_step_2": "2. Run [bold]codrsync sprint start[/bold] to begin development",
    "kickstart.next_step_3": "3. Run [bold]codrsync build[/bold] to start implementing",

    # === Build ===
    "build.panel_title": "[bold]codrsync build[/bold] - AI-guided development",
    "build.panel_description": "Semi-autonomous mode: I'll implement and pause for important decisions.",
    "build.building_story": "Building story: {story_id}",
    "build.executing_prp": "Executing PRP: {prp_id}",
    "build.continuing_story": "Continuing story: {story_id}",
    "build.no_active_work": "[yellow]No active work found.[/yellow]",
    "build.start_sprint_hint": "Run [bold]codrsync sprint start[/bold] to begin a sprint.",
    "build.story_not_found": "Story '{story_id}' not found",
    "build.points_label": "Points:",
    "build.generating_plan": "[dim]Generating implementation plan...[/dim]",
    "build.prp_not_found": "PRP '{prp_id}' not found",
    "build.prp_not_approved": "PRP '{prp_id}' is not approved yet.",
    "build.prp_validate_hint": "Run [bold]codrsync prp validate {prp_id}[/bold] first.",
    "build.acceptance_criteria": "[bold]Acceptance Criteria:[/bold]",
    "build.mark_complete_confirm": "Mark this story as complete?",
    "build.story_completed": "Story {story_id} marked as complete!",
    "build.story_continued": "Story remains in progress. Run [bold]codrsync build[/bold] to continue.",
    "build.prp_reading": "Reading PRP and analyzing stories...",
    "build.prp_phase1": "[bold]Phase 1:[/bold] Generating execution plan...",
    "build.prp_phase2": "[bold]Phase 2:[/bold] Implementing stories...",
    "build.prp_plan_failed": "Could not parse execution plan from AI response.",
    "build.prp_fallback": "Falling back to full PRP execution mode.",
    "build.prp_plan_ready": "Execution plan ready for: {name}",
    "build.prp_stories_title": "Stories to Implement",
    "build.col_files": "Files",
    "build.col_points": "Points",
    "build.prp_total": "Total: {count} stories, {points} points",
    "build.prp_start_confirm": "Start implementing?",
    "build.prp_story_progress": "Story {current} of {total}",
    "build.prp_story_choice": "Action [continue/skip/stop]",
    "build.prp_stopped": "Build stopped. Progress has been saved.",
    "build.prp_story_skipped": "Skipped story {story_id}.",
    "build.prp_executing_full": "[dim]Executing full PRP in single-pass mode...[/dim]",
    "build.prp_summary": "Completed {completed} of {total} stories.",
    "build.prp_summary_remaining": "Remaining: {remaining} stories.",
    "build.prp_summary_title": "Build Summary",

    # === PRP ===
    "prp.unknown_action": "Unknown action '{action}'",
    "prp.available_actions": "Available: list, generate, validate, execute",
    "prp.no_project": "[yellow]No project found. Run 'codrsync init' first.[/yellow]",
    "prp.no_prps": "[yellow]No PRPs found.[/yellow]",
    "prp.create_hint": "Run [bold]codrsync prp generate INITIAL.md[/bold] to create one.",
    "prp.table_title": "PRPs",
    "prp.col_id": "ID",
    "prp.col_name": "Name",
    "prp.col_status": "Status",
    "prp.col_decisions": "Decisions",
    "prp.col_approved": "Approved",
    "prp.specify_initial": "Please specify an INITIAL.md file",
    "prp.usage_generate": "Usage: codrsync prp generate path/to/INITIAL.md",
    "prp.file_not_found": "File not found: {file}",
    "prp.generating_from": "Generating PRP from: {file}",
    "prp.specify_prp": "Please specify a PRP file",
    "prp.usage_validate": "Usage: codrsync prp validate PRPs/PRP-01-feature.md",
    "prp.ai_required": "AI backend required for PRP generation.",
    "prp.auth_hint": "Run [bold]codrsync auth[/bold] to configure.",
    # generate
    "prp.generate_reading_initial": "Reading initial requirements...",
    "prp.generate_calling_ai": "[dim]Generating PRP with AI...[/dim]",
    "prp.generate_failed": "PRP generation failed: {error}",
    "prp.generate_saved": "PRP saved to: {file}",
    "prp.generate_next_step": "Next: Run [bold]codrsync prp validate {prp_file}[/bold] to review decisions.",
    # validate
    "prp.validate_title": "[bold]PRP Interactive Validation[/bold]",
    "prp.validate_description": "I'll review the PRP and ask critical questions about architecture and scope.",
    "prp.validate_analyzing": "[dim]Analyzing PRP for critical decisions...[/dim]",
    "prp.validate_question": "Question",
    "prp.validate_answer_prompt": "Your answer (or 'done' to finish)",
    "prp.validate_done_default": "done",
    "prp.validate_complete_title": "Validation Complete",
    "prp.validate_finished": "Validation complete with {count} decisions recorded.",
    "prp.validate_approve_confirm": "Approve this PRP?",
    "prp.validate_approved": "PRP approved!",
    "prp.validate_build_hint": "Run [bold]codrsync build {prp_file}[/bold] to start implementation.",
    # execute
    "prp.execute_not_approved": "PRP '{file}' is not yet approved.",
    "prp.execute_anyway_confirm": "Execute anyway?",
    "prp.execute_delegating": "Delegating to build command...",

    # === Doctor ===
    "doctor.title": "[bold]codrsync doctor[/bold] v{version}",
    "doctor.col_check": "Check",
    "doctor.col_status": "Status",
    "doctor.col_details": "Details",
    "doctor.python_version": "Python version",
    "doctor.python_ok": "(OK)",
    "doctor.python_need": "(need 3.10+)",
    "doctor.claude_code": "Claude Code CLI",
    "doctor.not_installed_optional": "not installed (optional)",
    "doctor.anthropic_api_key": "Anthropic API Key",
    "doctor.configured": "configured",
    "doctor.not_set_optional": "not set (optional)",
    "doctor.active_backend": "Active AI Backend",
    "doctor.config_file": "Config file",
    "doctor.not_created": "not created yet",
    "doctor.project_detected": "Project detected",
    "doctor.no_project": "no project in current directory",
    "doctor.dependencies": "Dependencies",
    "doctor.all_installed": "all installed",
    "doctor.missing": "missing: {deps}",
    "doctor.ai_disabled_note": "AI features disabled. Run 'codrsync auth' to configure.",
    "doctor.init_tip": "Run 'codrsync init' to create a new project.",

    # === Onboarding ===
    "onboarding.welcome_title": "Welcome to codrsync!",
    "onboarding.welcome_body": (
        "[bold cyan]codrsync[/bold cyan] - Turn any dev into jedi ninja codr\n\n"
        "AI-powered development orchestrator with guided development,\n"
        "interactive validation, and persistent context."
    ),
    "onboarding.language_prompt": "Choose your language:",
    "onboarding.language_other": "Other (type language code)",
    "onboarding.enter_lang_code": "Enter language code (e.g. ja, ko, zh):",
    "onboarding.no_api_key_warning": (
        "Language '{lang}' requires translation via Anthropic API.\n"
        "No API key configured. Falling back to English.\n"
        "Run [bold]codrsync auth[/bold] to configure an API key."
    ),
    "onboarding.translating": "Translating to {lang}...",
    "onboarding.translation_failed": "Translation failed. Using English.",
    "onboarding.tour_title": "What codrsync does",
    "onboarding.tour_body": (
        "[bold]Local commands[/bold] (no AI needed):\n"
        "  [cyan]status[/cyan]   - Project dashboard\n"
        "  [cyan]roadmap[/cyan]  - Timeline and dependencies\n"
        "  [cyan]export[/cyan]   - Export to Excel/Jira/Trello/Notion\n"
        "  [cyan]sprint[/cyan]   - Manage sprints\n\n"
        "[bold]AI-powered commands[/bold]:\n"
        "  [cyan]init[/cyan]     - Initialize new project (wizard)\n"
        "  [cyan]build[/cyan]    - Execute development with AI guidance\n"
        "  [cyan]prp[/cyan]      - Generate or execute PRPs\n\n"
        "[bold]Configuration[/bold]:\n"
        "  [cyan]auth[/cyan]     - Configure AI backend\n"
        "  [cyan]doctor[/cyan]   - Check installation"
    ),
    "onboarding.ready_title": "Ready to start!",
    "onboarding.ready_body": (
        "Next steps:\n"
        "  1. [bold]codrsync auth[/bold]   - Configure AI backend\n"
        "  2. [bold]codrsync init[/bold]   - Create your first project\n"
        "  3. [bold]codrsync status[/bold] - View project dashboard"
    ),

    # === Next Steps ===
    "next.no_config": "Run [bold]codrsync auth[/bold] to configure your AI backend.",
    "next.no_project": "Run [bold]codrsync init[/bold] to create a new project.",
    "next.no_sprint": "Run [bold]codrsync sprint start[/bold] to begin a sprint.",
    "next.suggestion_title": "Suggested next step:",

    # === CLI: scan command ===
    "cli.scan.help": (
        "Scan current project to detect stack, docs, and integrations.\n\n"
        "Detects languages, frameworks, databases, infrastructure,\n"
        "and tools by analyzing file markers and config files.\n\n"
        "Works offline. Use --github or --docs for extended scanning."
    ),
    "cli.scan.path_help": "Project root path",
    "cli.scan.github_help": "Import issues, PRs, and workflows from GitHub",
    "cli.scan.docs_help": "Scan README, CLAUDE.md, and docs/ directory",
    "cli.scan.deep_help": "Generate AI-powered context document",

    # === CLI: connect command ===
    "cli.connect.help": (
        "Check and display integration status for external services.\n\n"
        "Connectors: supabase, vercel, digitalocean, mcp, github, tailwind.\n\n"
        "Works offline - checks CLIs, env vars, and config files."
    ),
    "cli.connect.service_help": "Specific service to check (default: all)",
    "cli.connect.path_help": "Project root path",

    # === Scan ===
    "scan.header": "PROJECT SCAN",
    "scan.scanning": "Scanning project at {path}...",
    "scan.languages_header": "Languages",
    "scan.frameworks_header": "Frameworks",
    "scan.databases_header": "Databases",
    "scan.infrastructure_header": "Infrastructure",
    "scan.tools_header": "Tools",
    "scan.no_detections": "No known markers detected.",
    "scan.detected": "Detected: {items}",
    "scan.docs_header": "DOCUMENTATION",
    "scan.docs_found": "Found: {files}",
    "scan.docs_none": "No documentation files found.",
    "scan.readme_preview": "README preview ({lines} lines)",
    "scan.github_header": "GITHUB",
    "scan.github_issues": "Open issues: {count}",
    "scan.github_prs": "Open PRs: {count}",
    "scan.github_workflows": "Workflows: {count}",
    "scan.github_not_available": "GitHub CLI (gh) not available.",
    "scan.github_not_repo": "Not a Git repository or no remote configured.",
    "scan.deep_header": "DEEP ANALYSIS",
    "scan.deep_generating": "Generating AI context document...",
    "scan.deep_saved": "Context saved to {path}",
    "scan.deep_failed": "Deep analysis failed: {error}",
    "scan.result_saved": "Scan result saved to {path}",
    "scan.package_json_deps": "Dependencies from package.json: {count}",
    "scan.pyproject_name": "Python project: {name}",
    "scan.summary": "Summary: {languages} languages, {frameworks} frameworks, {databases} databases",

    # === Connect ===
    "connect.header": "INTEGRATIONS STATUS",
    "connect.checking": "Checking integrations...",
    "connect.service_col": "Service",
    "connect.status_col": "Status",
    "connect.details_col": "Details",
    "connect.cli_col": "CLI",
    "connect.connected": "[green]connected[/green]",
    "connect.not_configured": "[yellow]not configured[/yellow]",
    "connect.skipped": "[dim]skipped[/dim]",
    "connect.error": "[red]error[/red]",
    "connect.cli_available": "[green]yes[/green]",
    "connect.cli_missing": "[dim]no[/dim]",
    "connect.cli_na": "[dim]n/a[/dim]",
    "connect.unknown_service": "Unknown service '{service}'. Available: {available}",
    "connect.result_saved": "Integration status saved to {path}",
    "connect.summary": "{connected} connected, {not_configured} not configured, {skipped} skipped",
    "connect.supabase_url": "URL: {url}",
    "connect.supabase_key_set": "API key: configured",
    "connect.supabase_key_missing": "API key: not set",
    "connect.vercel_project": "Project: {name}",
    "connect.vercel_no_project": "No Vercel project linked",
    "connect.github_repo": "Repo: {repo}",
    "connect.github_user": "User: {user}",
    "connect.github_no_auth": "Not authenticated",
    "connect.tailwind_version": "v{version}",
    "connect.tailwind_plugins": "Plugins: {plugins}",
    "connect.tailwind_no_config": "No tailwind config found",
    "connect.mcp_servers": "Servers: {count}",
    "connect.mcp_server_list": "Active: {servers}",
    "connect.mcp_none": "No MCP servers configured",
    "connect.mcp_suggestions": "Suggested MCPs for your stack: {suggestions}",
    "connect.digitalocean_detected": "doctl CLI detected",
    "connect.digitalocean_not_detected": "doctl CLI not installed",

    # === Init (expanded) ===
    "init.existing_detected": "Existing project detected!",
    "init.existing_description": (
        "This directory contains code files.\n"
        "You can import the existing project or start fresh."
    ),
    "init.choice_import": "Import existing project (scan & configure)",
    "init.choice_fresh": "Start fresh (kickstart wizard)",
    "init.importing": "Importing existing project...",
    "init.import_complete": "Project imported successfully!",
    "init.import_scan_step": "Scanning project structure...",
    "init.import_connect_step": "Checking integrations...",
    "init.import_context_step": "Generating project context...",

    # === Cloud Auth (Device Flow) ===
    "cloud_auth.requesting_code": "[dim]Requesting device code...[/dim]",
    "cloud_auth.request_failed": "Failed to request device code: {error}",
    "cloud_auth.enter_code": "Enter this code in your browser:",
    "cloud_auth.open_browser": "Opening: {url}",
    "cloud_auth.device_flow_title": "Device Authorization",
    "cloud_auth.waiting": "[dim]Waiting for authorization...[/dim]",
    "cloud_auth.logged_in": "Logged in as {name}!",
    "cloud_auth.tier": "Plan: {tier}",
    "cloud_auth.success_title": "Authenticated",
    "cloud_auth.expired": "Device code expired. Run 'codrsync auth --cloud' again.",
    "cloud_auth.denied": "Authorization denied.",
    "cloud_auth.timeout": "Timed out waiting for authorization.",
    "cloud_auth.logged_out": "Logged out. Credentials removed.",

    # === Cloud Storage ===
    "cloud_storage.not_authenticated": "Not authenticated. Run 'codrsync auth --cloud' first.",
    "cloud_storage.requesting_upload_url": "[dim]Requesting upload URL...[/dim]",
    "cloud_storage.uploading": "Uploading [cyan]{filename}[/cyan] ({size})",
    "cloud_storage.confirming": "[dim]Confirming upload...[/dim]",
    "cloud_storage.uploaded": "Uploaded: {key}",
    "cloud_storage.downloading": "Downloading [cyan]{filename}[/cyan]",
    "cloud_storage.downloaded": "Downloaded to: {path}",
    "cloud_storage.deleted": "Deleted: {key}",
    "cloud_storage.limit_exceeded": "Storage limit exceeded. {used} of {limit} used.",
    "cloud_storage.upgrade_hint": "Upgrade to {plan} for more storage: codrsync.dev/pricing",

    # === CLI: storage command ===
    "cli.storage.help": "Manage cloud storage.\n\nRequires authentication: codrsync auth --cloud",
    "cli.storage.upload_help": "Upload a file to cloud storage.",
    "cli.storage.download_help": "Download a file from cloud storage.",
    "cli.storage.list_help": "List files in cloud storage.",
    "cli.storage.delete_help": "Delete a file from cloud storage.",
    "cli.storage.usage_help": "Show storage usage and limits.",
    "cli.storage.file_help": "File path to upload",
    "cli.storage.key_help": "File key in storage",
    "cli.storage.output_help": "Output path for download",
    "cli.storage.folder_help": "Folder in storage",
    "cli.storage.public_help": "Make file publicly accessible",
}


# ---------------------------------------------------------------------------
# Brazilian Portuguese
# ---------------------------------------------------------------------------
PT_BR: dict[str, str] = {
    # === CLI: app-level ===
    "cli.app.help": "Transforme qualquer dev em jedi ninja codr",
    "cli.app.description": (
        "[bold cyan]codrsync[/bold cyan] - Transforme qualquer dev em jedi ninja codr\n\n"
        "Orquestrador de desenvolvimento com IA, desenvolvimento guiado,\n"
        "validacao interativa e contexto persistente."
    ),
    "cli.version.help": "Mostrar versao e sair",
    "cli.version.show": "[bold cyan]codrsync[/bold cyan] versao {version}",

    # === CLI: help panels ===
    "cli.panel.local": "Local (sem IA)",
    "cli.panel.ai": "Com IA",
    "cli.panel.config": "Configuracao",

    # === CLI: status command ===
    "cli.status.help": "Mostrar dashboard do projeto.\n\nFunciona offline - le arquivos JSON locais.",
    "cli.status.mini_help": "Status em uma linha",
    "cli.status.prp_help": "Status de PRP especifico",
    "cli.status.executive_help": "Resumo executivo",

    # === CLI: roadmap command ===
    "cli.roadmap.help": "Mostrar roadmap e timeline do projeto.\n\nFunciona offline - le arquivos JSON locais.",
    "cli.roadmap.current_help": "Mostrar apenas sprint atual",
    "cli.roadmap.epics_help": "Focar em epicos",
    "cli.roadmap.mermaid_help": "Saida como diagrama Mermaid",
    "cli.roadmap.json_help": "Saida como JSON",

    # === CLI: export command ===
    "cli.export.help": (
        "Exportar projeto para diferentes formatos.\n\n"
        "Formatos:\n"
        "  - excel: Relatorio completo com todas as abas (recomendado)\n"
        "  - jira: CSV para importacao no Jira\n"
        "  - trello: JSON para importacao no Trello\n"
        "  - notion: Markdown para Notion\n"
        "  - json: Dados estruturados para integracoes\n\n"
        "Funciona offline - le arquivos JSON locais."
    ),
    "cli.export.format_help": "Formato: excel, jira, trello, notion, json",
    "cli.export.output_help": "Diretorio de saida",

    # === CLI: sprint commands ===
    "cli.sprint.help": "Gerenciar sprints de desenvolvimento",
    "cli.sprint.status_help": "Mostrar status do sprint atual (padrao sem subcomando).",
    "cli.sprint.start_help": "Iniciar um novo sprint.",
    "cli.sprint.duration_help": "Duracao do sprint em semanas",
    "cli.sprint.goal_help": "Objetivo do sprint",
    "cli.sprint.plan_help": "Planejamento interativo do sprint.",
    "cli.sprint.review_help": "Review do sprint - resumir entregas.",
    "cli.sprint.retro_help": "Retrospectiva do sprint - capturar aprendizados.",
    "cli.sprint.close_help": "Encerrar sprint atual.",

    # === CLI: init command ===
    "cli.init.help": (
        "Inicializar novo projeto com wizard guiado por IA.\n\n"
        "O wizard principal que:\n"
        "- Te conhece\n"
        "- Entende seu projeto\n"
        "- Pesquisa melhores praticas\n"
        "- Cria estrutura do projeto\n"
        "- Gera primeiro PRP\n\n"
        "Requer: Claude Code ou ANTHROPIC_API_KEY"
    ),
    "cli.init.name_help": "Nome do projeto",
    "cli.init.skip_research_help": "Pular pesquisa de mercado",

    # === CLI: build command ===
    "cli.build.help": (
        "Executar desenvolvimento com orientacao de IA.\n\n"
        "Modo semi-autonomo: IA implementa, pausa para decisoes importantes.\n\n"
        "Requer: Claude Code ou ANTHROPIC_API_KEY"
    ),
    "cli.build.prp_help": "Arquivo PRP para executar",
    "cli.build.story_help": "Story especifica para trabalhar",

    # === CLI: prp command ===
    "cli.prp.help": (
        "Gerenciar PRPs (Product Requirement Prompts).\n\n"
        "Acoes:\n"
        "  - list: Mostrar todos os PRPs e status\n"
        "  - generate: Criar PRP a partir de INITIAL.md\n"
        "  - validate: Iniciar validacao interativa\n"
        "  - execute: Executar PRP aprovado\n\n"
        "'list' funciona offline, demais requerem IA."
    ),
    "cli.prp.action_help": "Acao: list, generate, validate, execute",
    "cli.prp.file_help": "INITIAL.md ou arquivo PRP",

    # === CLI: auth command ===
    "cli.auth.help": (
        "Configurar autenticacao do backend de IA.\n\n"
        "Opcoes:\n"
        "  1. Usar Claude Code (auto-detectado)\n"
        "  2. Usar chave da API Anthropic\n"
        "  3. Modo offline (funcoes limitadas)"
    ),
    "cli.auth.show_help": "Mostrar status atual de autenticacao",
    "cli.auth.cloud_help": "Login no codrsync cloud (device flow)",
    "cli.auth.logout_help": "Logout do codrsync cloud",

    # === CLI: doctor command ===
    "cli.doctor.help": (
        "Verificar instalacao e configuracao do codrsync.\n\n"
        "Verifica:\n"
        "  - Versao do Python\n"
        "  - Dependencias\n"
        "  - Disponibilidade do backend de IA\n"
        "  - Estrutura do projeto"
    ),

    # === Common ===
    "common.error": "[red]Erro:[/red]",
    "common.warning": "[yellow]Aviso:[/yellow]",
    "common.tip": "[dim]Dica:[/dim]",
    "common.note": "[yellow]Nota:[/yellow]",
    "common.success": "[green]✓[/green]",
    "common.cancelled": "Cancelado.",
    "common.ai_required": (
        "[yellow]Backend de IA nao configurado.[/yellow]\n\n"
        "Para usar este comando, voce precisa de:\n"
        "  1. Claude Code instalado (recomendado)\n"
        "  2. Variavel de ambiente ANTHROPIC_API_KEY\n\n"
        "Execute [bold]codrsync auth[/bold] para configurar."
    ),
    "common.ai_required_title": "Autenticacao Necessaria",
    "common.ai_required_short": "Backend de IA necessario. Execute 'codrsync auth' para configurar.",
    "common.no_project": (
        "Nenhum projeto codrsync encontrado no diretorio atual.\n"
        "Execute [bold]codrsync init[/bold] para criar um novo projeto."
    ),

    # === Auth ===
    "auth.setup_title": "[bold cyan]Configuracao de Autenticacao codrsync[/bold cyan]",
    "auth.backend_question": "Como voce quer usar o codrsync?",
    "auth.claude_detected": "Usar Claude Code (detectado) - Recomendado",
    "auth.claude_not_installed": "Usar Claude Code (nao instalado)",
    "auth.claude_install_hint": "Instale em: https://claude.ai/download",
    "auth.api_detected": "Usar API Anthropic (chave detectada)",
    "auth.api_enter": "Usar API Anthropic (inserir chave)",
    "auth.offline_option": "Modo offline (funcoes limitadas)",
    "auth.enter_api_key": "Digite sua chave da API Anthropic:",
    "auth.api_key_saved": "Chave da API salva em ~/.codrsync/config.json",
    "auth.api_key_tip": "Voce tambem pode definir a variavel ANTHROPIC_API_KEY",
    "auth.config_saved": "Configuracao salva!",
    "auth.backend_label": "Backend:",
    "auth.offline_note": "Modo offline suporta apenas:",
    "auth.offline_commands": "  - codrsync status\n  - codrsync roadmap\n  - codrsync export\n  - codrsync sprint",
    "auth.status_title": "Status de Autenticacao codrsync",
    "auth.current_backend": "[bold]Backend Atual:[/bold]",
    "auth.available_backends": "[bold]Backends Disponiveis:[/bold]",
    "auth.claude_code_label": "Claude Code:",
    "auth.anthropic_api_label": "API Anthropic:",
    "auth.config_label": "[bold]Config:[/bold]",
    "auth.installed": "Instalado",
    "auth.not_found": "Nao encontrado",
    "auth.configured": "configurada",
    "auth.not_set": "nao definida",
    "auth.warning_claude_fallback": "Claude Code nao encontrado, voltando ao fallback...",
    "auth.warning_api_fallback": "Chave da API nao encontrada, voltando ao fallback...",

    # === Status ===
    "status.header": "STATUS DO PROJETO",
    "status.project_label": "Projeto:",
    "status.phase_label": "Fase:",
    "status.health_label": "Saude:",
    "status.quick_stats": "ESTATISTICAS RAPIDAS",
    "status.overall_progress": "Progresso Geral",
    "status.epics_label": "Epicos",
    "status.stories_label": "Stories",
    "status.total": "total",
    "status.done": "prontos",
    "status.active": "ativos",
    "status.pending": "pendentes",
    "status.current_focus": "FOCO ATUAL",
    "status.active_prp": "PRP Ativo:",
    "status.status_label": "Status:",
    "status.blockers": "[red]Bloqueadores:[/red]",
    "status.no_blockers": "[green]Sem bloqueadores[/green]",
    "status.milestones": "MARCOS",
    "status.recent_activity": "ATIVIDADE RECENTE",
    "status.footer": "Atualizado: {timestamp} | Comandos: /roadmap /sprint /export",
    "status.prp_not_found": "PRP '{prp_id}' nao encontrado",
    "status.executive_header": "RESUMO EXECUTIVO",
    "status.status_report": "Relatorio de Status",
    "status.date_label": "Data:",
    "status.status_text": "STATUS:",
    "status.progress_label": "Progresso:",
    "status.complete": "completo",
    "status.upcoming_milestones": "Proximos Marcos:",
    "status.health_good": "BOM",
    "status.health_warning": "ATENCAO",
    "status.health_at_risk": "EM RISCO",
    "status.health_critical": "CRITICO",
    "status.blocker_singular": "bloqueador",
    "status.blocker_plural": "bloqueadores",
    "status.no_blockers_mini": "sem bloqueadores",
    "status.decisions_label": "Decisoes:",
    "status.approved_label": "Aprovado:",

    # === Roadmap ===
    "roadmap.header": "ROADMAP",
    "roadmap.phases_header": "FASES",
    "roadmap.epics_header": "EPICOS",
    "roadmap.milestones_header": "MARCOS",
    "roadmap.epic_col": "Epico",
    "roadmap.status_col": "Status",
    "roadmap.progress_col": "Progresso",
    "roadmap.dependencies_col": "Dependencias",
    "roadmap.no_active_sprint": "[yellow]Nenhum sprint ativo.[/yellow]",
    "roadmap.start_sprint_hint": "Execute [bold]codrsync sprint start[/bold] para iniciar um sprint.",
    "roadmap.sprint_header": "SPRINT {number}",
    "roadmap.period_label": "Periodo:",
    "roadmap.goal_label": "Objetivo:",
    "roadmap.stories_label": "Stories:",
    "roadmap.epics_overview": "VISAO GERAL DOS EPICOS",
    "roadmap.dependencies_label": "Dependencias:",
    "roadmap.phase_discovery": "Descoberta",
    "roadmap.phase_design": "Design",
    "roadmap.phase_development": "Desenvolvimento",
    "roadmap.phase_testing": "Testes",
    "roadmap.phase_deploy": "Deploy",
    "roadmap.phase_launch": "Lancamento",

    # === Sprint ===
    "sprint.no_active": "[yellow]Nenhum sprint ativo.[/yellow]",
    "sprint.start_hint": "Execute [bold]codrsync sprint start[/bold] para iniciar um novo sprint.",
    "sprint.status_header": "STATUS DO SPRINT {number}",
    "sprint.period": "Periodo: {start} - {end}",
    "sprint.goal": "Objetivo: {goal}",
    "sprint.goal_not_set": "Nao definido",
    "sprint.points_delivered": "Pontos: {done}/{total} entregues",
    "sprint.stories_label": "Stories:",
    "sprint.started": "Sprint {number} iniciado!",
    "sprint.started_period": "Periodo: {start} - {end} ({duration} semanas)",
    "sprint.started_goal": "Objetivo: {goal}",
    "sprint.plan_next": "Proximo: Execute [bold]codrsync sprint plan[/bold] para selecionar stories.",
    "sprint.close_active_confirm": "Sprint {number} esta ativo. Encerrar e iniciar novo?",
    "sprint.goal_prompt": "Objetivo do sprint",
    "sprint.no_active_error": "Nenhum sprint ativo. Execute [bold]codrsync sprint start[/bold] primeiro.",
    "sprint.no_stories": "[yellow]Nenhuma story disponivel no backlog.[/yellow]",
    "sprint.planning_header": "PLANEJAMENTO DO SPRINT",
    "sprint.planning_info": "Sprint {number} | Objetivo: {goal}",
    "sprint.available_stories": "Stories Disponiveis:",
    "sprint.select_stories": "Selecione stories para este sprint:",
    "sprint.no_selection": "Nenhuma story selecionada.",
    "sprint.planned": "Sprint planejado com {count} stories ({points} pontos)",
    "sprint.no_active_review": "Nenhum sprint ativo.",
    "sprint.review_header": "REVIEW DO SPRINT {number}",
    "sprint.delivered": "Entregue: {done}/{total} pontos ({completion}%)",
    "sprint.completed_label": "[green]Concluidos:[/green]",
    "sprint.not_completed_label": "[yellow]Nao Concluidos:[/yellow]",
    "sprint.retro_header": "RETROSPECTIVA DO SPRINT {number}",
    "sprint.retro_went_well": "[green]O que foi bem?[/green]",
    "sprint.retro_improve": "[yellow]O que pode melhorar?[/yellow]",
    "sprint.retro_actions": "[blue]Acoes para o proximo sprint:[/blue]",
    "sprint.retro_saved": "Retrospectiva salva!",
    "sprint.close_confirm": "Encerrar Sprint {number}?",
    "sprint.moving_incomplete": "Movendo {count} stories incompletas de volta ao backlog",
    "sprint.closed": "Sprint {number} encerrado!",
    "sprint.velocity": "Velocidade: {points} pontos",
    "sprint.average_velocity": "Velocidade media: {avg} pontos",

    # === Export ===
    "export.unknown_format": "Formato desconhecido '{format}'",
    "export.available_formats": "Disponiveis: excel, jira, trello, notion, json, all",
    "export.openpyxl_missing": "openpyxl nao instalado. Execute: pip install openpyxl",
    "export.excel_exported": "Excel exportado: {filename}",
    "export.jira_exported": "Jira CSV exportado: {filename}",
    "export.jira_import_hint": "Importar: Project Settings > External System Import > CSV",
    "export.trello_exported": "Trello JSON exportado: {filename}",
    "export.trello_import_hint": "Importar: Use Trello Power-Up ou API",
    "export.notion_exported": "Notion Markdown exportado: {filename}",
    "export.notion_import_hint": "Importar: Copie/cole ou arraste para o Notion",
    "export.json_exported": "JSON exportado: {filename}",

    # === Kickstart (init) ===
    "kickstart.wizard_title": "[bold]codrsync[/bold] - Wizard de Kickstart do Projeto",
    "kickstart.wizard_intro": "Vamos criar algo incrivel juntos!",
    "kickstart.project_exists": "[yellow]Um projeto ja existe neste diretorio.[/yellow]",
    "kickstart.overwrite_confirm": "Comecar do zero? (vai sobrescrever o projeto existente)",
    "kickstart.phase1": "[bold]Fase 1: Te conhecendo[/bold]",
    "kickstart.ask_name": "Qual e o seu nome?",
    "kickstart.ask_level": "Qual e seu nivel de experiencia em programacao?",
    "kickstart.level_beginner": "Iniciante (aprendendo a programar)",
    "kickstart.level_intermediate": "Intermediario (ja construiu alguns projetos)",
    "kickstart.level_advanced": "Avancado (desenvolvedor profissional)",
    "kickstart.greeting": "Prazer em te conhecer, {name}!",
    "kickstart.phase2": "[bold]Fase 2: Entendendo seu projeto[/bold]",
    "kickstart.ask_project_name": "O que voce quer construir? (nome do projeto)",
    "kickstart.ask_description": "Descreva brevemente",
    "kickstart.default_description": "Uma aplicacao web",
    "kickstart.ask_type": "Que tipo de projeto e este?",
    "kickstart.type_webapp": "Web App (frontend + backend)",
    "kickstart.type_api": "API (somente backend)",
    "kickstart.type_saas": "SaaS (web app multi-tenant)",
    "kickstart.type_mobile": "App Mobile",
    "kickstart.type_bot": "Bot / Automacao",
    "kickstart.type_cli": "Ferramenta CLI",
    "kickstart.phase3": "[bold]Fase 3: Decisoes tecnicas[/bold]",
    "kickstart.ask_tech_choice": "Como voce quer escolher a tech stack?",
    "kickstart.tech_manual": "Deixa eu escolher (tenho preferencias)",
    "kickstart.tech_research": "Pesquisar melhores praticas (recomendado)",
    "kickstart.frontend_prompt": "Frontend",
    "kickstart.backend_prompt": "Backend",
    "kickstart.database_prompt": "Banco de dados",
    "kickstart.extras_prompt": "Extras (separados por virgula)",
    "kickstart.researching": "Pesquisando melhores praticas...",
    "kickstart.research_complete": "Pesquisa concluida!",
    "kickstart.research_failed": "Pesquisa falhou: {error}",
    "kickstart.recommended_stack": "[bold]Stack Recomendada:[/bold]",
    "kickstart.frontend_label": "Frontend:",
    "kickstart.backend_label": "Backend:",
    "kickstart.database_label": "Banco de dados:",
    "kickstart.extras_label": "Extras:",
    "kickstart.tech_stack_title": "Tech Stack",
    "kickstart.use_stack_confirm": "Usar esta stack?",
    "kickstart.phase4": "[bold]Fase 4: Criando projeto[/bold]",
    "kickstart.create_confirm": "Criar projeto '{name}'?",
    "kickstart.created_structure": "Estrutura do projeto criada",
    "kickstart.created_manifest": "manifest.json criado",
    "kickstart.created_progress": "progress.json criado",
    "kickstart.created_context": "context-session.md criado",
    "kickstart.success": "[bold green]Projeto criado com sucesso![/bold green]",
    "kickstart.success_title": "Sucesso",
    "kickstart.next_steps": "[bold]Proximos passos:[/bold]",
    "kickstart.next_step_1": "1. Execute [bold]codrsync status[/bold] para ver o dashboard",
    "kickstart.next_step_2": "2. Execute [bold]codrsync sprint start[/bold] para iniciar o desenvolvimento",
    "kickstart.next_step_3": "3. Execute [bold]codrsync build[/bold] para comecar a implementar",

    # === Build ===
    "build.panel_title": "[bold]codrsync build[/bold] - Desenvolvimento guiado por IA",
    "build.panel_description": "Modo semi-autonomo: vou implementar e pausar para decisoes importantes.",
    "build.building_story": "Construindo story: {story_id}",
    "build.executing_prp": "Executando PRP: {prp_id}",
    "build.continuing_story": "Continuando story: {story_id}",
    "build.no_active_work": "[yellow]Nenhum trabalho ativo encontrado.[/yellow]",
    "build.start_sprint_hint": "Execute [bold]codrsync sprint start[/bold] para iniciar um sprint.",
    "build.story_not_found": "Story '{story_id}' nao encontrada",
    "build.points_label": "Pontos:",
    "build.generating_plan": "[dim]Gerando plano de implementacao...[/dim]",
    "build.prp_not_found": "PRP '{prp_id}' nao encontrado",
    "build.prp_not_approved": "PRP '{prp_id}' ainda nao foi aprovado.",
    "build.prp_validate_hint": "Execute [bold]codrsync prp validate {prp_id}[/bold] primeiro.",
    "build.acceptance_criteria": "[bold]Criterios de Aceitacao:[/bold]",
    "build.mark_complete_confirm": "Marcar esta story como completa?",
    "build.story_completed": "Story {story_id} marcada como completa!",
    "build.story_continued": "Story continua em progresso. Execute [bold]codrsync build[/bold] para continuar.",
    "build.prp_reading": "Lendo PRP e analisando stories...",
    "build.prp_phase1": "[bold]Fase 1:[/bold] Gerando plano de execucao...",
    "build.prp_phase2": "[bold]Fase 2:[/bold] Implementando stories...",
    "build.prp_plan_failed": "Nao foi possivel interpretar o plano de execucao da resposta da IA.",
    "build.prp_fallback": "Usando modo de execucao completa do PRP.",
    "build.prp_plan_ready": "Plano de execucao pronto para: {name}",
    "build.prp_stories_title": "Stories para Implementar",
    "build.col_files": "Arquivos",
    "build.col_points": "Pontos",
    "build.prp_total": "Total: {count} stories, {points} pontos",
    "build.prp_start_confirm": "Iniciar implementacao?",
    "build.prp_story_progress": "Story {current} de {total}",
    "build.prp_story_choice": "Acao [continue/skip/stop]",
    "build.prp_stopped": "Build interrompido. Progresso foi salvo.",
    "build.prp_story_skipped": "Story {story_id} pulada.",
    "build.prp_executing_full": "[dim]Executando PRP completo em modo unico...[/dim]",
    "build.prp_summary": "Completadas {completed} de {total} stories.",
    "build.prp_summary_remaining": "Restantes: {remaining} stories.",
    "build.prp_summary_title": "Resumo do Build",

    # === PRP ===
    "prp.unknown_action": "Acao desconhecida '{action}'",
    "prp.available_actions": "Disponiveis: list, generate, validate, execute",
    "prp.no_project": "[yellow]Nenhum projeto encontrado. Execute 'codrsync init' primeiro.[/yellow]",
    "prp.no_prps": "[yellow]Nenhum PRP encontrado.[/yellow]",
    "prp.create_hint": "Execute [bold]codrsync prp generate INITIAL.md[/bold] para criar um.",
    "prp.table_title": "PRPs",
    "prp.col_id": "ID",
    "prp.col_name": "Nome",
    "prp.col_status": "Status",
    "prp.col_decisions": "Decisoes",
    "prp.col_approved": "Aprovado",
    "prp.specify_initial": "Especifique um arquivo INITIAL.md",
    "prp.usage_generate": "Uso: codrsync prp generate caminho/para/INITIAL.md",
    "prp.file_not_found": "Arquivo nao encontrado: {file}",
    "prp.generating_from": "Gerando PRP a partir de: {file}",
    "prp.specify_prp": "Especifique um arquivo PRP",
    "prp.usage_validate": "Uso: codrsync prp validate PRPs/PRP-01-feature.md",
    "prp.ai_required": "Backend de IA necessario para geracao de PRP.",
    "prp.auth_hint": "Execute [bold]codrsync auth[/bold] para configurar.",
    # generate
    "prp.generate_reading_initial": "Lendo requisitos iniciais...",
    "prp.generate_calling_ai": "[dim]Gerando PRP com IA...[/dim]",
    "prp.generate_failed": "Geracao de PRP falhou: {error}",
    "prp.generate_saved": "PRP salvo em: {file}",
    "prp.generate_next_step": "Proximo: Execute [bold]codrsync prp validate {prp_file}[/bold] para revisar decisoes.",
    # validate
    "prp.validate_title": "[bold]Validacao Interativa de PRP[/bold]",
    "prp.validate_description": "Vou revisar o PRP e fazer perguntas criticas sobre arquitetura e escopo.",
    "prp.validate_analyzing": "[dim]Analisando PRP para decisoes criticas...[/dim]",
    "prp.validate_question": "Pergunta",
    "prp.validate_answer_prompt": "Sua resposta (ou 'pronto' para finalizar)",
    "prp.validate_done_default": "pronto",
    "prp.validate_complete_title": "Validacao Completa",
    "prp.validate_finished": "Validacao completa com {count} decisoes registradas.",
    "prp.validate_approve_confirm": "Aprovar este PRP?",
    "prp.validate_approved": "PRP aprovado!",
    "prp.validate_build_hint": "Execute [bold]codrsync build {prp_file}[/bold] para iniciar a implementacao.",
    # execute
    "prp.execute_not_approved": "PRP '{file}' ainda nao foi aprovado.",
    "prp.execute_anyway_confirm": "Executar mesmo assim?",
    "prp.execute_delegating": "Delegando para o comando build...",

    # === Doctor ===
    "doctor.title": "[bold]codrsync doctor[/bold] v{version}",
    "doctor.col_check": "Verificacao",
    "doctor.col_status": "Status",
    "doctor.col_details": "Detalhes",
    "doctor.python_version": "Versao do Python",
    "doctor.python_ok": "(OK)",
    "doctor.python_need": "(necessario 3.10+)",
    "doctor.claude_code": "Claude Code CLI",
    "doctor.not_installed_optional": "nao instalado (opcional)",
    "doctor.anthropic_api_key": "Chave da API Anthropic",
    "doctor.configured": "configurada",
    "doctor.not_set_optional": "nao definida (opcional)",
    "doctor.active_backend": "Backend de IA Ativo",
    "doctor.config_file": "Arquivo de config",
    "doctor.not_created": "ainda nao criado",
    "doctor.project_detected": "Projeto detectado",
    "doctor.no_project": "nenhum projeto no diretorio atual",
    "doctor.dependencies": "Dependencias",
    "doctor.all_installed": "todas instaladas",
    "doctor.missing": "faltando: {deps}",
    "doctor.ai_disabled_note": "Funcoes de IA desabilitadas. Execute 'codrsync auth' para configurar.",
    "doctor.init_tip": "Execute 'codrsync init' para criar um novo projeto.",

    # === Onboarding ===
    "onboarding.welcome_title": "Bem-vindo ao codrsync!",
    "onboarding.welcome_body": (
        "[bold cyan]codrsync[/bold cyan] - Transforme qualquer dev em jedi ninja codr\n\n"
        "Orquestrador de desenvolvimento com IA, desenvolvimento guiado,\n"
        "validacao interativa e contexto persistente."
    ),
    "onboarding.language_prompt": "Escolha seu idioma:",
    "onboarding.language_other": "Outro (digitar codigo do idioma)",
    "onboarding.enter_lang_code": "Digite o codigo do idioma (ex: ja, ko, zh):",
    "onboarding.no_api_key_warning": (
        "O idioma '{lang}' requer traducao via API Anthropic.\n"
        "Nenhuma chave de API configurada. Voltando para ingles.\n"
        "Execute [bold]codrsync auth[/bold] para configurar uma chave de API."
    ),
    "onboarding.translating": "Traduzindo para {lang}...",
    "onboarding.translation_failed": "Traducao falhou. Usando ingles.",
    "onboarding.tour_title": "O que o codrsync faz",
    "onboarding.tour_body": (
        "[bold]Comandos locais[/bold] (sem IA):\n"
        "  [cyan]status[/cyan]   - Dashboard do projeto\n"
        "  [cyan]roadmap[/cyan]  - Timeline e dependencias\n"
        "  [cyan]export[/cyan]   - Exportar para Excel/Jira/Trello/Notion\n"
        "  [cyan]sprint[/cyan]   - Gerenciar sprints\n\n"
        "[bold]Comandos com IA[/bold]:\n"
        "  [cyan]init[/cyan]     - Inicializar novo projeto (wizard)\n"
        "  [cyan]build[/cyan]    - Executar desenvolvimento com IA\n"
        "  [cyan]prp[/cyan]      - Gerar ou executar PRPs\n\n"
        "[bold]Configuracao[/bold]:\n"
        "  [cyan]auth[/cyan]     - Configurar backend de IA\n"
        "  [cyan]doctor[/cyan]   - Verificar instalacao"
    ),
    "onboarding.ready_title": "Pronto para comecar!",
    "onboarding.ready_body": (
        "Proximos passos:\n"
        "  1. [bold]codrsync auth[/bold]   - Configurar backend de IA\n"
        "  2. [bold]codrsync init[/bold]   - Criar seu primeiro projeto\n"
        "  3. [bold]codrsync status[/bold] - Ver dashboard do projeto"
    ),

    # === Next Steps ===
    "next.no_config": "Execute [bold]codrsync auth[/bold] para configurar seu backend de IA.",
    "next.no_project": "Execute [bold]codrsync init[/bold] para criar um novo projeto.",
    "next.no_sprint": "Execute [bold]codrsync sprint start[/bold] para iniciar um sprint.",
    "next.suggestion_title": "Proximo passo sugerido:",

    # === CLI: scan command ===
    "cli.scan.help": (
        "Escanear projeto atual para detectar stack, docs e integracoes.\n\n"
        "Detecta linguagens, frameworks, bancos de dados, infraestrutura\n"
        "e ferramentas analisando marcadores de arquivo e configs.\n\n"
        "Funciona offline. Use --github ou --docs para escaneamento estendido."
    ),
    "cli.scan.path_help": "Caminho raiz do projeto",
    "cli.scan.github_help": "Importar issues, PRs e workflows do GitHub",
    "cli.scan.docs_help": "Escanear README, CLAUDE.md e diretorio docs/",
    "cli.scan.deep_help": "Gerar documento de contexto com IA",

    # === CLI: connect command ===
    "cli.connect.help": (
        "Verificar e exibir status de integracoes com servicos externos.\n\n"
        "Conectores: supabase, vercel, digitalocean, mcp, github, tailwind.\n\n"
        "Funciona offline - verifica CLIs, variaveis de ambiente e configs."
    ),
    "cli.connect.service_help": "Servico especifico para verificar (padrao: todos)",
    "cli.connect.path_help": "Caminho raiz do projeto",

    # === Scan ===
    "scan.header": "SCAN DO PROJETO",
    "scan.scanning": "Escaneando projeto em {path}...",
    "scan.languages_header": "Linguagens",
    "scan.frameworks_header": "Frameworks",
    "scan.databases_header": "Bancos de Dados",
    "scan.infrastructure_header": "Infraestrutura",
    "scan.tools_header": "Ferramentas",
    "scan.no_detections": "Nenhum marcador conhecido detectado.",
    "scan.detected": "Detectado: {items}",
    "scan.docs_header": "DOCUMENTACAO",
    "scan.docs_found": "Encontrado: {files}",
    "scan.docs_none": "Nenhum arquivo de documentacao encontrado.",
    "scan.readme_preview": "Preview do README ({lines} linhas)",
    "scan.github_header": "GITHUB",
    "scan.github_issues": "Issues abertas: {count}",
    "scan.github_prs": "PRs abertos: {count}",
    "scan.github_workflows": "Workflows: {count}",
    "scan.github_not_available": "GitHub CLI (gh) nao disponivel.",
    "scan.github_not_repo": "Nao e um repositorio Git ou nenhum remote configurado.",
    "scan.deep_header": "ANALISE PROFUNDA",
    "scan.deep_generating": "Gerando documento de contexto com IA...",
    "scan.deep_saved": "Contexto salvo em {path}",
    "scan.deep_failed": "Analise profunda falhou: {error}",
    "scan.result_saved": "Resultado do scan salvo em {path}",
    "scan.package_json_deps": "Dependencias do package.json: {count}",
    "scan.pyproject_name": "Projeto Python: {name}",
    "scan.summary": "Resumo: {languages} linguagens, {frameworks} frameworks, {databases} bancos de dados",

    # === Connect ===
    "connect.header": "STATUS DAS INTEGRACOES",
    "connect.checking": "Verificando integracoes...",
    "connect.service_col": "Servico",
    "connect.status_col": "Status",
    "connect.details_col": "Detalhes",
    "connect.cli_col": "CLI",
    "connect.connected": "[green]conectado[/green]",
    "connect.not_configured": "[yellow]nao configurado[/yellow]",
    "connect.skipped": "[dim]ignorado[/dim]",
    "connect.error": "[red]erro[/red]",
    "connect.cli_available": "[green]sim[/green]",
    "connect.cli_missing": "[dim]nao[/dim]",
    "connect.cli_na": "[dim]n/a[/dim]",
    "connect.unknown_service": "Servico desconhecido '{service}'. Disponiveis: {available}",
    "connect.result_saved": "Status das integracoes salvo em {path}",
    "connect.summary": "{connected} conectados, {not_configured} nao configurados, {skipped} ignorados",
    "connect.supabase_url": "URL: {url}",
    "connect.supabase_key_set": "Chave da API: configurada",
    "connect.supabase_key_missing": "Chave da API: nao definida",
    "connect.vercel_project": "Projeto: {name}",
    "connect.vercel_no_project": "Nenhum projeto Vercel vinculado",
    "connect.github_repo": "Repo: {repo}",
    "connect.github_user": "Usuario: {user}",
    "connect.github_no_auth": "Nao autenticado",
    "connect.tailwind_version": "v{version}",
    "connect.tailwind_plugins": "Plugins: {plugins}",
    "connect.tailwind_no_config": "Nenhum config do tailwind encontrado",
    "connect.mcp_servers": "Servidores: {count}",
    "connect.mcp_server_list": "Ativos: {servers}",
    "connect.mcp_none": "Nenhum servidor MCP configurado",
    "connect.mcp_suggestions": "MCPs sugeridos para sua stack: {suggestions}",
    "connect.digitalocean_detected": "doctl CLI detectado",
    "connect.digitalocean_not_detected": "doctl CLI nao instalado",

    # === Init (expanded) ===
    "init.existing_detected": "Projeto existente detectado!",
    "init.existing_description": (
        "Este diretorio contem arquivos de codigo.\n"
        "Voce pode importar o projeto existente ou comecar do zero."
    ),
    "init.choice_import": "Importar projeto existente (escanear e configurar)",
    "init.choice_fresh": "Comecar do zero (wizard kickstart)",
    "init.importing": "Importando projeto existente...",
    "init.import_complete": "Projeto importado com sucesso!",
    "init.import_scan_step": "Escaneando estrutura do projeto...",
    "init.import_connect_step": "Verificando integracoes...",
    "init.import_context_step": "Gerando contexto do projeto...",

    # === Cloud Auth (Device Flow) ===
    "cloud_auth.requesting_code": "[dim]Solicitando codigo de dispositivo...[/dim]",
    "cloud_auth.request_failed": "Falha ao solicitar codigo de dispositivo: {error}",
    "cloud_auth.enter_code": "Digite este codigo no seu navegador:",
    "cloud_auth.open_browser": "Abrindo: {url}",
    "cloud_auth.device_flow_title": "Autorizacao de Dispositivo",
    "cloud_auth.waiting": "[dim]Aguardando autorizacao...[/dim]",
    "cloud_auth.logged_in": "Logado como {name}!",
    "cloud_auth.tier": "Plano: {tier}",
    "cloud_auth.success_title": "Autenticado",
    "cloud_auth.expired": "Codigo expirou. Execute 'codrsync auth --cloud' novamente.",
    "cloud_auth.denied": "Autorizacao negada.",
    "cloud_auth.timeout": "Tempo esgotado aguardando autorizacao.",
    "cloud_auth.logged_out": "Deslogado. Credenciais removidas.",

    # === Cloud Storage ===
    "cloud_storage.not_authenticated": "Nao autenticado. Execute 'codrsync auth --cloud' primeiro.",
    "cloud_storage.requesting_upload_url": "[dim]Solicitando URL de upload...[/dim]",
    "cloud_storage.uploading": "Enviando [cyan]{filename}[/cyan] ({size})",
    "cloud_storage.confirming": "[dim]Confirmando upload...[/dim]",
    "cloud_storage.uploaded": "Enviado: {key}",
    "cloud_storage.downloading": "Baixando [cyan]{filename}[/cyan]",
    "cloud_storage.downloaded": "Baixado para: {path}",
    "cloud_storage.deleted": "Deletado: {key}",
    "cloud_storage.limit_exceeded": "Limite de armazenamento excedido. {used} de {limit} usado.",
    "cloud_storage.upgrade_hint": "Faca upgrade para {plan} para mais espaco: codrsync.dev/pricing",

    # === CLI: storage command ===
    "cli.storage.help": "Gerenciar armazenamento na nuvem.\n\nRequer autenticacao: codrsync auth --cloud",
    "cli.storage.upload_help": "Enviar arquivo para o armazenamento na nuvem.",
    "cli.storage.download_help": "Baixar arquivo do armazenamento na nuvem.",
    "cli.storage.list_help": "Listar arquivos no armazenamento na nuvem.",
    "cli.storage.delete_help": "Deletar arquivo do armazenamento na nuvem.",
    "cli.storage.usage_help": "Mostrar uso e limites de armazenamento.",
    "cli.storage.file_help": "Caminho do arquivo para enviar",
    "cli.storage.key_help": "Chave do arquivo no armazenamento",
    "cli.storage.output_help": "Caminho de saida para download",
    "cli.storage.folder_help": "Pasta no armazenamento",
    "cli.storage.public_help": "Tornar arquivo publicamente acessivel",
}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
KEYS: list[str] = list(EN.keys())

BUILTIN_LANGUAGES: dict[str, dict[str, str]] = {
    "en": EN,
    "pt-br": PT_BR,
}
