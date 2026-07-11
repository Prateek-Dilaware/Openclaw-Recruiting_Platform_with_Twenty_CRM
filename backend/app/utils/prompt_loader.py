import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_prompt(prompt_name: str, **variables) -> str:
    """
    Loads a prompt markdown template from the root prompts/ directory and formats it with variables.
    
    Args:
        prompt_name: Name of the prompt file (e.g. 'jd_prompt.md' or just 'jd_prompt')
        **variables: Keyword arguments to format the template with.
    """
    if not prompt_name.endswith(".md"):
        prompt_name += ".md"
        
    # Resolve root prompts directory
    # Path of this file: backend/app/utils/prompt_loader.py
    # Parents: 0 -> utils, 1 -> app, 2 -> backend, 3 -> root
    prompts_dir = Path(__file__).resolve().parents[3] / "prompts"
    prompt_path = prompts_dir / prompt_name
    
    if not prompt_path.exists():
        logger.error(f"Prompt template not found at: {prompt_path}")
        raise FileNotFoundError(f"Prompt template '{prompt_name}' not found at {prompt_path.absolute()}")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if variables:
        try:
            return content.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing prompt variable {e} for {prompt_name}. Returning unformatted content.")
            return content
            
    return content
