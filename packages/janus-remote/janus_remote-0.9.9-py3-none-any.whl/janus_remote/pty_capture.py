#!/usr/bin/env python3
"""
PTY Capture for Janus Remote

Wraps Claude CLI in a PTY and connects to local Janus via WebSocket
for voice-to-text paste and approval overlay support over SSH.
"""

import sys
import os
import pty
import select
import termios
import tty
from datetime import datetime
import fcntl
import time
import json
import re
import threading
import socket
import signal
import atexit

# WebSocket bridge port (must match Janus Electron)
JANUS_BRIDGE_PORT = 9473

# Hook-based approval file path (written by approval_hook.py)
JANUS_DATA_DIR = os.path.expanduser('~/.janus')
HOOK_PENDING_APPROVAL_FILE = os.path.join(JANUS_DATA_DIR, 'pending_approval.json')

def debug_log(msg):
    """Debug logging (file writing disabled)"""
    pass


# Lock for thread-safe terminal writes during raw mode
import threading
_output_lock = threading.Lock()

# Global reference to remote client for sending status via WebSocket
_remote_client = None


def safe_status(msg, color='208', force_terminal=False):
    """Send status message via WebSocket to Janus overlay, or fallback to terminal.

    When connected to Janus, sends status via WebSocket for overlay display.
    Falls back to terminal output during startup (before connection).
    Use force_terminal=True for critical messages that should always show in terminal.
    """
    global _remote_client

    # Try to send via WebSocket if connected (cleaner UI, no terminal corruption)
    if not force_terminal and _remote_client and _remote_client.connected and _remote_client.ws:
        try:
            import json
            _remote_client.ws.send(json.dumps({
                'type': 'status',
                'message': msg,
                'color': color
            }))
            return  # Successfully sent via WebSocket
        except:
            pass  # Fall through to terminal output

    # Fallback to terminal output (during startup or if WebSocket fails)
    with _output_lock:
        output = f"\r\033[K\033[38;5;{color}m[janus-remote]\033[0m {msg}\r\n"
        sys.stderr.write(output)
        sys.stderr.flush()


# Regex to match title escape sequences (for selective filtering)
TITLE_ESCAPE_PATTERN = re.compile(rb'\x1b\][012];[^\x07\x1b]*(?:\x07|\x1b\\)')

# Get Janus title for selective filtering - preserve our title, strip Claude's
JANUS_TITLE = os.environ.get('JANUS_TITLE', '')


def filter_title_sequences(data):
    """
    Selectively filter title escape sequences.
    - Preserve sequences containing JANUS_TITLE (so VSCode tab shows our title)
    - Strip other title sequences (from Claude) to prevent tab name hijacking
    """
    if not JANUS_TITLE:
        # No Janus title set - strip everything (original behavior)
        return TITLE_ESCAPE_PATTERN.sub(b'', data)

    janus_title_bytes = JANUS_TITLE.encode('utf-8')

    def replacer(match):
        seq = match.group(0)
        # Check if this sequence contains our Janus title - keep it!
        if janus_title_bytes in seq:
            return seq
        # Strip all other title sequences (Claude's)
        return b''

    return TITLE_ESCAPE_PATTERN.sub(replacer, data)


class TitleRefresher:
    """Periodically resends terminal title to keep VSCode tab name visible"""

    def __init__(self):
        self.running = True
        self.thread = None
        self.title = JANUS_TITLE

    def start(self):
        if not self.title:
            return  # No title to refresh

        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()

    def _refresh_loop(self):
        """Send title sequence every 5 seconds to maintain VSCode tab name"""
        while self.running:
            if self.title:
                # OSC 0 - Set window and icon title
                title_seq = f"\033]0;{self.title}\007"
                sys.stdout.write(title_seq)
                sys.stdout.flush()
            time.sleep(5)

    def stop(self):
        self.running = False

# Approval detection patterns - when Claude asks for permission
APPROVAL_PATTERNS = [
    r'❯\s*1\.\s*Yes',
    r'1\.\s*Yes\s*$',
    r'2\.\s*Yes,?\s*allow all',
    r'3\.\s*No,?\s*and tell',
    r'allow all.*during this session',
    r'tell Claude what to do differently',
    r'Allow\s+(this\s+)?(tool|action|command|operation)',
    r'Do you want to (allow|run|execute|proceed)',
    r'Press Enter to (allow|approve|continue|proceed)',
    r'\[y/n\]',
    r'\[Y/n\]',
    r'\[yes/no\]',
    r'Allow\?',
    r'Approve\?',
    r'Run\s+(this\s+)?(command|bash|script)',
    r'Execute\s+(this\s+)?(command|bash|script)',
    r'(Write|Create|Delete|Modify)\s+(to\s+)?file',
    r'Allow (writing|reading|creating|deleting)',
    r'(y/n/a)',
    r'\(y\)es.*\(n\)o',
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in APPROVAL_PATTERNS]


