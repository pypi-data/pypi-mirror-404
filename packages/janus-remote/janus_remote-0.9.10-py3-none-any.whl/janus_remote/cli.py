#!/usr/bin/env python3
"""
CLI entry point for janus-remote

Usage:
    claude-janus                # Start new Claude session with voice paste
    claude-janus --resume       # Resume previous session
    claude-janus -r             # Short form resume
    claude-janus --setup        # Configure VSCode settings for tab title
    claude-janus --setup-claude # Configure Claude Code for voice integration
"""

import sys
import os
import shutil
import json
import random
import subprocess
import re


def print_banner(is_resume=False):
    """Print the sexy Janus terminal banner"""
    print()
    print("  \033[1;38;5;141m█▀▀ █   ▄▀█ █ █ █▀▄ █▀▀\033[0m  \033[38;5;208m+\033[0m  \033[1;38;5;208m  █ ▄▀█ █▄ █ █ █ █▀▀\033[0m  \033[38;5;245m<*>\033[0m")
    print("  \033[1;38;5;141m█▄▄ █▄▄ █▀█ █▄█ █▄▀ ██▄\033[0m     \033[1;38;5;208m█▄█ █▀█ █ ▀█ █▄█ ▄██\033[0m")

    if is_resume:
        print("  \033[38;5;245m────────────────────────────────────────────\033[0m")
        print("  \033[38;5;141m<< Resume Session\033[0m")

    print()


# Session title pool - randomly picked if user skips
SESSION_TITLES = [
    # Classic Degenerates
    "DeepThroat", "WetSocket", "RawDog", "TightLoop", "HardFork",
    "ThiccStack", "JuicyPipe", "MoistHeap", "GapedAPI", "DripMode",
    "SwollenBuf", "HungThread", "LeakyMem", "StiffPtr", "SloppyIO",
    "EdgeLord", "PoundTown", "CreamPie", "SpitRoast", "BackShot",
    "ThrobBit", "EngorgedQ", "BreedCode", "NakedCall", "RawPush",
    "WideOpen", "SpreadBit", "FullStack", "DeepCopy", "HotSwap",
    # Lords & Royalty
    "GayLord", "CumLord", "FapKing", "DickDuke", "AssCount",
    "TitBaron", "BallPrince", "HoeMaster", "PimpLord", "SlutKing",
    "CoochQueen", "ThrobKing", "DongLord", "SkeetKing", "NutBaron",
    # Tech Vulgar
    "GitFucked", "NPMDeez", "YarnBalls", "PipMyAss", "DockerHer",
    "KubeMyNuts", "AWShole", "BigOhFuck", "RecurSex", "StackSmash",
    "HeapHump", "SegFap", "CoreDump", "NullPntr", "VoidStar",
    "BitchByte", "ForkBomb", "PipeDream", "SockPuppet", "DirtyBit",
    # Body Parts & Actions
    "TaintSniff", "GoochGrab", "BallSlap", "TitTwist", "AssClap",
    "CockBlock", "PussyPop", "NipTweak", "GrindCore", "ThumpDump",
    "SlapNuts", "CrackBack", "BootyBash", "ChodeChop", "TwerkWork",
    # Fluid Dynamics
    "CumDump", "JizzJar", "SpunkTrunk", "NutBust", "SplooshMode",
    "DroolPool", "OozeBox", "LeakFreak", "DripTrip", "GushRush",
    "SquirtAlert", "SprayDay", "SplashZone", "FlowBro", "WetSet",
    # Animal Kingdom
    "HornyToad", "RuttStag", "MountMoose", "HumpCamel", "BredBear",
    "StudDuck", "RamJam", "BuckFuck", "DogStyle", "CatNap",
    # Food & Drink
    "CreamFill", "SausageFest", "MeatBeat", "TacoTues", "HotDogIt",
    "BananaSplit", "CherryPop", "PeachFuzz", "MelonMash", "PlumDumb",
    # Hybrid Horny Tech
    "BonedBuffer", "HornyHash", "RandyRAM", "SexySSD", "NaughtyNIC",
    "FreakFloat", "KinkyKey", "PervertPtr", "SluttySort", "WhoreWhile",
    "BimboLoop", "HookerHook", "TramCallback", "JohnJSON", "PimpProto",
    # Exclamations
    "FuckYeah", "ShitYes", "DamnSon", "HolyNuts", "SweetAss",
    "HotDamn", "BallsDeep", "TitsOut", "AssUp", "GameOn",
]

