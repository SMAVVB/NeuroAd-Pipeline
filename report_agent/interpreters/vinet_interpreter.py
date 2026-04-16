#!/usr/bin/env python3
"""
vinet_interpreter.py — ViNet Visual Attention Score Interpreter

Analyzes ViNet visual attention/saliency scores and generates:
- Attention score calculation
- Focal point quality assessment
- LLM-powered analysis of attention direction
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from report_agent.interpreters.base_interpreter import BaseInterpreter


class ViNetInterpreter(BaseInterpreter):
    """Interpreter for ViNet visual attention scoring results."""
    
    def __init__(self):
        super().__init__(module_name="vinet")
        # Attention benchmarks
        self.BENCHMARKS = {
            "excellent": 0.15,
            "good": 0.10,
            "average": 0.05,
            "poor": 0.0
        }
    
    def load_scores(self, scores_path: Path) -> Dict[str, Any]:
        """
        Load ViNet scores from JSON file.
        
        Expected format (saliency_scores.json):
        {
            "asset_path": "...",
            "asset_type": "video",
            "product_attention": 0.0,
            "brand_attention": 0.0,
            "cta_attention": 0.0,
            "roi_scores": {},
            "center_bias": 1.0,
            "temporal_variance": 0.0,
            "mean_saliency": 0.044,
            "saliency_map_path": "...",
            "heatmap_png_path": "...",
            "overlay_png_path": "...",
            "inference_time_s": 6.9
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
        Interpret ViNet scores and generate analysis.
        
        Args:
            scores: ViNet scores dictionary
            brand_context: Optional brand profile or STORM report
            
        Returns:
            Dictionary with summary, strengths, weaknesses, recommendations, creative_rankings
        """
        product_attention = scores.get("product_attention", 0)
        brand_attention = scores.get("brand_attention", 0)
        cta_attention = scores.get("cta_attention", 0)
        center_bias = scores.get("center_bias", 1.0)
        temporal_variance = scores.get("temporal_variance", 0)
        mean_saliency = scores.get("mean_saliency", 0)
        
        # Calculate attention score (weighted composite)
        attention_score = (
            product_attention * 0.35 +
            brand_attention * 0.35 +
            cta_attention * 0.30
        )
        
        # Calculate focal point quality
        focal_point_quality = self._assess_focal_point_quality(
            product_attention, brand_attention, cta_attention, center_bias
        )
        
        # Determine attention category
        attention_category = self._categorize_attention(attention_score)
        
        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if attention_category in ["excellent", "good"]:
            strengths.append(f"Starke Aufmerksamkeitssteuerung ({attention_score:.3f})")
        elif attention_category in ["average", "poor"]:
            weaknesses.append(f"Niedrige Aufmerksamkeitssteuerung ({attention_score:.3f})")
        
        if focal_point_quality == "excellent":
            strengths.append("Hervorragende Fokuspunkt-Qualität")
        elif focal_point_quality == "poor":
            weaknesses.append("Schwache Fokuspunkt-Qualität")
        
        if center_bias > 1.2:
            weaknesses.append("Starke Zentrierungs-Bias (zu zentrierte Komposition)")
        elif center_bias < 0.8:
            strengths.append("Gute Kompositions-Vielfalt")
        
        if temporal_variance < 0.05:
            strengths.append("Konsistente Aufmerksamkeit über den Videoverlauf")
        else:
            weaknesses.append("Schwankende Aufmerksamkeit")
        
        # Generate recommendations
        recommendations = []
        if product_attention < 0.05:
            recommendations.append("Lenken Sie die Aufmerksamkeit stärker auf das Produkt")
        if brand_attention < 0.05:
            recommendations.append("Stärken Sie die Markenpräsenz visuell")
        if cta_attention < 0.05:
            recommendations.append("Machen Sie den Call-to-Action sichtbarer")
        if temporal_variance > 0.1:
            recommendations.append("Sorgen Sie für konsistente Aufmerksamkeitsführung")
        
        # LLM Analysis
        llm_summary = self._generate_llm_analysis(
            scores=scores,
            attention_score=attention_score,
            focal_point_quality=focal_point_quality,
            brand_context=brand_context
        )
        
        return {
            "summary": llm_summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "creative_rankings": [scores.get("asset_path", "unknown")],
            "metrics": {
                "attention_score": attention_score,
                "attention_category": attention_category,
                "focal_point_quality": focal_point_quality,
                "product_attention": product_attention,
                "brand_attention": brand_attention,
                "cta_attention": cta_attention,
                "center_bias": center_bias,
                "temporal_variance": temporal_variance,
                "mean_saliency": mean_saliency
            }
        }
    
    def _categorize_attention(self, score: float) -> str:
        """Categorize attention level based on score."""
        if score >= self.BENCHMARKS["excellent"]:
            return "excellent"
        elif score >= self.BENCHMARKS["good"]:
            return "good"
        elif score >= self.BENCHMARKS["average"]:
            return "average"
        else:
            return "poor"
    
    def _assess_focal_point_quality(
        self, 
        product: float, 
        brand: float, 
        cta: float, 
        center_bias: float
    ) -> str:
        """Assess focal point quality based on attention distribution."""
        total_attention = product + brand + cta
        
        if total_attention < 0.03:
            return "poor"  # No clear focal point
        elif total_attention < 0.08:
            return "average"  # Some focal point but weak
        elif total_attention < 0.15:
            return "good"  # Clear focal point
        else:
            return "excellent"  # Strong focal point
        
        # Also consider center bias
        if center_bias > 1.5 and total_attention < 0.1:
            return "poor"  # Center bias without clear focal elements
    
    def _generate_llm_analysis(
        self,
        scores: Dict[str, Any],
        attention_score: float,
        focal_point_quality: str,
        brand_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate LLM-powered analysis."""
        
        brand_info = ""
        if brand_context:
            brand_name = brand_context.get("brand", "unbekannte Marke")
            brand_info = f"Die Analyse bezieht sich auf die Marke '{brand_name}'. "
        
        system_prompt = """Du bist ein Visual-Attention-Experte.
Analysiere die ViNet Saliency Scores und erkläre die Aufmerksamkeitsverteilung.
Formuliere präzise und visuell beschreibend."""
        
        user_prompt = f"""Analysiere die folgenden ViNet Visual Attention Scores für ein Werbevideo:

Aufmerksamkeitsscore: {attention_score:.3f}
Kategorie: {focal_point_quality}
Produkt-Aufmerksamkeit: {scores.get('product_attention', 0):.3f}
Brand-Aufmerksamkeit: {scores.get('brand_attention', 0):.3f}
CTA-Aufmerksamkeit: {scores.get('cta_attention', 0):.3f}
Center Bias: {scores.get('center_bias', 1.0):.2f}
Zeitliche Varianz: {scores.get('temporal_variance', 0):.3f}

{brand_info}
Lenkt das Creative die Aufmerksamkeit auf die richtigen Elemente?
Sind Produkt, Marke und Call-to-Action ausreichend sichtbar?
Gib eine Analyse der visuellen Aufmerksamkeitsführung ab."""
        
        return self.ask_llm(system_prompt, user_prompt)
    
    def compare_creatives(
        self, 
        scores_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple creatives by visual attention.
        
        Args:
            scores_list: List of ViNet score dictionaries
            
        Returns:
            List of creative comparisons with rankings and reasoning
        """
        if not scores_list:
            return []
        
        # Sort by attention score
        creative_scores = []
        for scores in scores_list:
            attention_score = (
                scores.get("product_attention", 0) * 0.35 +
                scores.get("brand_attention", 0) * 0.35 +
                scores.get("cta_attention", 0) * 0.30
            )
            focal_quality = self._assess_focal_point_quality(
                scores.get("product_attention", 0),
                scores.get("brand_attention", 0),
                scores.get("cta_attention", 0),
                scores.get("center_bias", 1.0)
            )
            
            creative_scores.append({
                "asset_path": scores.get("asset_path", "unknown"),
                "attention_score": attention_score,
                "focal_point_quality": focal_quality,
                "product_attention": scores.get("product_attention", 0),
                "brand_attention": scores.get("brand_attention", 0),
                "cta_attention": scores.get("cta_attention", 0)
            })
        
        creative_scores.sort(key=lambda x: x["attention_score"], reverse=True)
        
        # Generate reasoning
        ranked_list = []
        for i, creative in enumerate(creative_scores):
            reasoning = self._generate_comparative_reasoning(creative, i + 1, creative_scores)
            ranked_list.append({
                "rank": i + 1,
                "asset_path": creative["asset_path"],
                "attention_score": creative["attention_score"],
                "focal_point_quality": creative["focal_point_quality"],
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
        
        system_prompt = """Du bist ein Visual-Design-Experte.
Erkläre warum ein Creative besser/schlechter ist als andere."""
        
        top_score = all_creatives[0]["attention_score"] if all_creatives else 1
        score_diff = (creative["attention_score"] - top_score) / top_score * 100
        
        user_prompt = f"""Das Creative '{creative['asset_path']}' erreicht einen Attention Score von {creative['attention_score']:.3f} (Fokuspunkt-Qualität: {creative['focal_point_quality']}).
Das beste Creative erreicht {top_score:.3f} (Differenz: {score_diff:+.1f}%).

Warum lenkt dieses Creative die Aufmerksamkeit besser/schlechter?
Welche visuellen Elemente (Produkt, Marke, CTA) tragen bei?
Gib eine kurze, prägnante Begründung."""
        
        return self.ask_llm(system_prompt, user_prompt)
