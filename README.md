# Browser Agent

An AI-powered browser automation tool that can perform web tasks continuously while maintaining browser sessions and handling authentication.

## Features

- 🤖 **Continuous Task Mode**: Ask for new tasks without restarting the browser
- 🔐 **Persistent Sessions**: Uses your Chrome profile with saved logins and cookies
- ⏸️ **Manual Credential Handling**: Pauses for you to enter login credentials manually
- 🌐 **Real Chrome Integration**: Uses your actual Chrome browser with all extensions
- 📝 **Interactive Task Assignment**: Get new tasks dynamically during execution
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

# Run the agent
python browser_agent.py
```

### How It Works
1. **Agent starts** and waits for your first task
2. **Browser opens** using your Chrome profile (with saved logins)
3. **Execute task** - Agent performs the requested action
4. **Get new task** - Agent asks "What's next?" instead of closing
5. **Manual intervention** - Pause anytime to handle logins manually
6. **Continue** - Keep working in the same browser session

### Interactive Commands
- When agent asks for a new task, you can:
  - Give it another task: `"Check my LinkedIn notifications"`
  - Continue previous work: `"Click on the first result"`
  - End session: `"quit"` or just press Enter

## Examples

### Initial Tasks
- `"Go to LinkedIn and open my profile"`
- `"Navigate to GitHub and find trending Python repos"`
- `"Open Gmail and check for unread emails"`

### Follow-up Tasks
- `"Click on the first notification"`
- `"Scroll down and read the comments"`
- `"Open that repository in a new tab"`
- `"Compose a new email"`

### Authentication-Heavy Sites
- `"Go to my bank website"` → Agent navigates, you handle login → `"Check account balance"`
- `"Open Facebook"` → You log in manually → `"Check recent messages"`

## Configuration

The agent supports several configuration options:

- **Chrome Profile**: Automatically uses `~/.config/browseruse/profiles/real-chrome`
- **Browser Path**: Uses `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Timeout**: 100-second timeout for LLM responses
- **Logging**: Set `BROWSER_USE_LOGGING_LEVEL=debug` for detailed logs

## Troubleshooting

- **"Module not found"**: Make sure to activate the virtual environment
- **Chrome profile errors**: The copied profile may have lock files - this is normal
- **Timeout issues**: Increase the timeout in `browser_agent.py` if needed
- **Authentication loops**: Use the manual pause feature to handle complex logins