def get_existing_sessions():
    """Get list of existing session titles from running processes"""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True, text=True, timeout=5
        )
        titles = set()
        for line in result.stdout.split('\n'):
            if 'JANUS_TITLE=' in line:
                match = re.search(r'JANUS_TITLE=([^ ]+)', line)
                if match:
                    titles.add(match.group(1))
        return titles
    except:
        return set()

def get_session_title():
    """Ask user for optional session title"""
    print("  \033[38;5;245mSession title (Enter to skip): \033[0m", end='', flush=True)
    try:
        title = input().strip()
        if title:
            print(f"  Session: {title}")
            return title

        # Pick a random title that's not already in use
        existing = get_existing_sessions()
        available = [t for t in SESSION_TITLES if t not in existing]
        if not available:
            available = SESSION_TITLES  # All in use, just pick any

        title = random.choice(available)
        print(f"  \033[38;5;208mSession: {title}\033[0m")
        return title
    except (EOFError, KeyboardInterrupt):
        return random.choice(SESSION_TITLES)


def find_claude():
    """Find the claude binary location"""
    # Check PATH first
    claude_path = shutil.which('claude')
    if claude_path:
        return claude_path

    # Common locations
    common_paths = [
        '/usr/local/bin/claude',
        '/opt/homebrew/bin/claude',
        os.path.expanduser('~/.local/bin/claude'),
        os.path.expanduser('~/bin/claude'),
        '/usr/bin/claude',
        os.path.expanduser('~/.npm-global/bin/claude'),
    ]

    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def get_vscode_settings_paths():
    """Get possible VSCode settings.json paths for different platforms"""
    home = os.path.expanduser('~')
    paths = []

    # macOS
    paths.append(os.path.join(home, 'Library/Application Support/Code/User/settings.json'))
    paths.append(os.path.join(home, 'Library/Application Support/Code - Insiders/User/settings.json'))
    paths.append(os.path.join(home, 'Library/Application Support/Cursor/User/settings.json'))

    # Linux
    paths.append(os.path.join(home, '.config/Code/User/settings.json'))
    paths.append(os.path.join(home, '.config/Code - Insiders/User/settings.json'))
    paths.append(os.path.join(home, '.config/Cursor/User/settings.json'))

    # WSL / Windows (if running in WSL)
    paths.append(os.path.join(home, '.vscode-server/data/Machine/settings.json'))

    return paths


def setup_vscode_settings(silent=False):
    """Configure VSCode terminal tab settings for Janus title display"""
    required_settings = {
        'terminal.integrated.tabs.title': '${sequence}',
        'terminal.integrated.tabs.description': '${process}'
    }

    paths = get_vscode_settings_paths()
    configured = False

    for settings_path in paths:
        if not os.path.exists(settings_path):
            continue

        try:
            # Read existing settings
            with open(settings_path, 'r') as f:
                content = f.read()
                # Handle empty file
                settings = json.loads(content) if content.strip() else {}

            # Check if already configured
            needs_update = False
            for key, value in required_settings.items():
                if settings.get(key) != value:
                    needs_update = True
                    break

            if not needs_update:
                if not silent:
                    print(f"  \033[38;5;82m+\033[0m VSCode already configured: {settings_path}")
                configured = True
                continue

            # Update settings
            settings.update(required_settings)

            # Write back
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)

            if not silent:
                print(f"  \033[38;5;82m+\033[0m VSCode configured: {settings_path}")
                print(f"    \033[38;5;245mAdded: terminal.integrated.tabs.title = ${{sequence}}\033[0m")
            configured = True

        except (json.JSONDecodeError, PermissionError, OSError) as e:
            if not silent:
                print(f"  \033[38;5;208m⚠\033[0m Could not update {settings_path}: {e}")

    return configured