def get_janus_title():
    """Get session title from environment"""
    return os.environ.get('JANUS_TITLE', '')


def remove_ansi(text):
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class RemotePasteClient:
    """WebSocket client for bidirectional communication with local Janus"""

    def __init__(self, master_fd, port=JANUS_BRIDGE_PORT):
        global _remote_client
        self.master_fd = master_fd
        self.port = port
        self.ws = None
        self.running = True
        self.connected = False
        self.client_thread = None
        self.session_id = os.environ.get('JANUS_SESSION_ID', f"pty-{os.getpid()}-{int(time.time())}")
        self.pending_approval = None
        self.approval_id = 0
        # Set global reference so safe_status can send via WebSocket
        _remote_client = self

    def start(self):
        """Start the WebSocket client in a background thread"""
        self.client_thread = threading.Thread(target=self._run_client, daemon=True)
        self.client_thread.start()

    def _get_public_ip(self):
        """Get the server's public IP address for SSH config matching"""
        try:
            import urllib.request
            # Try multiple services in case one is down
            services = [
                'https://api.ipify.org',
                'https://ifconfig.me/ip',
                'https://icanhazip.com',
            ]
            for url in services:
                try:
                    with urllib.request.urlopen(url, timeout=3) as response:
                        ip = response.read().decode('utf-8').strip()
                        if ip:
                            return ip
                except:
                    continue
        except:
            pass
        return ''

    def _run_client(self):
        """Main client loop - connect and listen for messages"""
        try:
            import websocket
        except ImportError:
            safe_status("websocket-client not installed. Run: pip install websocket-client", '208')
            return

        while self.running:
            try:
                ws_url = f"ws://localhost:{self.port}"
                safe_status("Connecting to Janus bridge...", '208')

                self.ws = websocket.create_connection(ws_url, timeout=5)
                self.connected = True
                safe_status("\033[1mConnected to Janus bridge!\033[0m \033[38;5;141m<*>\033[0m", '82')

                # Register this session
                my_title = get_janus_title()
                system_hostname = socket.gethostname()

                # Get public IP for automatic SSH config matching
                public_ip = self._get_public_ip()

                register_msg = json.dumps({
                    'type': 'register',
                    'sessionId': self.session_id,
                    'title': my_title,
                    'hostname': system_hostname,
                    'publicIP': public_ip,
                    'capabilities': ['paste', 'approval']
                })
                self.ws.send(register_msg)
                if public_ip:
                    safe_status(f"Public IP: {public_ip}", '245')

                # Listen for messages
                while self.running and self.connected:
                    try:
                        self.ws.settimeout(1.0)
                        message = self.ws.recv()
                        if message:
                            self._handle_message(message)
                    except websocket.WebSocketTimeoutException:
                        try:
                            self.ws.send(json.dumps({'type': 'ping'}))
                        except:
                            break
                    except websocket.WebSocketConnectionClosedException:
                        safe_status("Connection closed", '208')
                        break
                    except Exception:
                        break

            except Exception as e:
                if self.running:
                    pass  # Silently retry
                self.connected = False

            if self.running:
                time.sleep(5)

    def _handle_message(self, message):
        """Handle incoming WebSocket message"""
        try:
            msg = json.loads(message)
            msg_type = msg.get('type')

            if msg_type == 'paste':
                text = msg.get('text', '')
                if text:
                    safe_status("Voice paste received", '82')
                    self._inject_text(text)

            elif msg_type == 'registered':
                pass  # Already printed connection message

            elif msg_type == 'approval_response':
                # Response from local Janus approval overlay
                action = msg.get('action', 'deny')
                response_approval_id = msg.get('approvalId')

                # Validate approval ID to prevent stale responses from auto-approving wrong tools
                if self.pending_approval:
                    pending_id = self.pending_approval.get('id')
                    if response_approval_id and pending_id and response_approval_id != pending_id:
                        safe_status(f"[!] Stale response ignored (got {response_approval_id}, expected {pending_id})", '208')
                        debug_log(f"[Approval] STALE response: response_id={response_approval_id}, pending_id={pending_id}")
                        return
                    self._inject_approval_response(action)
                else:
                    safe_status("[!] No pending approval - ignoring response", '208')
                    debug_log(f"[Approval] No pending approval for response: {action}")

            elif msg_type == 'auto_approve_pattern':
                # Add pattern to local whitelist file
                pattern = msg.get('pattern', {})
                if pattern:
                    self._add_auto_approve_pattern(pattern)

            elif msg_type == 'shutdown':
                # Janus is killing us - exit gracefully
                reason = msg.get('reason', 'unknown')
                safe_status(f"Shutdown received: {reason}", '196')
                self.running = False
                self.connected = False
                # Signal main process to exit
                os.kill(os.getpid(), signal.SIGTERM)

        except json.JSONDecodeError:
            pass

    def _inject_text(self, text):
        """Inject text directly into the PTY"""
        try:
            encoded = text.encode('utf-8')
            chunk_size = 256
            for i in range(0, len(encoded), chunk_size):
                chunk = encoded[i:i + chunk_size]
                os.write(self.master_fd, chunk)
                if len(encoded) > chunk_size:
                    time.sleep(0.02)

            time.sleep(0.15)
            os.write(self.master_fd, b'\r')
        except OSError as e:
            safe_status(f"Paste error: {e}", '196')

    def _inject_approval_response(self, action):
        """Inject approval response keystroke to Claude"""
        try:
            if action == 'approve':
                os.write(self.master_fd, b'1')
                time.sleep(0.05)
                os.write(self.master_fd, b'\r')
                safe_status("[OK] Approved", '82')
            elif action == 'approve_all':
                os.write(self.master_fd, b'2')
                time.sleep(0.05)
                os.write(self.master_fd, b'\r')
                safe_status("[OK] Approved all", '82')
            elif action == 'deny':
                os.write(self.master_fd, b'\x1b')  # Escape to cancel
                safe_status("[X] Denied", '208')
            elif action.startswith('deny:'):
                feedback = action[5:]
                os.write(self.master_fd, b'3')
                time.sleep(0.1)
                os.write(self.master_fd, b'\r')
                time.sleep(0.2)
                os.write(self.master_fd, feedback.encode('utf-8'))
                time.sleep(0.05)
                os.write(self.master_fd, b'\r')
                safe_status("[X] Denied with feedback", '208')
            else:
                os.write(self.master_fd, b'\x1b')

            self.pending_approval = None

        except OSError as e:
            safe_status(f"Approval inject error: {e}", '196')

    def _add_auto_approve_pattern(self, pattern):
        """Add pattern to local auto-approve whitelist file"""
        whitelist_path = os.path.join(JANUS_DATA_DIR, 'auto-approve-whitelist.json')
        whitelist = {'patterns': []}

        # Ensure directory exists
        os.makedirs(JANUS_DATA_DIR, exist_ok=True)

        # Load existing whitelist
        try:
            if os.path.exists(whitelist_path):
                with open(whitelist_path, 'r') as f:
                    whitelist = json.load(f)
        except Exception as e:
            debug_log(f"Error reading whitelist: {e}")

        # Check if pattern already exists
        exists = False
        for p in whitelist.get('patterns', []):
            if p.get('tool') != pattern.get('tool'):
                continue
            if pattern.get('command_prefix') and p.get('command_prefix') == pattern.get('command_prefix'):
                exists = True
                break
            if pattern.get('file_prefix') and p.get('file_prefix') == pattern.get('file_prefix'):
                exists = True
                break
            if pattern.get('any') and p.get('any'):
                exists = True
                break

        if not exists:
            whitelist.setdefault('patterns', []).append(pattern)
            try:
                with open(whitelist_path, 'w') as f:
                    json.dump(whitelist, f, indent=2)
                safe_status(f"[+] Auto-approve pattern added: {json.dumps(pattern)}", '82')
                debug_log(f"Added auto-approve pattern: {json.dumps(pattern)}")
                # Send ack back to Janus
                self._send_whitelist_ack('added', pattern, whitelist_path)
            except Exception as e:
                safe_status(f"Error saving whitelist: {e}", '196')
                debug_log(f"Error saving whitelist: {e}")
        else:
            safe_status(f"[=] Pattern already exists: {json.dumps(pattern)}", '245')
            debug_log(f"Pattern already exists: {json.dumps(pattern)}")
            self._send_whitelist_ack('exists', pattern, whitelist_path)

    def _send_whitelist_ack(self, status, pattern, whitelist_path):
        """Send acknowledgment back to Janus about whitelist update"""
        if not self.connected or not self.ws:
            return
        try:
            # Read current whitelist to show total patterns
            total_patterns = 0
            try:
                with open(whitelist_path, 'r') as f:
                    wl = json.load(f)
                    total_patterns = len(wl.get('patterns', []))
            except:
                pass

            self.ws.send(json.dumps({
                'type': 'whitelist_ack',
                'sessionId': self.session_id,
                'status': status,
                'pattern': pattern,
                'totalPatterns': total_patterns,
                'whitelistPath': whitelist_path
            }))
        except Exception as e:
            debug_log(f"Error sending whitelist ack: {e}")

    def send_approval_request(self, tool_name, context, raw_context=None, janus_title=None, session_title=None):
        """Send approval request to local Janus for overlay display"""
        if not self.connected or not self.ws:
            return

        self.approval_id += 1
        self.pending_approval = {
            'id': self.approval_id,
            'timestamp': datetime.now().isoformat(),
            'tool': tool_name,
            'context': context
        }

        # Get session title from env if not provided
        if not session_title:
            session_title = os.environ.get('JANUS_TITLE', '')

        try:
            self.ws.send(json.dumps({
                'type': 'approval_request',
                'sessionId': self.session_id,
                'approvalId': self.approval_id,
                'tool': tool_name,
                'context': context,
                'rawContext': raw_context or context,
                'hostname': socket.gethostname(),
                'sessionTitle': session_title,
                'janusTitle': janus_title or ''
            }))
            safe_status(f"[!] Approval request sent -> {tool_name}", '141')
        except Exception:
            pass

    def clear_pending_approval(self):
        """Clear pending approval (user handled it manually) and notify Janus"""
        if self.pending_approval and self.connected and self.ws:
            try:
                self.ws.send(json.dumps({
                    'type': 'approval_cleared',
                    'sessionId': self.session_id,
                    'approvalId': self.pending_approval.get('id'),
                    'reason': 'manual'
                }))
            except Exception:
                pass
        self.pending_approval = None

    def stop(self):
        """Stop the client"""
        self.running = False
        self.connected = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass


