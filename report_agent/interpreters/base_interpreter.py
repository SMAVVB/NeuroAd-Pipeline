#!/usr/bin/env python3
"""
base_interpreter.py — Abstract Base Class for Report Interpreters

Provides the foundation for all module-specific score interpreters.
Each interpreter must implement:
- load_scores(path) → dict
- interpret(scores, brand_context) → dict
- compare_creatives(scores) → ranked list with reasoning
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from config_core import ask_llm, MODEL_WORKHORSE


class BaseInterpreter(ABC):
    """Abstract base class for all score interpreters."""
    
    def __init__(self, module_name: str):
        """
        Initialize the interpreter.
        
        Args:
            module_name: Name of the scoring module (e.g., 'tribe', 'clip')
        """
        self.module_name = module_name
    
    @abstractmethod
    def load_scores(self, scores_path: Path) -> Dict[str, Any]:
        """
        Load scores from JSON file.
        
        Args:
            scores_path: Path to the scores JSON file
            
        Returns:
            Dictionary containing the scores data
        """
        pass
    
    @abstractmethod
    def interpret(
        self, 
        scores: Dict[str, Any], 
        brand_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Interpret scores and generate analysis.
        
        Args:
            scores: Raw scores dictionary
            brand_context: Optional brand profile or STORM report context
            
        Returns:
            Dictionary with keys:
            - summary: Overall assessment
            - strengths: List of key strengths
            - weaknesses: List of key weaknesses
            - recommendations: List of actionable recommendations
            - creative_rankings: List of creatives ranked by performance
        """
        pass
    
    @abstractmethod
    def compare_creatives(
        self, 
        scores_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple creatives and generate rankings.
        
        Args:
            scores_list: List of score dictionaries from multiple creatives
            
        Returns:
            List of creative comparisons with rankings and reasoning
        """
        pass
    
    def ask_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Wrapper for LLM calls using config_core.ask_llm.
        
        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            
        Returns:
            LLM response string
        """
        return ask_llm(system_prompt, user_prompt, MODEL_WORKHORSE)
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Helper to load JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