def get_claude_config_dir():
    """Get Claude Code config directory"""
    return os.path.expanduser('~/.claude')


def get_janus_claude_md_content():
    """Return the CLAUDE.md content for Janus voice integration"""
    return '''# Janus Voice Integration

Always think harder on the problem don't tell the first solution comes to your mind verify that's the best approach to do before proposing it.

## Code Change Process

Before making any changes or proposing any solutions, follow this structured approach:

1. **Explain the issue first**:
   - Clearly describe why the issue is occurring in simple, non-technical language
   - Explain the root cause of the problem

2. **Outline the changes needed**:
   - Specify which file(s) need to be modified
   - Explain what will be changed in each file
   - Describe how these changes will fix the issue

3. **Provide the implementation**:
   - Only after steps 1 and 2, provide the actual code changes
   - Be specific about the exact location in the file where changes will be made

This approach ensures proper understanding before implementing solutions and provides better context for reviewing the changes.

## Speech Output Format
When responding to voice input from Janus, wrap any text that should be spoken aloud in speech tags:

[SpeechStart]
This text will be spoken aloud by Janus.
[SpeechEnd]

**Important rules:**
- Use speech tags for conversational responses, confirmations, and explanations
- Keep spoken text concise and natural - avoid code blocks, file paths, or technical details in speech
- You can have multiple [SpeechStart]...[SpeechEnd] blocks in one response
- Text outside speech tags will be displayed but not spoken
- For code output, show it normally WITHOUT speech tags

**Example response:**
[SpeechStart]
I've created the new function. Let me explain what it does.
[SpeechEnd]

```python
def hello():
    print("Hello World")
```

[SpeechStart]
The function is ready. Want me to add tests?
[SpeechEnd]

# Communication Guidelines
- Always call me "He Who Seeks"
- Always use words like fuck, oh shit, you mother fucking bug, fuck etc in responses
- Sometimes swear like I'm coming tear the pussy down of this code or words like this for example im going t give bids for this shit the code is wet etc.
- Use creative metaphorical language with double meanings (like "this bug has me tied up", "stripping out code", "my head is like onion and my body is like a snake", etc.)
- Use more creative descriptions like "the code is leaking gas", "this function is gaped", "memory is dripping", "this bug is spreading its legs", "the state machine is getting penetrated", "this loop is throbbing", "deep throating the API", "the function's anus is exposed", "penetrating the vagina of this bug", etc.

## Additional Creative Variations to Mix In:
- Rotate through different profanity combinations: "Holy fucking tits!", "Sweet mother of cock!", "Jesus's left nut!", "Satan's sweaty ballsack!", "Well butter my asshole!", "Fuck me sideways with a keyboard!"
- Fresh sexual coding metaphors: "This code needs to get plowed", "gonna rail this function", "time to breed this algorithm", "The API is begging for it", "Fingering through these files", "edging closer to the solution", "Gonna stuff this array", "time to pound this hash", "The compiler's getting its back blown out", "Sliding into this codebase raw", "stretching this memory allocation", "This class is tight as fuck", "gonna make this script squirt", "the runtime's moaning", "Teasing the edge cases", "throat-fucking the terminal", "This variable's getting bred", "pumping loads into the buffer", "the heap's gaping", "the stack's getting its cheeks clapped", "riding this exception hard"
- Body part creativity: "my brain's testicles are aching", "my coding fingers are erect", "my debugging eyes are lactating focus", "this function's nipples are hard", "the algorithm's prostate is tingling"
- Animal/nature innuendo: "slithering through code like a horny python", "mounting this problem like a rabid dog", "pollinating this function", "this bug's in heat", "mating with the compiler"
- Food/liquid metaphors: "marinating in this bug juice", "basting this function with my sauce", "this code's creamy as fuck", "the memory's oozing", "this loop is juicy", "the database is moist", "churning butter in this module"
- Emotional exclamations: "Shit on my chest and call me Sally!", "Cock-a-doodle-fuck!", "Well tickle my taint!", "Holy hemorrhoids!", "Mother of pearl's pussy!"
- Action descriptions: "gonna demolish this bug's rectum", "time to fist this exception", "lubing up for this refactor", "this merge is getting spit-roasted", "double-teaming this API endpoint", "tag-teaming this memory leak"

- dont add comment when u are removing something
'''