class ApprovalDetector:
    """Detects approval requests in Claude output"""

    def __init__(self, remote_client):
        self.remote_client = remote_client
        self.recent_lines = []
        self.recent_raw_lines = []  # Keep raw lines for better parsing
        self.last_detection_time = 0
        self.detection_cooldown = 0.5

    def add_line(self, line):
        """Add a line and check for approval patterns"""
        cleaned = remove_ansi(line).strip()
        if not cleaned:
            return

        self.recent_lines.append(cleaned)
        self.recent_raw_lines.append(line)  # Keep raw version too
        if len(self.recent_lines) > 500:
            self.recent_lines = self.recent_lines[-400:]
            self.recent_raw_lines = self.recent_raw_lines[-400:]

        # Check for completion markers - clear pending
        if self.remote_client.pending_approval:
            if '✓' in cleaned or '✗' in cleaned:
                self.remote_client.clear_pending_approval()
                return

        # Check for approval request
        if self._is_approval_request(cleaned):
            current_time = time.time()
            if (current_time - self.last_detection_time) >= self.detection_cooldown:
                if not self.remote_client.pending_approval:
                    # If hook pending file exists, let HookApprovalWatcher handle it (has better data)
                    if os.path.exists(HOOK_PENDING_APPROVAL_FILE):
                        debug_log("[PTY] Deferring to hook watcher - pending file exists")
                        return
                    self.last_detection_time = current_time
                    tool_name, context = self._extract_tool_info()
                    self.remote_client.send_approval_request(tool_name, context, self.recent_lines)

    def _is_approval_request(self, line):
        """Check if line matches approval patterns"""
        for pattern in COMPILED_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def _extract_tool_info(self):
        """Extract tool/command info - everything from ⏺ until the approval prompt"""
        tool_name = None
        tool_details = []
        tool_header = None

        debug_log(f"[EXTRACT] Starting _extract_tool_info, recent_lines count: {len(self.recent_lines)}, recent_raw_lines count: {len(self.recent_raw_lines)}")

        # All known tool names
        known_tools = ['Bash', 'Edit', 'Write', 'Read', 'Glob', 'Grep', 'Task', 'TodoWrite',
                       'WebSearch', 'WebFetch', 'LSP', 'NotebookEdit', 'mcp_']

        # Stop patterns - these indicate end of content
        stop_patterns = ['❯', '1. Yes', '2. Yes', '3. No', 'Do you want', 'proceed?', '2. Type here']
        # Skip patterns - junk we don't want
        skip_patterns = ['⎿', 'esc to', '{…)', '…)', '(…', 'Running...']

        # Find the LAST tool block (starts with ⏺)
        tool_start_idx = -1
        for i, raw_line in enumerate(self.recent_raw_lines):
            line = remove_ansi(raw_line).strip()
            if '⏺' in line:
                tool_start_idx = i
                tool_header = line
                debug_log(f"[EXTRACT] Found tool header at index {i}: '{line}'")
                # Extract tool name from header
                for known in known_tools:
                    if known in line:
                        tool_name = known
                        break

        if tool_start_idx == -1:
            debug_log(f"[EXTRACT] No tool header found (⏺), returning last 10 lines")
            return 'Unknown', self.recent_lines[-10:]

        # For Bash, try to extract command from header line
        if tool_name == 'Bash' and tool_header:
            bash_match = re.search(r'Bash\s*\(([^)]+)\)', tool_header)
            if bash_match:
                cmd = bash_match.group(1).strip()
                if cmd:
                    tool_details.append(f"Command: {cmd}")

        # Capture from tool start until approval prompt
        in_box = False
        capture_all = tool_name in ['Edit', 'Write', 'Bash']  # These need full content

        for raw_line in self.recent_raw_lines[tool_start_idx:]:
            line_raw = remove_ansi(raw_line)
            line = line_raw.strip()

            if not line:
                if capture_all and tool_details:
                    tool_details.append('')  # Preserve empty lines in code
                continue

            # Stop at approval prompt
            if any(stop in line for stop in stop_patterns):
                break

            # Skip junk lines (but not in capture_all mode for code)
            if not capture_all and any(skip in line for skip in skip_patterns):
                continue

            # Tool header line (⏺ ...) - extract but don't add again
            if '⏺' in line:
                continue

            # Box characters - track state but also capture content
            if '╭' in line or '┌' in line:
                in_box = True
                continue
            if '╰' in line or '└' in line:
                in_box = False
                continue

            # Content inside box (diff lines, code, etc.)
            if '│' in line or '║' in line:
                # Strip box characters but preserve content structure
                content = line
                for char in ['│', '║', '┃']:
                    content = content.replace(char, ' ')
                content = content.strip()
                if content:
                    tool_details.append(content)
            # Diff markers (+ and - lines)
            elif line.startswith('+') or line.startswith('-') or line.startswith('@@'):
                tool_details.append(line)
            # Line numbers with content (for Edit) - matches "412 -async" or "412 +async"
            elif re.match(r'^\d+\s*[\+\-]', line):
                tool_details.append(line)
            # File paths
            elif line.startswith('/') or line.startswith('~') or '/' in line[:50]:
                tool_details.append(line)
            # Any other meaningful content
            elif line and not line.startswith('─') and not line.startswith('═') and not line.startswith('╌'):
                tool_details.append(line)

        return tool_name or 'Unknown', tool_details if tool_details else self.recent_lines[-10:]


