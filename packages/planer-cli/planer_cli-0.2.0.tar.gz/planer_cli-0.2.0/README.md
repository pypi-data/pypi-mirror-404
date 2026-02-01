# Planer CLI

CLI tool for Microsoft Planner - manage plans, tasks, and buckets from the command line.

## Installation

```bash
uv sync
```

## Configuration

### Option 1: Environment Variable

```bash
export PLANER_CLIENT_ID=<your-azure-ad-client-id>
```

### Option 2: Config File

```bash
planer config init
planer config edit
```

Config file location: `~/.config/planer-cli/config.yaml`

```yaml
# Required
client_id: "your-azure-ad-client-id"

# Optional
tenant_id: common
output_format: table
default_plan_id: ""
watch_interval: 60
log_level: INFO
```

### Azure AD App Registration

1. Go to Azure Portal > App Registrations
2. Create a new registration
3. Set Redirect URI to `https://login.microsoftonline.com/common/oauth2/nativeclient`
4. Enable "Allow public client flows"
5. Add API permissions (Delegated):
   - `Tasks.ReadWrite`
   - `Group.Read.All`
   - `User.Read`
   - `User.ReadBasic.All`

## Authentication

```bash
planer login      # Authenticate with Microsoft
planer status     # Check authentication status
planer logout     # Clear cached tokens
```

## Commands

### Tasks

```bash
# List your tasks
planer tasks my
planer tasks my --open              # Only open tasks
planer tasks my --done              # Only completed tasks
planer tasks my --overdue           # Overdue tasks
planer tasks my --due-today         # Due today
planer tasks my --this-week         # Due this week
planer tasks my --unassigned        # Unassigned tasks
planer tasks my --label 1           # Filter by label

# Sorting
planer tasks my --sort-by due-date
planer tasks my --sort-by priority
planer tasks my --sort-by title
planer tasks my --sort-by due-date --reverse

# Export
planer tasks my --export tasks.csv
planer tasks my --export tasks.json

# List tasks in plan/bucket
planer tasks list <plan-id>
planer tasks list-bucket <bucket-id>

# Get task details
planer tasks get <task-id>
planer tasks get -i                 # Interactive selection with fzf

# Create task
planer tasks create <plan-id> "Task title"
planer tasks create <plan-id> "Task title" --bucket-id <id>
planer tasks create <plan-id> "Task title" --due-date 2024-12-31
planer tasks create <plan-id> "Task title" --priority urgent
planer tasks create <plan-id> "Task title" --notes "Description here"

# Update task
planer tasks update <task-id> --title "New title"
planer tasks update <task-id> --progress 50
planer tasks update <task-id> --priority important
planer tasks update <task-id> --due-date 2024-12-31
planer tasks update <task-id> --bucket-id <id>
planer tasks update <task-id> --notes "Updated notes"
planer tasks update <task-id> --label 1 --label 2
planer tasks update <task-id> --remove-label 3
planer tasks update -i --title "New title"  # Interactive

# Complete task
planer tasks complete <task-id>
planer tasks complete -i            # Interactive selection

# Assign task
planer tasks assign <task-id> <user-id>

# Delete task
planer tasks delete <task-id>
planer tasks delete -i              # Interactive selection
```

### Batch Operations

```bash
# Complete all tasks
planer tasks complete-all --plan-id <id>
planer tasks complete-all --bucket-id <id>
planer tasks complete-all --plan-id <id> --yes  # Skip confirmation

# Move all tasks between buckets
planer tasks move-all --from-bucket <id> --to-bucket <id>

# Delete all tasks
planer tasks delete-all --plan-id <id>
planer tasks delete-all --bucket-id <id>
planer tasks delete-all --plan-id <id> --done-only  # Only completed
```

### Checklists

```bash
planer tasks checklist list <task-id>
planer tasks checklist add <task-id> "Checklist item"
planer tasks checklist check <task-id> <item-id>
planer tasks checklist uncheck <task-id> <item-id>
planer tasks checklist remove <task-id> <item-id>
```

### Quick-Add (Natural Language)

```bash
planer quick "Fix bug tomorrow"
planer quick "Review PR next Monday"
planer quick "Deploy on Friday" --plan-id <id>
planer quick "Write docs" --bucket-id <id>
```

Requires `default_plan_id` in config or `--plan-id` flag.

### Watch Mode

```bash
planer watch                    # Default 60s interval
planer watch --interval 30      # Custom interval
planer watch --no-notify        # Disable desktop notifications
```

Shows desktop notifications (macOS/Linux) when tasks are:
- Added
- Updated
- Completed

### Plans

```bash
planer plans my                         # Plans you have tasks in
planer plans list <group-id>            # Plans in a group
planer plans get <plan-id>              # Plan details
planer plans create <group-id> "Title"  # Create plan
planer plans update <plan-id> --title "New Title"
planer plans delete <plan-id>

# Labels
planer plans labels <plan-id>           # Show plan labels
planer plans set-label <plan-id> 1 "Bug"  # Set label name
```

### Buckets

```bash
planer buckets list <plan-id>
planer buckets get <bucket-id>
planer buckets create <plan-id> "Bucket Name"
planer buckets update <bucket-id> --name "New Name"
planer buckets delete <bucket-id>
```

### Groups

```bash
planer groups list              # List Microsoft 365 groups
planer groups get <group-id>    # Group details
```

### Users

```bash
planer users me                 # Show your user ID
planer users list               # List users in organization
planer users list --search Max  # Search by name or email
planer users get <user-id>      # Get user by ID or email
```

Use these IDs with `planer tasks assign <task-id> <user-id>`.

### Config

```bash
planer config init    # Create config template
planer config show    # Show current configuration
planer config edit    # Open in default editor
```

## Output Formats

```bash
planer tasks my --format json
planer -f json tasks my
```

## Shell Completions

```bash
# Bash
planer completions bash >> ~/.bashrc

# Zsh
planer completions zsh >> ~/.zshrc

# Fish
planer completions fish > ~/.config/fish/completions/planer.fish
```

## Interactive Selection (fzf)

Commands with `-i/--interactive` flag use fzf for task selection:

```bash
planer tasks get -i
planer tasks complete -i
planer tasks update -i --title "New title"
planer tasks delete -i
```

Requires [fzf](https://github.com/junegunn/fzf) to be installed:
```bash
brew install fzf      # macOS
apt install fzf       # Ubuntu/Debian
```

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=planer_cli --cov-report=term-missing
```

## License

MIT
