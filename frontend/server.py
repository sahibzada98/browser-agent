#!/usr/bin/env python3
"""
Flask server to bridge frontend with browser_agent.py functionality
"""

import os
import asyncio
import json
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import signal

# Import our browser agent functions
import sys
sys.path.append('..')
from browser_agent import main as agent_main, replay_flow
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

class RecordingManager:
    def __init__(self):
        self.recording_process = None
        self.is_recording = False
        self.current_flow_name = None
        self.recording_thread = None

    def start_recording(self, flow_name, task_description):
        if self.is_recording:
            return False, "Already recording"

        self.is_recording = True
        self.current_flow_name = flow_name

        # Start recording in a separate thread
        self.recording_thread = threading.Thread(
            target=self._run_recording,
            args=(flow_name, task_description)
        )
        self.recording_thread.start()
        
        return True, "Recording started"

    def _run_recording(self, flow_name, task_description):
        try:
            # Run the browser agent with save-flow option
            cmd = [
                'python', '../browser_agent.py', 
                '--save-flow', flow_name
            ]
            
            # Set the task as input for the process
            self.recording_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            # Send the task description to the process
            stdout, stderr = self.recording_process.communicate(
                input=task_description + '\n'
            )
            
            print(f"Recording output: {stdout}")
            if stderr:
                print(f"Recording errors: {stderr}")
                
        except Exception as e:
            print(f"Error in recording: {e}")
        finally:
            self.is_recording = False
            self.recording_process = None

    def stop_recording(self):
        if not self.is_recording:
            return False, "Not recording"

        if self.recording_process:
            try:
                self.recording_process.terminate()
                self.recording_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.recording_process.kill()

        self.is_recording = False
        flow_name = self.current_flow_name
        self.current_flow_name = None
        
        return True, f"Recording stopped: {flow_name}"

    def get_status(self):
        return {
            'is_recording': self.is_recording,
            'flow_name': self.current_flow_name,
            'success': not self.is_recording,  # Success when not recording anymore
            'error': None
        }

# Global recording manager
recording_manager = RecordingManager()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/api/start-recording', methods=['POST'])
def start_recording():
    data = request.json
    flow_name = data.get('flow_name', '').strip()
    task_description = data.get('task_description', '').strip()

    if not flow_name or not task_description:
        return jsonify({'error': 'Flow name and task description are required'}), 400

    # Sanitize flow name
    flow_name = ''.join(c for c in flow_name if c.isalnum() or c in '_-')
    
    success, message = recording_manager.start_recording(flow_name, task_description)
    
    if success:
        return jsonify({'message': message, 'flow_name': flow_name})
    else:
        return jsonify({'error': message}), 400

@app.route('/api/stop-recording', methods=['POST'])
def stop_recording():
    success, message = recording_manager.stop_recording()
    
    if success:
        return jsonify({'message': message, 'flow_name': recording_manager.current_flow_name})
    else:
        return jsonify({'error': message}), 400

@app.route('/api/recording-status')
def recording_status():
    return jsonify(recording_manager.get_status())

@app.route('/api/flows')
def list_flows():
    flows_dir = Path('../flows')
    flows = []
    
    if flows_dir.exists():
        for flow_file in flows_dir.glob('*.json'):
            try:
                stat = flow_file.stat()
                
                # Try to read flow to get step count
                steps = 'Unknown'
                try:
                    with open(flow_file, 'r') as f:
                        flow_data = json.load(f)
                        history = flow_data.get('history', [])
                        steps = len(history)
                except:
                    pass

                flows.append({
                    'name': flow_file.stem,
                    'created': stat.st_mtime,
                    'size': stat.st_size,
                    'steps': steps
                })
            except Exception as e:
                print(f"Error reading flow {flow_file}: {e}")
                continue

    # Sort by creation time (newest first)
    flows.sort(key=lambda x: x['created'], reverse=True)
    
    return jsonify(flows)

@app.route('/api/replay-flow', methods=['POST'])
def start_replay():
    data = request.json
    flow_name = data.get('flow_name', '').strip()

    if not flow_name:
        return jsonify({'error': 'Flow name is required'}), 400

    # Check if flow exists
    flow_path = Path(f'../flows/{flow_name}.json')
    if not flow_path.exists():
        return jsonify({'error': f'Flow "{flow_name}" not found'}), 404

    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY not configured'}), 500

    try:
        # Start replay in a separate thread to avoid blocking
        def run_replay():
            asyncio.run(replay_flow(flow_name, api_key))

        replay_thread = threading.Thread(target=run_replay)
        replay_thread.start()
        
        return jsonify({'message': f'Replay started for "{flow_name}"'})
    
    except Exception as e:
        return jsonify({'error': f'Failed to start replay: {str(e)}'}), 500

@app.route('/api/flows/<flow_name>', methods=['DELETE'])
def delete_flow(flow_name):
    flow_path = Path(f'../flows/{flow_name}.json')
    
    if not flow_path.exists():
        return jsonify({'error': f'Flow "{flow_name}" not found'}), 404

    try:
        flow_path.unlink()
        return jsonify({'message': f'Flow "{flow_name}" deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to delete flow: {str(e)}'}), 500

def signal_handler(signum, frame):
    """Handle shutdown gracefully"""
    print("Shutting down server...")
    if recording_manager.is_recording:
        recording_manager.stop_recording()
    os._exit(0)

if __name__ == '__main__':
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Browser Agent Web UI starting...")
    print("📍 Open http://localhost:5001 in your browser")
    
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)