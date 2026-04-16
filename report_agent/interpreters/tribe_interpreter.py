#!/usr/bin/env python3
"""
tribe_interpreter.py — TRIBE v2 Score Interpreter

Analyzes TRIBE neural engagement scores and generates:
- Engagement curve analysis (peak, avg, stability)
- Creative comparison based on neural activation
- LLM-powered scientific interpretation
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from report_agent.interpreters.base_interpreter import BaseInterpreter


class TribeInterpreter(BaseInterpreter):
    """Interpreter for TRIBE v2 neural scoring results."""
    
    def __init__(self):
        super().__init__(module_name="tribe")
    
    def load_scores(self, scores_path: Path) -> Dict[str, Any]:
        """
        Load TRIBE scores from JSON file.
        
        Expected format:
        {
            "asset_path": "...",
            "asset_type": "video",
            "neural_engagement": 0.205,
            "emotional_impact": 0.186,
            "face_response": 0.217,
            "scene_response": 0.200,
            "motion_response": 0.192,
            "language_engagement": 0.190,
            "temporal_peak": 31.0,
            "n_segments": 36,
            "brain_map_path": "...",
            "inference_time_s": 32.2
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
        Interpret TRIBE scores and generate analysis.
        
        Args:
            scores: TRIBE scores dictionary
            brand_context: Optional brand profile or STORM report
            
        Returns:
            Dictionary with summary, strengths, weaknesses, recommendations, creative_rankings
        """
        # Calculate engagement metrics
        neural_engagement = scores.get("neural_engagement", 0)
        emotional_impact = scores.get("emotional_impact", 0)
        face_response = scores.get("face_response", 0)
        scene_response = scores.get("scene_response", 0)
        motion_response = scores.get("motion_response", 0)
        language_engagement = scores.get("language_engagement", 0)
        temporal_peak = scores.get("temporal_peak", 0)
        n_segments = scores.get("n_segments", 0)
        
        # Calculate derived metrics
        avg_engagement = (
            neural_engagement + emotional_impact + face_response + 
            scene_response + motion_response + language_engagement
        ) / 6
        
        # Engagement stability (lower variance = more stable)
        engagement_values = [
            neural_engagement, emotional_impact, face_response,
            scene_response, motion_response, language_engagement
        ]
        engagement_std = np.std(engagement_values)
        engagement_stability = 1 - min(engagement_std, 1)  # Normalize to 0-1
        
        # Peak engagement ratio
        peak_ratio = temporal_peak / n_segments if n_segments > 0 else 0
        
        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if neural_engagement > 0.18:
            strengths.append(f"Starke neurale Aktivierung ({neural_engagement:.3f})")
        else:
            weaknesses.append("Niedrige neurale Aktivierung (<0.18)")
        
        if emotional_impact > 0.15:
            strengths.append("Hoher emotionaler Impact")
        else:
            weaknesses.append("Geringer emotionaler Impact")
        
        if face_response > 0.18:
            strengths.append("Starke Gesichts-Response (Fokus auf Menschen)")
        else:
            weaknesses.append("Schwache Gesichts-Response")
        
        if motion_response > 0.18:
            strengths.append("Starke Motion-Response (Bewegungserkennung)")
        else:
            weaknesses.append("Schwache Motion-Response")
        
        if engagement_stability > 0.8:
            strengths.append("Hohe Engagement-Stabilität über den gesamten Videoverlauf")
        else:
            weaknesses.append("Schwankende Engagement-Raten")
        
        # Generate recommendations
        recommendations = []
        if face_response < 0.18:
            recommendations.append("Erhöhen Sie den Fokus auf menschliche Gesichter im Video")
        if motion_response < 0.18:
            recommendations.append("Integrieren Sie mehr dynamische Bewegungselemente")
        if emotional_impact < 0.15:
            recommendations.append("Stärken Sie den emotionalen Call-to-Action")
        if engagement_stability < 0.7:
            recommendations.append("Sorgen Sie für konsistentes Engagement über den gesamten Videoverlauf")
        
        # LLM Analysis
        llm_summary = self._generate_llm_analysis(
            scores=scores,
            avg_engagement=avg_engagement,
            engagement_stability=engagement_stability,
            brand_context=brand_context
        )
        
        return {
            "summary": llm_summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "creative_rankings": [scores.get("asset_path", "unknown")],
            "metrics": {
                "neural_engagement": neural_engagement,
                "emotional_impact": emotional_impact,
                "face_response": face_response,
                "scene_response": scene_response,
                "motion_response": motion_response,
                "language_engagement": language_engagement,
                "avg_engagement": avg_engagement,
                "engagement_stability": engagement_stability,
                "temporal_peak": temporal_peak,
                "n_segments": n_segments,
                "peak_ratio": peak_ratio
            }
        }
    
    def _generate_llm_analysis(
        self,
        scores: Dict[str, Any],
        avg_engagement: float,
        engagement_stability: float,
        brand_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate LLM-powered scientific interpretation."""
        
        brand_info = ""
        if brand_context:
            brand_name = brand_context.get("brand", "unbekannte Marke")
            brand_info = f"Die Analyse bezieht sich auf die Marke '{brand_name}'. "
        
        system_prompt = """Du bist ein Neurowissenschaftler und Werbeexperte. 
Analysiere die TRIBE v2 Scores und erkläre die neurologischen Muster.
Formuliere wissenschaftlich präzise, aber verständlich.
Nutze keine Aufzählungszeichen, sondern fließende Texte."""
        
        user_prompt = f"""Analysiere die folgenden TRIBE v2 Scores für ein Werbevideo:

Neurale Engagement: {scores.get('neural_engagement', 0):.3f}
Emotionaler Impact: {scores.get('emotional_impact', 0):.3f}
Gesichts-Response: {scores.get('face_response', 0):.3f}
Szenen-Response: {scores.get('scene_response', 0):.3f}
Motion-Response: {scores.get('motion_response', 0):.3f}
Sprach-Engagement: {scores.get('language_engagement', 0):.3f}
Durchschnittliches Engagement: {avg_engagement:.3f}
Engagement-Stabilität: {engagement_stability:.3f}
Zeitlicher Peak: {scores.get('temporal_peak', 0)}/{scores.get('n_segments', 0)} Segmente

{brand_info}
Was bedeutet dieses Engagement-Muster für die Werbewirkung?
Welche neurologischen Mechanismen sind aktiv?
Ist das Engagement stabil oder schwankend? Was bedeutet das für die Aufmerksamkeitsdauer?
Gib eine wissenschaftliche Einordnung ab."""
        
        return self.ask_llm(system_prompt, user_prompt)
    
    def compare_creatives(
        self, 
        scores_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple creatives and rank by neural engagement.
        
        Args:
            scores_list: List of TRIBE score dictionaries
            
        Returns:
            List of creative comparisons with rankings and reasoning
        """
        if not scores_list:
            return []
        
        # Calculate composite scores
        creative_scores = []
        for scores in scores_list:
            neural = scores.get("neural_engagement", 0)
            emotional = scores.get("emotional_impact", 0)
            face = scores.get("face_response", 0)
            motion = scores.get("motion_response", 0)
            
            # Weighted composite
            composite = (
                neural * 0.35 +
                emotional * 0.25 +
                face * 0.20 +
                motion * 0.20
            )
            
            creative_scores.append({
                "asset_path": scores.get("asset_path", "unknown"),
                "composite_score": composite,
                "neural_engagement": neural,
                "emotional_impact": emotional,
                "face_response": face,
                "motion_response": motion
            })
        
        # Sort by composite score
        creative_scores.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Generate reasoning
        ranked_list = []
        for i, creative in enumerate(creative_scores):
            reasoning = self._generate_comparative_reasoning(creative, i + 1, creative_scores)
            ranked_list.append({
                "rank": i + 1,
                "asset_path": creative["asset_path"],
                "composite_score": creative["composite_score"],
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
        
        system_prompt = """Du bist ein Werbeeffektivitäts-Experte.
Erkläre warum ein Creative besser/schlechter ist als andere.
Sei präzise und datenbasiert."""
        
        top_score = all_creatives[0]["composite_score"] if all_creatives else 1
        score_diff = (creative["composite_score"] - top_score) / top_score * 100
        
        user_prompt = f"""Das Creative '{creative['asset_path']}' erreicht ein neurales Engagement von {creative['neural_engagement']:.3f}.
Das beste Creative erreicht {top_score:.3f} (Differenz: {score_diff:+.1f}%).

Warum resoniert dieses Creative besser/schlechter mit der Zielgruppe?
Welche spezifischen Elemente (Face-Response, Motion, Emotional Impact) tragen bei?
Gib eine kurze, prägnante Begründung."""
        
        return self.ask_llm(system_prompt, user_prompt)
