#!/usr/bin/env python3
"""
clip_interpreter.py — CLIP Brand Consistency Score Interpreter

Analyzes CLIP brand consistency scores and generates:
- Brand fit assessment (benchmark: >0.8 = strong, 0.6-0.8 = okay, <0.6 = weak)
- Visual element analysis
- LLM-powered interpretation of brand identity strength
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from report_agent.interpreters.base_interpreter import BaseInterpreter


class ClipInterpreter(BaseInterpreter):
    """Interpreter for CLIP brand consistency scoring results."""
    
    def __init__(self):
        super().__init__(module_name="clip")
        # CLIP benchmark thresholds
        self.BENCHMARKS = {
            "strong": 0.8,
            "okay": 0.6,
            "weak": 0.0
        }
    
    def load_scores(self, scores_path: Path) -> Dict[str, Any]:
        """
        Load CLIP scores from JSON file.
        
        Expected format:
        {
            "asset_path": "...",
            "brand_match_score": 0.200,
            "top_label": "cinematic storytelling",
            "top_label_score": 0.204,
            "all_scores": {
                "sleek minimalist design": 0.197,
                "vibrant colorful energy": 0.198,
                "cinematic storytelling": 0.204,
                "feature demonstration": 0.202,
                "emotional lifestyle": 0.198
            }
        }
        """
        with open(scores_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def interpret(
        self, 
        scores: Dict[str, Any], 
        brand_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Interpret CLIP scores and generate analysis.
        
        Args:
            scores: CLIP scores dictionary
            brand_context: Optional brand profile or STORM report
            
        Returns:
            Dictionary with summary, strengths, weaknesses, recommendations, creative_rankings
        """
        brand_match_score = scores.get("brand_match_score", 0)
        top_label = scores.get("top_label", "unknown")
        top_label_score = scores.get("top_label_score", 0)
        all_scores = scores.get("all_scores", {})
        
        # Determine brand fit category
        brand_fit = self._categorize_brand_fit(brand_match_score)
        
        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if brand_fit == "strong":
            strengths.append(f"Starke Brand-Konsistenz ({brand_match_score:.3f})")
        elif brand_fit == "weak":
            weaknesses.append(f"Schwache Brand-Konsistenz ({brand_match_score:.3f})")
        
        if top_label_score > 0.19:
            strengths.append(f"Klare visuelle Ausrichtung: '{top_label}'")
        else:
            weaknesses.append("Unklare visuelle Ausrichtung")
        
        # Analyze label distribution
        label_scores = list(all_scores.values()) if all_scores else []
        if label_scores:
            score_variance = max(label_scores) - min(label_scores)
            if score_variance < 0.02:
                weaknesses.append("Geringe Label-Diskriminierung (zu viele ähnliche Scores)")
            else:
                strengths.append("Gute Label-Diskriminierung")
        
        # Generate recommendations
        recommendations = []
        if brand_fit == "weak":
            recommendations.append("Stärken Sie die visuelle Brand Identity")
        if top_label_score < 0.18:
            recommendations.append("Vermeiden Sie visuelle Mehrdeutigkeit")
        if score_variance < 0.02 if label_scores else False:
            recommendations.append("Schärfen Sie die visuelle Botschaft")
        
        # LLM Analysis
        llm_summary = self._generate_llm_analysis(
            scores=scores,
            brand_fit=brand_fit,
            brand_context=brand_context
        )
        
        return {
            "summary": llm_summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "creative_rankings": [scores.get("asset_path", "unknown")],
            "metrics": {
                "brand_match_score": brand_match_score,
                "brand_fit": brand_fit,
                "top_label": top_label,
                "top_label_score": top_label_score,
                "all_scores": all_scores
            }
        }
    
    def _categorize_brand_fit(self, score: float) -> str:
        """Categorize brand fit based on score."""
        if score >= self.BENCHMARKS["strong"]:
            return "strong"
        elif score >= self.BENCHMARKS["okay"]:
            return "okay"
        else:
            return "weak"
    
    def _generate_llm_analysis(
        self,
        scores: Dict[str, Any],
        brand_fit: str,
        brand_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate LLM-powered analysis."""
        
        brand_info = ""
        if brand_context:
            brand_name = brand_context.get("brand", "unbekannte Marke")
            brand_info = f"Die Analyse bezieht sich auf die Marke '{brand_name}'. "
        
        system_prompt = """Du bist ein Brand-Identity-Experte.
Analysiere die CLIP Brand Consistency Scores und erkläre die visuellen Elemente.
Formuliere präzise und visuell beschreibend."""
        
        all_scores = scores.get("all_scores", {})
        top_label = scores.get("top_label", "unknown")
        
        user_prompt = f"""Analysiere die folgenden CLIP Brand Consistency Scores für ein Werbevideo:

Brand Match Score: {scores.get('brand_match_score', 0):.3f}
Kategorie: {brand_fit}
Top Label: '{top_label}' (Score: {scores.get('top_label_score', 0):.3f})
Alle Labels:
{chr(10).join(f'  - {label}: {score:.3f}' for label, score in all_scores.items())}

{brand_info}
Welche visuellen Elemente stärken/schwächen die Brand Identity?
Ist die visuelle Botschaft klar und konsistent?
Gib eine Analyse der visuellen Markenwirkung ab."""
        
        return self.ask_llm(system_prompt, user_prompt)
    
    def compare_creatives(
        self, 
        scores_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple creatives by brand consistency.
        
        Args:
            scores_list: List of CLIP score dictionaries
            
        Returns:
            List of creative comparisons with rankings and reasoning
        """
        if not scores_list:
            return []
        
        # Sort by brand match score
        creative_scores = []
        for scores in scores_list:
            brand_match = scores.get("brand_match_score", 0)
            brand_fit = self._categorize_brand_fit(brand_match)
            
            creative_scores.append({
                "asset_path": scores.get("asset_path", "unknown"),
                "brand_match_score": brand_match,
                "brand_fit": brand_fit,
                "top_label": scores.get("top_label", "unknown")
            })
        
        creative_scores.sort(key=lambda x: x["brand_match_score"], reverse=True)
        
        # Generate reasoning
        ranked_list = []
        for i, creative in enumerate(creative_scores):
            reasoning = self._generate_comparative_reasoning(creative, i + 1, creative_scores)
            ranked_list.append({
                "rank": i + 1,
                "asset_path": creative["asset_path"],
                "brand_match_score": creative["brand_match_score"],
                "brand_fit": creative["brand_fit"],
                "reasoning": reasoning
            })
        
        return ranked_list
    
    def _generate_comparative_reasoning(
        self, 
        creative: Dict[str, Any], 
        rank: int,
        all_creatives: List[Dict[str, Any]]
    ) -> str:
        """Generate reasoning for creative ranking."""
        
        system_prompt = """Du bist ein Brand-Identity-Experte.
Erkläre warum ein Creative besser/schlechter ist als andere."""
        
        top_score = all_creatives[0]["brand_match_score"] if all_creatives else 1
        score_diff = (creative["brand_match_score"] - top_score) / top_score * 100
        
        user_prompt = f"""Das Creative '{creative['asset_path']}' erreicht einen Brand Match Score von {creative['brand_match_score']:.3f} (Kategorie: {creative['brand_fit']}).
Das beste Creative erreicht {top_score:.3f} (Differenz: {score_diff:+.1f}%).

Warum hat dieses Creative eine stärkere/schwächere Brand Identity?
Welche visuellen Elemente tragen zur Brand Consistency bei?
Gib eine kurze, prägnante Begründung."""
        
        return self.ask_llm(system_prompt, user_prompt)
