#!/usr/bin/env python3
"""
mirofish_interpreter.py — MiroFish Social Score Interpreter

Analyzes MiroFish social simulation scores and generates:
- Social resonance comparison
- Grade-based performance assessment (A-F)
- LLM-powered analysis of why creatives resonate better
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from report_agent.interpreters.base_interpreter import BaseInterpreter


class MiroFishInterpreter(BaseInterpreter):
    """Interpreter for MiroFish social scoring results."""
    
    def __init__(self):
        super().__init__(module_name="mirofish")
        # Grade thresholds
        self.GRADE_THRESHOLDS = {
            "A": 0.85,
            "B": 0.70,
            "C": 0.55,
            "D": 0.40,
            "F": 0.0
        }
    
    def load_scores(self, scores_path: Path) -> Dict[str, Any]:
        # Handle pipeline_results_final.json format
        pass
    
    def load_scores_from_dict(self, asset_dict: Dict[str, Any]) -> Dict[str, Any]:
        miro = asset_dict.get("mirofish", {})
        llm = miro.get("llm_scores", {})
        sentiment = llm.get("positive_sentiment", 0.5)
        virality = llm.get("virality_score", 0.5)
        social_score = (sentiment * 0.6 + virality * 0.4)
        return {
            "asset_path": asset_dict.get("asset_path", "unknown"),
            "social_score": social_score,
            "grade": self._calculate_grade(social_score),
            "resonance_metrics": {
                "target_audience_match": sentiment,
                "emotional_resonance": sentiment,
                "shareability": virality,
                "brand_affinity": 1 - llm.get("controversy_risk", 0.2)
            }
        }
    
    def _load_scores_file(self, scores_path: Path) -> Dict[str, Any]:
        """
        Load MiroFish scores from JSON file.
        
        Expected format:
        {
            "asset_path": "...",
            "social_score": 0.75,
            "grade": "B",
            "resonance_metrics": {
                "target_audience_match": 0.80,
                "emotional_resonance": 0.72,
                "shareability": 0.68,
                "brand_affinity": 0.75
            },
            "simulated_engagement": {
                "likes": 1250,
                "comments": 85,
                "shares": 45
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
        Interpret MiroFish scores and generate analysis.
        
        Args:
            scores: MiroFish scores dictionary
            brand_context: Optional brand profile or STORM report
            
        Returns:
            Dictionary with summary, strengths, weaknesses, recommendations, creative_rankings
        """
        social_score = scores.get("social_score", 0)
        grade = scores.get("grade", self._calculate_grade(social_score))
        resonance_metrics = scores.get("resonance_metrics", {})
        simulated_engagement = scores.get("simulated_engagement", {})
        
        # Calculate derived metrics
        target_match = resonance_metrics.get("target_audience_match", 0)
        emotional_resonance = resonance_metrics.get("emotional_resonance", 0)
        shareability = resonance_metrics.get("shareability", 0)
        brand_affinity = resonance_metrics.get("brand_affinity", 0)
        
        avg_resonance = (
            target_match + emotional_resonance + shareability + brand_affinity
        ) / 4
        
        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if grade in ["A", "B"]:
            strengths.append(f"Sehr hohe soziale Resonanz (Note: {grade})")
        elif grade in ["D", "F"]:
            weaknesses.append(f"Niedrige soziale Resonanz (Note: {grade})")
        
        if target_match > 0.75:
            strengths.append("Starke Übereinstimmung mit Zielgruppe")
        else:
            weaknesses.append("Geringe Zielgruppenübereinstimmung")
        
        if emotional_resonance > 0.70:
            strengths.append("Hoher emotionaler Resonanz-Effekt")
        else:
            weaknesses.append("Schwacher emotionaler Resonanz-Effekt")
        
        if brand_affinity > 0.70:
            strengths.append("Starke Markenaffinität")
        else:
            weaknesses.append("Schwache Markenaffinität")
        
        # Generate recommendations
        recommendations = []
        if target_match < 0.65:
            recommendations.append("Optimieren Sie die Zielgruppenansprache")
        if emotional_resonance < 0.60:
            recommendations.append("Stärken Sie den emotionalen Call-to-Action")
        if shareability < 0.60:
            recommendations.append("Machen Sie das Creative teilerfreundlicher")
        if brand_affinity < 0.60:
            recommendations.append("Stärken Sie die Markenidentifikation")
        
        # LLM Analysis
        llm_summary = self._generate_llm_analysis(
            scores=scores,
            avg_resonance=avg_resonance,
            brand_context=brand_context
        )
        
        return {
            "summary": llm_summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "creative_rankings": [scores.get("asset_path", "unknown")],
            "metrics": {
                "social_score": social_score,
                "grade": grade,
                "resonance_metrics": resonance_metrics,
                "avg_resonance": avg_resonance,
                "simulated_engagement": simulated_engagement
            }
        }
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from numeric score."""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return "F"
    
    def _generate_llm_analysis(
        self,
        scores: Dict[str, Any],
        avg_resonance: float,
        brand_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate LLM-powered analysis."""
        
        brand_info = ""
        if brand_context:
            brand_name = brand_context.get("brand", "unbekannte Marke")
            brand_info = f"Die Analyse bezieht sich auf die Marke '{brand_name}'. "
        
        system_prompt = """Du bist ein Social-Media-Strategie-Experte.
Analysiere die MiroFish Social Scores und erkläre die Resonanzmuster.
Formuliere präzise und datenbasiert."""
        
        resonance_metrics = scores.get("resonance_metrics", {})
        
        user_prompt = f"""Analysiere die folgenden MiroFish Social Scores für ein Werbevideo:

Soziale Resonanz: {scores.get('social_score', 0):.3f}
Note: {scores.get('grade', 'N/A')}
Durchschnittliche Resonanz: {avg_resonance:.3f}
Zielgruppenübereinstimmung: {resonance_metrics.get('target_audience_match', 0):.3f}
Emotionale Resonanz: {resonance_metrics.get('emotional_resonance', 0):.3f}
Teilbarkeit: {resonance_metrics.get('shareability', 0):.3f}
Markenaffinität: {resonance_metrics.get('brand_affinity', 0):.3f}

{brand_info}
Warum resoniert dieses Creative besser/schlechter mit der Zielgruppe?
Welche Elemente fördern die Teilbarkeit?
Gib eine strategische Einordnung ab."""
        
        return self.ask_llm(system_prompt, user_prompt)
    
    def compare_creatives(
        self, 
        scores_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple creatives by social resonance.
        
        Args:
            scores_list: List of MiroFish score dictionaries
            
        Returns:
            List of creative comparisons with rankings and reasoning
        """
        if not scores_list:
            return []
        
        # Sort by social score
        creative_scores = []
        for scores in scores_list:
            social_score = scores.get("social_score", 0)
            grade = scores.get("grade", self._calculate_grade(social_score))
            
            creative_scores.append({
                "asset_path": scores.get("asset_path", "unknown"),
                "social_score": social_score,
                "grade": grade,
                "resonance_metrics": scores.get("resonance_metrics", {})
            })
        
        creative_scores.sort(key=lambda x: x["social_score"], reverse=True)
        
        # Generate reasoning
        ranked_list = []
        for i, creative in enumerate(creative_scores):
            reasoning = self._generate_comparative_reasoning(creative, i + 1, creative_scores)
            ranked_list.append({
                "rank": i + 1,
                "asset_path": creative["asset_path"],
                "social_score": creative["social_score"],
                "grade": creative["grade"],
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
        
        system_prompt = """Du bist ein Social-Media-Content-Experte.
Erkläre warum ein Creative besser/schlechter ist als andere."""
        
        top_score = all_creatives[0]["social_score"] if all_creatives else 1
        score_diff = (creative["social_score"] - top_score) / top_score * 100
        
        user_prompt = f"""Das Creative '{creative['asset_path']}' erreicht eine soziale Resonanz von {creative['social_score']:.3f} (Note: {creative['grade']}).
Das beste Creative erreicht {top_score:.3f} (Differenz: {score_diff:+.1f}%).

Warum resoniert dieses Creative besser/schlechter mit der Zielgruppe?
Welche spezifischen Resonanz-Elemente (Zielgruppenübereinstimmung, emotionale Resonanz, Teilbarkeit) tragen bei?
Gib eine kurze, prägnante Begründung."""
        
        return self.ask_llm(system_prompt, user_prompt)