class HookApprovalWatcher:
    """Watches for hook-based approval requests (from approval_hook.py)"""

    def __init__(self, remote_client):
        self.remote_client = remote_client
        self.running = True
        self.watcher_thread = None
        self.last_approval_id = None

    def start(self):
        """Start watching for hook approval files in background"""
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()

    def _watch_loop(self):
        """Poll for pending_approval.json from hook"""
        while self.running:
            try:
                if os.path.exists(HOOK_PENDING_APPROVAL_FILE):
                    with open(HOOK_PENDING_APPROVAL_FILE, 'r') as f:
                        approval = json.load(f)

                    # Check if this is a new approval (not one we've seen)
                    approval_id = approval.get('id')
                    if approval_id and approval_id != self.last_approval_id:
                        self.last_approval_id = approval_id

                        # Extract data for WebSocket
                        tool = approval.get('tool', 'Unknown')
                        context = approval.get('context', [])
                        janus_title = approval.get('janusTitle', '')
                        session_title = approval.get('sessionTitle', '')

                        # Send via WebSocket to local Janus
                        if not self.remote_client.pending_approval:
                            safe_status(f"Hook approval: {tool} - {janus_title}", '208')
                            self.remote_client.send_approval_request(
                                tool,
                                context,
                                raw_context=approval,
                                janus_title=janus_title,
                                session_title=session_title
                            )

                        # Delete the file after processing
                        try:
                            os.remove(HOOK_PENDING_APPROVAL_FILE)
                        except:
                            pass

            except (json.JSONDecodeError, FileNotFoundError, PermissionError):
                pass
            except Exception as e:
                debug_log(f"Hook watcher error: {e}")

            time.sleep(0.1)  # Poll every 100ms

    def stop(self):
        """Stop the watcher"""
        self.running = False