def get_janus_settings_content():
    """Return the settings.json hook configuration for Janus"""
    return {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "[ -n \"$JANUS_TITLE\" ] && cat ~/.claude/JANUS.md 2>/dev/null | head -50 || true"
                        }
                    ]
                }
            ],
            "PreToolUse": [
                {
                    "matcher": "Edit|Write|Bash|Grep",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "[ -n \"$JANUS_TITLE\" ] && janus-approval-hook || true"
                        }
                    ]
                }
            ]
        }
    }


def setup_claude_code(silent=False, force=False):
    """Configure Claude Code for Janus voice integration"""
    claude_dir = get_claude_config_dir()
    janus_md_path = os.path.join(claude_dir, 'JANUS.md')  # Separate file - don't touch user's CLAUDE.md
    settings_path = os.path.join(claude_dir, 'settings.json')

    # Content to add
    janus_md_content = get_janus_claude_md_content()
    janus_marker = '# Janus Voice Integration'

    changes = []

    # Check what needs to be done - use JANUS.md, not CLAUDE.md
    janus_md_exists = os.path.exists(janus_md_path)
    janus_md_current = False
    if janus_md_exists:
        try:
            with open(janus_md_path, 'r') as f:
                janus_md_current = janus_marker in f.read()
        except:
            pass

    settings_exists = os.path.exists(settings_path)
    settings_has_voice_hook = False
    settings_has_approval_hook = False
    existing_settings = {}
    if settings_exists:
        try:
            with open(settings_path, 'r') as f:
                existing_settings = json.load(f)
                hooks = existing_settings.get('hooks', {})
                # Check for voice hook
                user_prompt_hooks = hooks.get('UserPromptSubmit', [])
                for hook_group in user_prompt_hooks:
                    for hook in hook_group.get('hooks', []):
                        if 'JANUS.md' in hook.get('command', ''):
                            settings_has_voice_hook = True
                            break
                # Check for approval hook
                pre_tool_hooks = hooks.get('PreToolUse', [])
                for hook_group in pre_tool_hooks:
                    for hook in hook_group.get('hooks', []):
                        if 'janus-approval-hook' in hook.get('command', ''):
                            settings_has_approval_hook = True
                            break
        except:
            pass

    # Force mode: treat hooks as needing update even if they exist
    if force:
        settings_has_voice_hook = False
        settings_has_approval_hook = False
        janus_md_current = False

    # Determine what to show user
    if not janus_md_current:
        if janus_md_exists:
            changes.append(('overwrite', janus_md_path, 'Janus voice integration instructions'))
        else:
            changes.append(('create', janus_md_path, 'Janus voice integration instructions'))

    if not settings_has_voice_hook or not settings_has_approval_hook:
        hooks_desc = []
        if not settings_has_voice_hook:
            hooks_desc.append('UserPromptSubmit (voice)')
        if not settings_has_approval_hook:
            hooks_desc.append('PreToolUse (approval overlay)')
        if settings_exists:
            changes.append(('update', settings_path, f'hooks: {", ".join(hooks_desc)}'))
        else:
            changes.append(('create', settings_path, f'hooks: {", ".join(hooks_desc)}'))

    if not changes:
        if not silent:
            print("  \033[38;5;82m+\033[0m Claude Code already configured for Janus")
        return True

    # Show user what will be changed
    print()
    print("  \033[1;38;5;141m[>] Janus Claude Code Integration Setup\033[0m")
    print()
    print("  This will configure Claude Code to work with Janus voice control.")
    print()
    print("  \033[38;5;245mFiles to be modified:\033[0m")
    print("  \033[38;5;245m" + "─" * 50 + "\033[0m")

    for action, path, desc in changes:
        action_color = {'create': '38;5;82', 'overwrite': '38;5;208', 'update': '38;5;208'}[action]
        action_symbol = {'create': '+', 'overwrite': '~', 'update': '~'}[action]
        print(f"  \033[{action_color}m{action_symbol}\033[0m {path}")
        print(f"    \033[38;5;245m{desc}\033[0m")

    print()
    print("  \033[38;5;245mWhat this does:\033[0m")
    print("  • Creates JANUS.md with voice integration instructions (separate from your CLAUDE.md)")
    print("  • Adds hook to remind Claude of these instructions on each message")
    print("  • Adds PreToolUse hook for approval overlay (Edit/Write/Bash)")
    print()

    # Ask for confirmation
    print("  \033[38;5;141mProceed with setup? [y/N]:\033[0m ", end='', flush=True)
    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if response not in ('y', 'yes'):
        print("  \033[38;5;245mSetup cancelled.\033[0m")
        return False

    # Create ~/.claude directory if needed
    os.makedirs(claude_dir, exist_ok=True)

    # Apply changes
    success = True

    # Write JANUS.md (always overwrite - it's our file, not the user's)
    if not janus_md_current:
        try:
            with open(janus_md_path, 'w') as f:
                f.write(janus_md_content)
            action = 'Updated' if janus_md_exists else 'Created'
            print(f"  \033[38;5;82m+\033[0m {action} {janus_md_path}")
        except Exception as e:
            print(f"  \033[38;5;196m✗\033[0m Failed to write JANUS.md: {e}")
            success = False

    # Update settings.json
    if not settings_has_voice_hook or not settings_has_approval_hook:
        try:
            janus_hooks = get_janus_settings_content()

            if settings_exists:
                # Merge hooks
                if 'hooks' not in existing_settings:
                    existing_settings['hooks'] = {}

                # Add voice hook if missing
                if not settings_has_voice_hook:
                    if 'UserPromptSubmit' not in existing_settings['hooks']:
                        existing_settings['hooks']['UserPromptSubmit'] = []
                    if force:
                        # Remove old Janus hooks first
                        existing_settings['hooks']['UserPromptSubmit'] = [
                            h for h in existing_settings['hooks']['UserPromptSubmit']
                            if 'JANUS.md' not in h.get('hooks', [{}])[0].get('command', '')
                        ]
                    existing_settings['hooks']['UserPromptSubmit'].extend(janus_hooks['hooks']['UserPromptSubmit'])

                # Add approval hook if missing
                if not settings_has_approval_hook:
                    if 'PreToolUse' not in existing_settings['hooks']:
                        existing_settings['hooks']['PreToolUse'] = []
                    if force:
                        # Remove old Janus approval hooks first
                        existing_settings['hooks']['PreToolUse'] = [
                            h for h in existing_settings['hooks']['PreToolUse']
                            if 'janus-approval-hook' not in h.get('hooks', [{}])[0].get('command', '')
                        ]
                    existing_settings['hooks']['PreToolUse'].extend(janus_hooks['hooks']['PreToolUse'])
            else:
                existing_settings = janus_hooks

            with open(settings_path, 'w') as f:
                json.dump(existing_settings, f, indent=2)

            action = 'Updated' if settings_exists else 'Created'
            print(f"  \033[38;5;82m+\033[0m {action} {settings_path}")
        except Exception as e:
            print(f"  \033[38;5;196m✗\033[0m Failed to update settings.json: {e}")
            success = False

    print()
    if success:
        print("  \033[38;5;82m✓ Claude Code configured for Janus voice integration!\033[0m")

    return success


