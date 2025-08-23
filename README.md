# Browser Agent

A simple CLI tool that uses AI to control web browsers and perform tasks.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browser:
   ```bash
   uvx playwright install chromium --with-deps --no-shell
   ```

3. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```
   
   Or copy `.env.example` to `.env` and add your key there.

## Usage

Run the browser agent:
```bash
python browser_agent.py
```

The script will prompt you for a task, then use AI to control a browser to complete it.

## Examples

- "Go to google.com and search for Python tutorials"
- "Navigate to news.ycombinator.com and find the top story"
- "Visit github.com and find trending repositories"