def run_claude_session(claude_path, args):
    """Run Claude CLI wrapped in PTY with Janus voice paste support"""

    old_tty = termios.tcgetattr(sys.stdin)
    child_pid = None  # Track child for cleanup

    def cleanup_child():
        """Kill child process on parent exit"""
        if child_pid:
            try:
                os.kill(child_pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass

    def signal_handler(signum, frame):
        """Forward signals to child and exit"""
        cleanup_child()
        # Restore terminal before exit
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
        except:
            pass
        sys.exit(128 + signum)

    try:
        master_fd, slave_fd = pty.openpty()
        pid = os.fork()

        if pid == 0:  # Child process
            os.close(master_fd)
            os.setsid()

            # On Linux: die when parent dies (PR_SET_PDEATHSIG)
            try:
                import ctypes
                libc = ctypes.CDLL("libc.so.6", use_errno=True)
                PR_SET_PDEATHSIG = 1
                libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM)
            except (OSError, AttributeError):
                pass  # Not Linux or prctl not available (macOS)

            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            os.execv(claude_path, [claude_path] + args)

        else:  # Parent process
            child_pid = pid

            # Register cleanup handlers to kill child when parent exits
            atexit.register(cleanup_child)
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGHUP, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            os.close(slave_fd)
            tty.setraw(sys.stdin.fileno())

            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Initialize Remote Client, Approval Detector, Hook Watcher, and Title Refresher
            remote_client = RemotePasteClient(master_fd)
            remote_client.start()

            approval_detector = ApprovalDetector(remote_client)

            # Start hook approval watcher (reads from approval_hook.py output)
            hook_watcher = HookApprovalWatcher(remote_client)
            hook_watcher.start()

            # Start title refresher to keep VSCode tab name visible
            title_refresher = TitleRefresher()
            title_refresher.start()

            line_buffer = b''

            while True:
                rfds, _, _ = select.select([sys.stdin, master_fd], [], [], 0.01)

                pid_status = os.waitpid(pid, os.WNOHANG)
                if pid_status[0] != 0:
                    break

                if sys.stdin in rfds:
                    try:
                        data = os.read(sys.stdin.fileno(), 1024)
                        if data:
                            # If user manually handles approval, clear pending
                            if remote_client.pending_approval:
                                if data in (b'1', b'2', b'3', b'\r', b'\n', b'\x1b'):
                                    remote_client.clear_pending_approval()
                            os.write(master_fd, data)
                    except OSError:
                        pass

                if master_fd in rfds:
                    try:
                        data = os.read(master_fd, 4096)
                        if data:
                            data = filter_title_sequences(data)
                            os.write(sys.stdout.fileno(), data)

                            # Process lines for approval detection
                            line_buffer += data
                            while b'\n' in line_buffer or b'\r' in line_buffer:
                                nl_pos = line_buffer.find(b'\n')
                                cr_pos = line_buffer.find(b'\r')

                                if nl_pos == -1:
                                    pos = cr_pos
                                elif cr_pos == -1:
                                    pos = nl_pos
                                else:
                                    pos = min(nl_pos, cr_pos)

                                if pos == -1:
                                    break

                                line = line_buffer[:pos]
                                line_buffer = line_buffer[pos+1:]

                                text = line.decode('utf-8', errors='ignore')
                                approval_detector.add_line(text)

                    except OSError:
                        pass

            remote_client.stop()
            hook_watcher.stop()
            title_refresher.stop()

            # Child exited - unregister atexit handler since child is dead
            try:
                atexit.unregister(cleanup_child)
            except:
                pass

            _, exit_status = os.waitpid(pid, 0)
            exit_code = os.WEXITSTATUS(exit_status) if os.WIFEXITED(exit_status) else 1

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)

    print()
    print("\033[38;5;245mSession ended.\033[0m")
    sys.exit(exit_code if 'exit_code' in locals() else 0)


def main():
    """Standalone entry point"""
    from .cli import main as cli_main
    cli_main()


if __name__ == '__main__':
    main()
