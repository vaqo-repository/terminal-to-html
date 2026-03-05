#!/usr/bin/env python3
"""
Terminal Output to HTML Converter
Paste terminal output and get a beautiful HTML file that looks like a real terminal.
Works with any hostname, any OS prompt format.
"""

import re
import sys
import os
import html
import datetime

# Common prompt patterns (covers bash, zsh, kali, ubuntu, generic linux, powershell, cmd)
PROMPT_PATTERNS = [
    # Kali-style: ┌──(user㉿host)-[path] / └─$
    re.compile(r'^(.*?[\$#%>])\s(.*)$'),
]

# Detect prompt lines
def is_prompt_line(line):
    """Detect if a line contains a shell prompt."""
    # Kali-style box drawing prompt
    if re.match(r'^[┌├└─│╭╰┬┤┘┐╮╯]+', line):
        return True
    # Generic prompt ending with $, #, %, >
    if re.match(r'^.*?[\w@㉿\-\.\[\]~\/\\:\(\)]+.*?[\$#%>]\s', line):
        return True
    # PS1-style: user@host:path$
    if re.match(r'^\w+@[\w\-\.]+[:\s].*[\$#]\s', line):
        return True
    # Simple $ or # prompt
    if re.match(r'^\s*[\$#]\s', line):
        return True
    # PowerShell prompt: PS C:\>
    if re.match(r'^PS\s+.*>', line):
        return True
    # CMD prompt: C:\>
    if re.match(r'^[A-Z]:\\.*>', line):
        return True
    return False


def parse_prompt_and_command(line):
    """Split a prompt line into prompt part and command part."""
    # Kali-style: └─$ command
    m = re.match(r'^(.*?[\$#%>])\s*(.*)', line)
    if m:
        return m.group(1), m.group(2)
    return line, ''


def classify_lines(text):
    """
    Classify each line as prompt, command-line, or output.
    Returns list of (type, content) tuples.
    type: 'prompt-header' (┌──...), 'command-line' (└─$ ...), 'output'
    """
    lines = text.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if not stripped and not line.strip():
            result.append(('empty', ''))
            continue
        
        # Kali-style header: ┌──(user㉿host)-[path]
        if re.match(r'^[┌╭]', stripped) and not re.search(r'[\$#%>]\s', stripped):
            result.append(('prompt-header', stripped))
            continue
        
        # Kali-style command line: └─$ command
        if re.match(r'^[└╰]', stripped):
            prompt, cmd = parse_prompt_and_command(stripped)
            result.append(('command-line', (prompt, cmd)))
            continue
        
        # Generic prompt with command
        if is_prompt_line(stripped):
            prompt, cmd = parse_prompt_and_command(stripped)
            result.append(('command-line', (prompt, cmd)))
            continue
        
        # Regular output
        result.append(('output', stripped))
    
    return result


def colorize_prompt_header(text):
    """Add colors to prompt header like ┌──(kali㉿kali)-[~]"""
    escaped = html.escape(text)
    
    # Color the box drawing characters
    escaped = re.sub(
        r'^([┌└─╭╰│├┬┤┘┐╮╯]+)',
        r'<span class="prompt-box">\1</span>',
        escaped
    )
    
    # Color (user㉿host) part in green
    escaped = re.sub(
        r'\(([^)]+)\)',
        r'(<span class="prompt-user">\1</span>)',
        escaped
    )
    
    # Color [path] part in blue
    escaped = re.sub(
        r'\[([^\]]+)\]',
        r'[<span class="prompt-path">\1</span>]',
        escaped
    )
    
    return escaped


def colorize_command_line(prompt, command):
    """Add colors to command line like └─$ command"""
    escaped_prompt = html.escape(prompt)
    escaped_cmd = html.escape(command)
    
    # Color box drawing chars
    escaped_prompt = re.sub(
        r'^([┌└─╭╰│├┬┤┘┐╮╯]+)',
        r'<span class="prompt-box">\1</span>',
        escaped_prompt
    )
    
    # Color the $ # % > symbol
    escaped_prompt = re.sub(
        r'([\$#%>])$',
        r'<span class="prompt-symbol">\1</span>',
        escaped_prompt
    )
    
    if escaped_cmd:
        # Highlight sudo
        escaped_cmd = re.sub(
            r'^(sudo)\b',
            r'<span class="cmd-sudo">\1</span>',
            escaped_cmd
        )
        # Highlight first word (command name)
        escaped_cmd = re.sub(
            r'^(<span class="cmd-sudo">sudo</span>\s+)?(\S+)',
            lambda m: (m.group(1) or '') + f'<span class="cmd-name">{m.group(2)}</span>',
            escaped_cmd
        )
        # Highlight flags (-x, --xxx)
        escaped_cmd = re.sub(
            r'(\s)(--?\w[\w\-]*)',
            r'\1<span class="cmd-flag">\2</span>',
            escaped_cmd
        )
        # Highlight paths (starting with /)
        escaped_cmd = re.sub(
            r'(\s)(/[\w/\.\-\*]+)',
            r'\1<span class="cmd-path">\2</span>',
            escaped_cmd
        )
    
    return f'{escaped_prompt} <span class="command">{escaped_cmd}</span>'


