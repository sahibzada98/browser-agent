#!/usr/bin/env python3
"""
Manual Flow Recorder - Capture user actions via CDP and convert to browser-use flows.
"""

import asyncio
import json
import time
from pathlib import Path
from browser_use import BrowserSession, BrowserProfile


class ManualRecorder:
    def __init__(self):
        self.cdp_events = []
        self.dom_snapshots = []
        self.recording = False
        self.session = None
    
    async def start_recording(self, flow_name: str, task_description: str):
        """Start manual recording session."""
        print(f"🎬 Starting manual recording for: {task_description}")
        
        # Create browser session
        profile = BrowserProfile(
            user_data_dir=f'/tmp/manual-recorder-{int(time.time())}',
            headless=False
        )
        self.session = BrowserSession(browser_profile=profile)
        
        # Start browser
        print("🚀 Starting browser...")
        await self.session.start()
        
        # Set up CDP event listeners
        await self._setup_cdp_listeners()
        
        # Start recording
        self.recording = True
        self.cdp_events = []
        
        print("=" * 50)
        print("📹 RECORDING STARTED")
        print("Perform your actions in the browser...")
        print("Press Enter in this terminal when done recording")
        print("=" * 50)
        
        # Wait for user to finish
        input()
        
        # Stop recording and convert
        await self.stop_recording(flow_name, task_description)
    
    async def _setup_cdp_listeners(self):
        """Set up CDP event listeners for user actions."""
        page = self.session.page
        
        # Listen for navigation
        await page.route("**/*", self._capture_navigation)
        
        # Listen for clicks and typing via CDP
        cdp = await page.context.new_cdp_session(page)
        
        # Enable DOM and Runtime domains
        await cdp.send("DOM.enable")
        await cdp.send("Runtime.enable")
        await cdp.send("Page.enable")
        
        # Listen for mouse clicks
        await cdp.send("Runtime.addBinding", {"name": "recordClick"})
        
        # Listen for input events
        await cdp.send("Runtime.addBinding", {"name": "recordInput"})
        
        # Inject JavaScript to capture user interactions
        await page.evaluate("""
            // Capture clicks
            document.addEventListener('click', (e) => {
                const rect = e.target.getBoundingClientRect();
                window.recordClick({
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2,
                    tagName: e.target.tagName,
                    text: e.target.textContent?.trim() || '',
                    id: e.target.id || '',
                    className: e.target.className || '',
                    timestamp: Date.now()
                });
            });
            
            // Capture input/typing
            document.addEventListener('input', (e) => {
                window.recordInput({
                    value: e.target.value,
                    tagName: e.target.tagName,
                    type: e.target.type || '',
                    id: e.target.id || '',
                    timestamp: Date.now()
                });
            });
        """)
        
        # Handle the bindings
        page.on("console", self._handle_console_event)
    
    async def _capture_navigation(self, route):
        """Capture navigation events."""
        url = route.request.url
        if self.recording:
            self.cdp_events.append({
                "type": "navigation",
                "url": url,
                "timestamp": time.time()
            })
        await route.continue_()
    
    def _handle_console_event(self, msg):
        """Handle console messages from injected JavaScript."""
        if not self.recording:
            return
            
        text = msg.text
        if "recordClick:" in text:
            data = json.loads(text.split("recordClick:")[1])
            self.cdp_events.append({
                "type": "click",
                "data": data,
                "timestamp": time.time()
            })
        elif "recordInput:" in text:
            data = json.loads(text.split("recordInput:")[1])
            self.cdp_events.append({
                "type": "input", 
                "data": data,
                "timestamp": time.time()
            })
    
    async def stop_recording(self, flow_name: str, task_description: str):
        """Stop recording and convert to browser-use flow."""
        self.recording = False
        
        print("🛑 Recording stopped")
        print(f"📊 Captured {len(self.cdp_events)} events")
        
        # Convert events to browser-use actions
        actions = self._convert_to_browser_use_actions()
        
        # Create flow structure
        flow_data = self._create_flow_structure(actions, task_description)
        
        # Save flow
        flows_dir = Path("flows")
        flows_dir.mkdir(exist_ok=True)
        
        flow_path = flows_dir / f"{flow_name}.json"
        with open(flow_path, 'w', encoding='utf-8') as f:
            json.dump(flow_data, f, indent=2)
        
        print(f"✅ Manual flow saved as: {flow_path}")
        print(f"   Original task: {task_description}")
        print(f"   Actions recorded: {len(actions)}")
        
        # Close browser
        if self.session:
            await self.session.close()
    
    def _convert_to_browser_use_actions(self):
        """Convert CDP events to browser-use actions."""
        actions = []
        
        # Group events by type and convert
        i = 0
        while i < len(self.cdp_events):
            event = self.cdp_events[i]
            
            if event["type"] == "navigation":
                actions.append({
                    "go_to_url": {
                        "url": event["url"],
                        "new_tab": False
                    }
                })
            
            elif event["type"] == "click":
                # Simple click action (index will be estimated)
                actions.append({
                    "click_element_by_index": {
                        "index": len(actions) + 1,  # Simple estimation
                        "while_holding_ctrl": False
                    }
                })
            
            elif event["type"] == "input":
                # Collect consecutive input events into one action
                text_value = event["data"]["value"]
                actions.append({
                    "input_text": {
                        "index": len(actions) + 1,  # Simple estimation  
                        "text": text_value,
                        "clear_existing": True
                    }
                })
            
            i += 1
        
        return actions
    
    def _create_flow_structure(self, actions, task_description):
        """Create browser-use compatible flow structure."""
        flow_data = {
            "original_user_task": task_description,
            "history": []
        }
        
        for i, action in enumerate(actions):
            step = {
                "model_output": {
                    "evaluation_previous_goal": "Manual recording step",
                    "memory": f"User manually performed action {i+1}",
                    "next_goal": f"Execute recorded action: {list(action.keys())[0]}",
                    "action": [action],
                    "thinking": f"Recorded from manual user demonstration - step {i+1}"
                },
                "result": [
                    {
                        "is_done": i == len(actions) - 1,
                        "error": None,
                        "include_extracted_content_only_once": False,
                        "include_in_memory": True
                    }
                ],
                "state": {
                    "url": "recorded_manually",
                    "title": "Manual Recording"
                },
                "metadata": {
                    "step_start_time": time.time() - len(actions) + i,
                    "step_end_time": time.time() - len(actions) + i + 1,
                    "step_number": i + 1
                }
            }
            flow_data["history"].append(step)
        
        return flow_data


async def main():
    """Main function for manual recording."""
    if len(asyncio.sys.argv) < 2:
        print("Usage: python manual_recorder.py <flow_name>")
        print("Example: python manual_recorder.py my_manual_flow")
        return
    
    flow_name = asyncio.sys.argv[1]
    task_description = input("Enter task description: ").strip()
    
    if not task_description:
        task_description = f"Manual recording: {flow_name}"
    
    recorder = ManualRecorder()
    await recorder.start_recording(flow_name, task_description)


if __name__ == "__main__":
    asyncio.run(main())