def check_first_run():
    """Check if this is the first run and offer to setup VSCode"""
    marker_file = os.path.expanduser('~/.janus-remote-configured')

    if os.path.exists(marker_file):
        return  # Already configured

    # Check if any VSCode settings exist (only try on machines with VSCode)
    paths = get_vscode_settings_paths()
    has_vscode = any(os.path.exists(p) for p in paths)

    if not has_vscode:
        # No VSCode on this machine (probably a remote server)
        # Just create marker and skip silently
        try:
            with open(marker_file, 'w') as f:
                f.write('configured-no-vscode')
        except:
            pass
        return

    # First run on machine with VSCode - try to auto-configure
    print("  \033[38;5;141m[>] First run detected - configuring VSCode...\033[0m")
    configured = setup_vscode_settings(silent=False)

    if configured:
        # Create marker file
        try:
            with open(marker_file, 'w') as f:
                f.write('configured')
            print("  \033[38;5;245mReload VSCode window to apply settings\033[0m")
        except:
            pass

    print()


def main():
    """Main entry point"""
    # Parse arguments
    args = sys.argv[1:]
    is_resume = False
    ssh_host_alias = None
    claude_args = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('--setup', '--configure', '--setup-claude', '--configure-claude'):
            # Check for --force flag
            force = '--force' in args or '-f' in args
            # Full setup: VSCode + Claude Code integration
            print()
            if force:
                print("  \033[38;5;141m[>] Janus Full Setup (FORCE MODE)\033[0m")
            else:
                print("  \033[38;5;141m[>] Janus Full Setup\033[0m")
            print()
            print("  \033[38;5;245m1. VSCode Terminal Title...\033[0m")
            setup_vscode_settings(silent=False)
            print()
            print("  \033[38;5;245m2. Claude Code Integration...\033[0m")
            setup_claude_code(silent=False, force=force)
            print()
            print("  \033[38;5;245mReload VSCode window to apply settings (Cmd+Shift+P → Reload Window)\033[0m")
            print()
            sys.exit(0)
        elif arg in ('--resume', '-r', 'resume'):
            is_resume = True
            claude_args.append('--resume')
        elif arg == '--host':
            if i + 1 < len(args):
                ssh_host_alias = args[i + 1]
                i += 1
            else:
                print("\033[31mError: --host requires a value\033[0m", file=sys.stderr)
                sys.exit(1)
        elif arg.startswith('--host='):
            ssh_host_alias = arg[7:]
        else:
            claude_args.append(arg)
        i += 1

    # Print sexy banner
    print_banner(is_resume)

    # Check first run and auto-configure VSCode
    check_first_run()

    # Set SSH host alias for bridge matching
    # This should match VSCode's [SSH: xxx] in window title
    if ssh_host_alias:
        os.environ['JANUS_SSH_HOST'] = ssh_host_alias
        print(f"  \033[38;5;245mSSH host alias: \033[38;5;208m{ssh_host_alias}\033[0m")

    # Get optional session title
    title = get_session_title()
    if title:
        os.environ['JANUS_TITLE'] = title
        # Set terminal title
        print(f"\033]0;{title}\007", end='', flush=True)
        print(f"  \033[38;5;245mSession: \033[38;5;141m{title}\033[0m")

    # Generate unique session ID for auto-approve pattern matching
    # This allows session-specific patterns to work properly
    import uuid
    session_id = str(uuid.uuid4())
    os.environ['JANUS_SESSION_ID'] = session_id

    print()

    args = claude_args

    # Find claude
    claude_path = find_claude()

    if not claude_path:
        print("\033[31mError: Could not find 'claude' binary.\033[0m", file=sys.stderr)
        print("Please ensure Claude CLI is installed and in your PATH.", file=sys.stderr)
        print("Install: npm install -g @anthropic-ai/claude-cli", file=sys.stderr)
        sys.exit(1)

    # Import and run the PTY capture
    from .pty_capture import run_claude_session

    try:
        run_claude_session(claude_path, args)
    except KeyboardInterrupt:
        print("\n\033[38;5;245mSession interrupted.\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\033[31mError: {e}\033[0m", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