def colorize_output(text):
    """Colorize output lines - detect errors, URLs, paths etc."""
    escaped = html.escape(text)
    
    # Highlight [ERROR] tags
    escaped = re.sub(
        r'\[ERROR\]',
        r'<span class="error">[ERROR]</span>',
        escaped
    )
    
    # Highlight [WARNING] tags
    escaped = re.sub(
        r'\[WARNING\]',
        r'<span class="warning">[WARNING]</span>',
        escaped
    )
    
    # Highlight URLs
    escaped = re.sub(
        r'(https?://[^\s<>&"]+)',
        r'<span class="url">\1</span>',
        escaped
    )
    
    # Highlight "Permission denied" and similar errors
    escaped = re.sub(
        r'(Permission denied|No such file|not found|invalid|error)',
        r'<span class="error-text">\1</span>',
        escaped,
        flags=re.IGNORECASE
    )
    
    return escaped


def generate_html(classified_lines, title="Terminal"):
    """Generate the full HTML document."""
    
    body_lines = []
    for line_type, content in classified_lines:
        if line_type == 'empty':
            body_lines.append('')
        elif line_type == 'prompt-header':
            body_lines.append(colorize_prompt_header(content))
        elif line_type == 'command-line':
            prompt, cmd = content
            body_lines.append(colorize_command_line(prompt, cmd))
        elif line_type == 'output':
            body_lines.append(colorize_output(content))
    
    terminal_content = '\n'.join(body_lines)
    
    html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: #1a1a2e;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            padding: 30px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}

        .terminal-window {{
            background: #0c0c0c;
            border-radius: 12px;
            width: 100%;
            max-width: 1100px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
                        0 0 40px rgba(0, 150, 255, 0.05);
            overflow: hidden;
            border: 1px solid #333;
        }}

        .terminal-header {{
            background: linear-gradient(180deg, #3c3c3c, #2d2d2d);
            padding: 10px 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid #1a1a1a;
            user-select: none;
        }}

        .terminal-btn {{
            width: 13px;
            height: 13px;
            border-radius: 50%;
            display: inline-block;
        }}

        .btn-close {{ background: #ff5f57; }}
        .btn-minimize {{ background: #ffbd2e; }}
        .btn-maximize {{ background: #28c840; }}

        .terminal-title {{
            color: #999;
            font-size: 13px;
            margin-left: 8px;
            flex-grow: 1;
            text-align: center;
        }}

        .terminal-body {{
            padding: 16px 20px;
            overflow-x: auto;
            min-height: 100px;
        }}

        .terminal-body pre {{
            font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 
                         'Source Code Pro', 'Consolas', 'Monaco', 
                         'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            color: #d4d4d4;
            white-space: pre-wrap;
            word-wrap: break-word;
            tab-size: 4;
        }}

        /* Prompt styling */
        .prompt-box {{
            color: #569cd6;
        }}

        .prompt-user {{
            color: #4ec9b0;
            font-weight: bold;
        }}

        .prompt-path {{
            color: #569cd6;
            font-weight: bold;
        }}

        .prompt-symbol {{
            color: #d4d4d4;
            font-weight: bold;
        }}

        /* Command styling */
        .command {{
            color: #e2e2e2;
        }}

        .cmd-sudo {{
            color: #f44747;
            font-weight: bold;
        }}

        .cmd-name {{
            color: #dcdcaa;
            font-weight: bold;
        }}

        .cmd-flag {{
            color: #9cdcfe;
        }}

        .cmd-path {{
            color: #ce9178;
        }}

        /* Output styling */
        .error {{
            color: #f44747;
            font-weight: bold;
        }}

        .error-text {{
            color: #f44747;
        }}

        .warning {{
            color: #ffbd2e;
            font-weight: bold;
        }}

        .url {{
            color: #3794ff;
            text-decoration: underline;
        }}

        /* Scrollbar */
        .terminal-body::-webkit-scrollbar {{
            height: 8px;
        }}

        .terminal-body::-webkit-scrollbar-track {{
            background: #1e1e1e;
        }}

        .terminal-body::-webkit-scrollbar-thumb {{
            background: #444;
            border-radius: 4px;
        }}

        .terminal-body::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}

        /* Selection */
        .terminal-body pre::selection,
        .terminal-body pre *::selection {{
            background: rgba(38, 79, 120, 0.8);
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            .terminal-body {{
                padding: 12px 14px;
            }}
            .terminal-body pre {{
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="terminal-window">
        <div class="terminal-header">
            <span class="terminal-btn btn-close"></span>
            <span class="terminal-btn btn-minimize"></span>
            <span class="terminal-btn btn-maximize"></span>
            <span class="terminal-title">{html.escape(title)}</span>
        </div>
        <div class="terminal-body">
            <pre>{terminal_content}</pre>
        </div>
    </div>
</body>
</html>'''
    
    return html_doc


def main():
    print("=" * 60)
    print("  Terminal Output → HTML Converter")
    print("=" * 60)
    print()
    print("Terminal outputunu paste edin.")
    print("Bitirdikden sonra yeni sətirdə 'END' yazıb Enter basın.")
    print("(Və ya Ctrl+Z basıb Enter basın)")
    print()
    
    lines = []
    try:
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
    except EOFError:
        pass
    
    if not lines:
        print("Heç bir input verilmədi!")
        sys.exit(1)
    
    text = '\n'.join(lines)
    
    # Classify lines
    classified = classify_lines(text)
    
    # Generate HTML
    html_output = generate_html(classified, title="Terminal Output")
    
    # Save to file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"terminal_{timestamp}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    abs_path = os.path.abspath(output_file)
    print(f"\nHTML fayl uğurla yaradıldı: {abs_path}")
    print(f"Brauzerdə açmaq üçün faylı iki dəfə klikləyin.")
    
    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(f'file://{abs_path}')
        print("Fayl brauzerdə açıldı!")
    except Exception:
        pass


if __name__ == '__main__':
    main()
