import os
import yaml
from pathlib import Path


def load_prompt(name):
    mydirectory = os.path.dirname(os.path.abspath(__file__))
    promptdir = Path(mydirectory) / 'prompts'
    filepath = promptdir / f"{name}.txt"
    with open(filepath) as file:
        content = file.read()
    return content


def parse_mcp_servers(mcp_list):
    """Parse MCP server list into command/args dicts.
    
    Args:
        mcp_list: List of command strings (e.g., ["python server.py", "node app.js"])
    
    Returns:
        List of dicts with 'command' and 'args' keys
    """
    if not mcp_list:
        return []
    
    servers = []
    for server_line in mcp_list:
        parts = server_line.split()
        if parts:
            servers.append({
                'command': parts[0],
                'args': parts[1:] if len(parts) > 1 else []
            })
    return servers


def parse_yaml_input(yaml_text):
    """Parse YAML input containing optional prompt and mcp entries.
    
    Args:
        yaml_text: YAML string that may contain 'prompt' and/or 'mcp' keys,
                   or plain text which will be treated as the prompt
    
    Returns:
        Dict with 'prompt' (str or None) and 'mcp_servers' (list) keys
    """
    if not yaml_text or not yaml_text.strip():
        return {'prompt': None, 'mcp_servers': []}
    
    try:
        config = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        # Invalid YAML - treat entire text as prompt
        return {'prompt': yaml_text, 'mcp_servers': []}
    
    if not config or not isinstance(config, dict):
        # YAML doesn't parse to a dict - treat entire text as prompt
        return {'prompt': yaml_text, 'mcp_servers': []}
    
    prompt = config.get('prompt')
    mcp_list = config.get('mcp', [])
    mcp_servers = parse_mcp_servers(mcp_list)
    
    return {'prompt': prompt, 'mcp_servers': mcp_servers}
