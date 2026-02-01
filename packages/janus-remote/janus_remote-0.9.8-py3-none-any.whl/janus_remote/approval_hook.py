#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook for Janus Approval System

Intercepts tool calls and extracts approval data with file context.

To enable, add to ~/.claude/settings.json:

{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|Bash|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /Users/cemyavas/Desktop/Janus/scripts/approval-hook.py"
          }
        ]
      }
    ]
  }
}
"""

import sys
import json
import os
import time
import difflib
import textwrap
import re
from datetime import datetime

# Use ~/.janus for remote (more portable than ~/Desktop/Janus)
JANUS_DIR = os.path.expanduser('~/.janus')
PENDING_APPROVAL_FILE = os.path.join(JANUS_DIR, 'pending_approval.json')
AUTO_APPROVE_FILE = os.path.join(JANUS_DIR, 'auto-approve-whitelist.json')


def is_janus_active():
    """Check if Janus is actually running and we should use approval overlay."""
    # Explicit disable takes priority
    if os.environ.get('JANUS_DISABLED') == '1' or os.environ.get('CLAUDE_ONLY') == '1':
        return False

    # If JANUS_TITLE is set, we're running through janus-remote
    if os.environ.get('JANUS_TITLE'):
        return True

    # If nothing indicates Janus is active, don't use approval overlay
    return False


# Early exit if Janus isn't active - pass through to Claude's normal approval
if not is_janus_active():
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask"}}))
    sys.exit(0)

# Ensure directory exists (only if Janus is active)
os.makedirs(JANUS_DIR, exist_ok=True)


def load_auto_approve_whitelist():
    """Load auto-approve patterns from whitelist file."""
    if not os.path.exists(AUTO_APPROVE_FILE):
        return []
    try:
        with open(AUTO_APPROVE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('patterns', [])
    except:
        return []


def check_auto_approve(tool_name, tool_input, session_id=''):
    """Check if this tool call matches any auto-approve pattern."""
    patterns = load_auto_approve_whitelist()
    current_session_id = session_id

    for pattern in patterns:
        # Check session restriction - pattern only applies to matching session ID
        if 'sessionId' in pattern:
            if pattern['sessionId'] != current_session_id:
                continue
        if pattern.get('tool') != tool_name:
            continue

        # Check for "any" pattern - auto-approve all for this tool
        if pattern.get('any'):
            return True

        # Tool-specific checks
        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            has_condition = 'command_prefix' in pattern or 'command_regex' in pattern
            # Check command_prefix
            if 'command_prefix' in pattern:
                if command.strip().startswith(pattern['command_prefix']):
                    return True
            # Check command_regex
            if 'command_regex' in pattern:
                try:
                    if re.match(pattern['command_regex'], command):
                        return True
                except:
                    pass
            # No specific condition = approve all Bash for this session
            if not has_condition:
                return True

        elif tool_name in ('Edit', 'Write'):
            file_path = tool_input.get('file_path', '')
            has_condition = 'file_pattern' in pattern or 'file_prefix' in pattern or 'file_path' in pattern
            if 'file_pattern' in pattern:
                import fnmatch
                if fnmatch.fnmatch(file_path, pattern['file_pattern']):
                    return True
            if 'file_prefix' in pattern:
                if file_path.startswith(pattern['file_prefix']):
                    return True
            if 'file_path' in pattern:
                if file_path == pattern['file_path']:
                    return True
            if not has_condition:
                return True

        elif tool_name == 'Read':
            file_path = tool_input.get('file_path', '')
            has_condition = 'file_pattern' in pattern or 'file_prefix' in pattern or 'file_path' in pattern
            if 'file_pattern' in pattern:
                import fnmatch
                if fnmatch.fnmatch(file_path, pattern['file_pattern']):
                    return True
            if 'file_prefix' in pattern:
                if file_path.startswith(pattern['file_prefix']):
                    return True
            if 'file_path' in pattern:
                if file_path == pattern['file_path']:
                    return True
            if not has_condition:
                return True

        elif tool_name == 'Grep':
            has_condition = 'search_pattern' in pattern or 'path_prefix' in pattern
            if 'search_pattern' in pattern:
                if tool_input.get('pattern', '') == pattern['search_pattern']:
                    return True
            if 'path_prefix' in pattern:
                if tool_input.get('path', '').startswith(pattern['path_prefix']):
                    return True
            if not has_condition:
                return True

        elif tool_name == 'Glob':
            has_condition = 'glob_pattern' in pattern or 'path_prefix' in pattern
            if 'glob_pattern' in pattern:
                if tool_input.get('pattern', '') == pattern['glob_pattern']:
                    return True
            if 'path_prefix' in pattern:
                if tool_input.get('path', '').startswith(pattern['path_prefix']):
                    return True
            if not has_condition:
                return True

    return False




def get_file_context(file_path, old_string, context_lines=5):
    """Read file and get context around where old_string appears."""
    if not file_path or not os.path.exists(file_path):
        return None, None, None

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        return None, None, None

    start_pos = content.find(old_string)
    if start_pos == -1:
        return None, None, None

    start_line = content[:start_pos].count('\n')
    old_lines_list = old_string.split('\n')
    end_line = start_line + len(old_lines_list) - 1

    # Before context
    ctx_start = max(0, start_line - context_lines)
    before = [{'num': i + 1, 'text': lines[i], 'type': 'ctx'} for i in range(ctx_start, start_line)]

    # Old lines (removed)
    old = [{'num': start_line + i + 1, 'text': line, 'type': 'del'} for i, line in enumerate(old_lines_list)]

    # After context
    ctx_end = min(len(lines), end_line + context_lines + 1)
    after = [{'num': i + 1, 'text': lines[i], 'type': 'ctx'} for i in range(end_line + 1, ctx_end)]

    return before, old, after


def build_diff(file_path, old_string, new_string, ctx=3):
    """Build diff using difflib to show only actual changes."""
    # Get starting line number from file
    start_line = 1
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            pos = content.find(old_string)
            if pos != -1:
                start_line = content[:pos].count('\n') + 1
        except:
            pass

    # Use difflib.unified_diff to get proper diff
    old_lines = old_string.splitlines(keepends=False)
    new_lines = new_string.splitlines(keepends=False)

    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm='', n=ctx))

    result = []
    old_num = start_line  # Line number in original file
    new_num = start_line  # Line number in resulting file

    # Skip the header lines (--- and +++)
    for line in diff:
        if line.startswith('@@'):
            continue
        elif line.startswith('---') or line.startswith('+++'):
            continue
        elif line.startswith('-'):
            # Removed line - exists in old, not in new
            result.append({'num': old_num, 'text': line[1:], 'type': 'removed'})
            old_num += 1
        elif line.startswith('+'):
            # Added line - exists in new, not in old
            result.append({'num': new_num, 'text': line[1:], 'type': 'added'})
            new_num += 1
        elif line.startswith(' '):
            # Context line - exists in both
            result.append({'num': new_num, 'text': line[1:], 'type': 'context'})
            old_num += 1
            new_num += 1
        else:
            # No prefix - treat as context
            result.append({'num': new_num, 'text': line, 'type': 'context'})
            old_num += 1
            new_num += 1

    return result


def format_diff_display(diff_lines):
    """Format diff for display."""
    output = []
    for l in diff_lines:
        num = f"{l['num']:4d}" if l['num'] else "    "
        if l['type'] == 'removed':
            output.append(f"  {num} - {l['text']}")
        elif l['type'] == 'added':
            output.append(f"  {num} + {l['text']}")
        else:
            output.append(f"  {num}   {l['text']}")
    return '\n'.join(output)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    tool_use_id = input_data.get('tool_use_id', '')
    session_id = os.environ.get('JANUS_SESSION_ID', '')

    # Check auto-approve whitelist - if matched, auto-approve without UI
    if check_auto_approve(tool_name, tool_input, session_id):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    approval = {
        'tool': tool_name,
        'tool_use_id': tool_use_id,
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    }

    if tool_name == 'Edit':
        file_path = tool_input.get('file_path', '')
        old_string = tool_input.get('old_string', '')
        new_string = tool_input.get('new_string', '')

        diff_lines = build_diff(file_path, old_string, new_string, ctx=5)

        approval['file_path'] = file_path
        approval['old_string'] = old_string
        approval['new_string'] = new_string
        approval['diff_lines'] = diff_lines
        approval['diff_display'] = format_diff_display(diff_lines)

    elif tool_name == 'Write':
        approval['file_path'] = tool_input.get('file_path', '')
        approval['content'] = tool_input.get('content', '')
        approval['is_new'] = not os.path.exists(approval['file_path'])

    elif tool_name == 'Bash':
        approval['command'] = tool_input.get('command', '')
        approval['description'] = tool_input.get('description', '')

    else:
        approval['raw_input'] = tool_input

    # Write to pending_approval.json for PTY to pick up and forward via WebSocket
    # Get filename for title (Edit/Write have file_path, Bash shows command snippet)
    if tool_name in ('Edit', 'Write'):
        file_path = approval.get('file_path', '')
        title = os.path.basename(file_path)
    elif tool_name == 'Bash':
        cmd = approval.get('command', '')
        title = cmd[:40] + '...' if len(cmd) > 40 else cmd
    else:
        title = 'Unknown'

    # For Bash, set trigger to the format extractCommandFromTrigger expects
    if tool_name == 'Bash':
        cmd = approval.get('command', '')
        trigger = f"⏺ Bash({cmd})"
    else:
        trigger = '❯ 1. Yes'

    janus_approval = {
        'id': int(time.time() * 1000) % 100000,
        'timestamp': approval['timestamp'],
        'trigger': trigger,
        'tool': tool_name,
        'status': 'pending',
        'janusTitle': title,  # Filename or command snippet
        'context': []
    }

    # Build context array - just the diff/content, no headers
    # Window already shows: title (left) = filename, tool (right) = Edit/Bash/Write

    if tool_name == 'Edit':
        for line in approval.get('diff_lines', []):
            num = line.get('num')
            text = line.get('text', '')
            line_type = line.get('type', 'context')

            # Format for Janus's formatDiffLine regex patterns:
            # Pattern 1: /^(\d+)\s*([\+\-])\s?(.*)$/ - "NUM + text" or "NUM - text"
            # Pattern 2: /^(\d+)\s{2,}(.*)$/ - "NUM  text" (context, 2+ spaces)
            # Pattern 3: /^\+/ - "+ text" (added without line num)
            # Pattern 4: /^\-/ - "- text" (removed without line num)

            if line_type == 'removed':
                if num is not None:
                    janus_approval['context'].append(f"{num} - {text}")
                else:
                    janus_approval['context'].append(f"- {text}")
            elif line_type == 'added':
                if num is not None:
                    janus_approval['context'].append(f"{num} + {text}")
                else:
                    janus_approval['context'].append(f"+ {text}")
            else:
                # Context lines need 2+ spaces between num and text
                if num is not None:
                    janus_approval['context'].append(f"{num}  {text}")
                else:
                    janus_approval['context'].append(text)

    elif tool_name == 'Bash':
        # Command is in trigger field, context can show description if available
        desc = approval.get('description', '')
        if desc:
            janus_approval['context'].append(desc)

    elif tool_name == 'Write':
        content = approval.get('content', '')
        for line in content.split('\n')[:50]:
            janus_approval['context'].append(f"+ {line}")

        if content.count('\n') > 50:
            janus_approval['context'].append(f"... ({content.count(chr(10)) - 50} more lines)")

    try:
        with open(PENDING_APPROVAL_FILE, 'w') as f:
            json.dump(janus_approval, f, indent=2)
    except Exception as e:
        pass

    # Return "ask" to show Claude's normal approval dialog
    # Change to "allow" to auto-approve, "deny" to block
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask"
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == '__main__':
    main()
