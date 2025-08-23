# Browser Agent

An AI-powered browser automation tool that can perform web tasks continuously while maintaining browser sessions and handling authentication. Record workflows and replay them later.

## Features

- 🤖 **Continuous Task Mode**: Ask for new tasks without restarting the browser
- 🔐 **Persistent Sessions**: Uses your Chrome profile with saved logins and cookies
- ⏸️ **Manual Credential Handling**: Pauses for you to enter login credentials manually
- 🌐 **Real Chrome Integration**: Uses your actual Chrome browser with all extensions
- 📝 **Interactive Task Assignment**: Get new tasks dynamically during execution
- 📼 **Flow Recording**: Save browser workflows for later replay
- 🔄 **Flow Replay**: Execute previously recorded workflows
- 🐛 **Debug Logging**: Optional detailed logging for troubleshooting

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browser:**
   ```bash
   uvx playwright install chromium --with-deps --no-shell
   ```

3. **Set up Chrome profile (optional but recommended):**
   ```bash
   mkdir -p ~/.config/browseruse/profiles
   cp -r ~/Library/Application\ Support/Google/Chrome ~/.config/browseruse/profiles/real-chrome
   ```

4. **Configure API key:**
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```
   
   Or copy `.env.example` to `.env` and add your key there.

5. **Optional - Enable debug logging:**
   ```bash
   export BROWSER_USE_LOGGING_LEVEL=debug
   ```

## Usage

### Basic Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Run the agent (interactive mode)
python browser_agent.py

# Record a workflow
python browser_agent.py --save-flow "my_workflow"

# Replay a workflow
python browser_agent.py --replay-flow "my_workflow"
```

### How It Works

#### Interactive Mode
1. **Agent starts** and waits for your first task
2. **Browser opens** using your Chrome profile (with saved logins)
3. **Execute task** - Agent performs the requested action
4. **Get new task** - Agent asks "What's next?" instead of closing
5. **Manual intervention** - Pause anytime to handle logins manually
6. **Continue** - Keep working in the same browser session

#### Flow Recording
1. **Start recording** with `--save-flow "workflow_name"`
2. **Enter task** when prompted (e.g., "Navigate to google.com")
3. **Agent executes** and records all actions, browser state, and results
4. **Flow saved** as JSON file in `flows/` directory

#### Flow Replay
1. **Start replay** with `--replay-flow "workflow_name"`
2. **Agent loads** the saved workflow from `flows/workflow_name.json`
3. **Recreates task** and executes the same actions
4. **Browser performs** the recorded workflow automatically

### Interactive Commands
- When agent asks for a new task, you can:
  - Give it another task: `"Check my LinkedIn notifications"`
  - Continue previous work: `"Click on the first result"`
  - End session: `"quit"` or just press Enter

## Examples

### Interactive Mode Tasks
- `"Go to LinkedIn and open my profile"`
- `"Navigate to GitHub and find trending Python repos"`
- `"Open Gmail and check for unread emails"`

### Flow Recording Examples
```bash
# Record a Google search workflow
python browser_agent.py --save-flow "google_search"
# Enter: "Go to google.com and search for Python tutorials"

# Record a LinkedIn check
python browser_agent.py --save-flow "linkedin_notifications"  
# Enter: "Go to LinkedIn and check notifications"

# Record email workflow
python browser_agent.py --save-flow "check_email"
# Enter: "Open Gmail and read the first unread email"
```

### Flow Replay Examples
```bash
# Replay the recorded workflows
python browser_agent.py --replay-flow "google_search"
python browser_agent.py --replay-flow "linkedin_notifications"
python browser_agent.py --replay-flow "check_email"
```

### Authentication-Heavy Sites
- `"Go to my bank website"` → Agent navigates, you handle login → `"Check account balance"`
- `"Open Facebook"` → You log in manually → `"Check recent messages"`

## Configuration

The agent supports several configuration options:

- **Chrome Profile**: Uses temporary profile at `/tmp/browser-agent-profile`
- **Flow Storage**: Saved flows are stored in `flows/` directory as JSON files
- **Timeout**: 100-second timeout for LLM responses
- **Logging**: Set `BROWSER_USE_LOGGING_LEVEL=debug` for detailed logs

### Flow File Structure
Recorded flows contain:
- **Action history**: Every action taken by the agent
- **Browser state**: Screenshots, URLs, page titles
- **Timestamps**: Execution timing for each step
- **Results**: Success/failure status and extracted content

## Troubleshooting

- **"Module not found"**: Make sure to activate the virtual environment
- **Chrome profile errors**: Browser profile conflicts - this is normal
- **Timeout issues**: Increase the timeout in `browser_agent.py` if needed
- **Authentication loops**: Use the manual pause feature to handle complex logins
- **Flow not found**: Check that the flow file exists in the `flows/` directory
- **Replay errors**: Recorded flows work best with the same browser profile and session state