#!/usr/bin/env python3
"""
report_builder.py — Report Generator for NeuroAd Pipeline Results

Generates structured outputs:
1. JSON Report (for dashboard integration)
2. Markdown Report (for human-readable analysis)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config_core import MODEL_JUDGE, ask_llm


class ReportBuilder:
    """Builder for JSON and Markdown reports."""
    
    def __init__(self, campaign_name: str, brand: Optional[str] = None):
        """
        Initialize the report builder.
        
        Args:
            campaign_name: Name of the campaign
            brand: Optional brand name
        """
        self.campaign_name = campaign_name
        self.brand = brand or "unbekannt"
        self.generated_at = datetime.now().isoformat()
        
        # Module data storage
        self.module_analyses: Dict[str, Dict[str, Any]] = {}
        self.creative_rankings: Dict[str, List[str]] = {}
        self.overall_ranking: List[str] = []
        self.master_summary: str = ""
        self.recommendations: List[str] = []
    
    def add_module_analysis(
        self, 
        module_name: str, 
        analysis: Dict[str, Any]
    ) -> None:
        """
        Add analysis result from a module interpreter.
        
        Args:
            module_name: Name of the module (tribe, mirofish, clip, vinet)
            analysis: Analysis dictionary from interpreter
        """
        self.module_analyses[module_name] = analysis
        
        # Extract creative rankings
        if "creative_rankings" in analysis:
            self.creative_rankings[module_name] = analysis["creative_rankings"]
    
    def set_overall_ranking(self, ranking: List[str]) -> None:
        """Set the overall creative ranking."""
        self.overall_ranking = ranking
    
    def set_master_summary(self, summary: str) -> None:
        """Set the master summary from the LLM."""
        self.master_summary = summary
    
    def set_recommendations(self, recommendations: List[str]) -> None:
        """Set the final recommendations."""
        self.recommendations = recommendations
    
    def generate_json_report(self, output_path: Path) -> Dict[str, Any]:
        """
        Generate JSON report for dashboard integration.
        
        Args:
            output_path: Path to save the JSON file
            
        Returns:
            The generated report dictionary
        """
        report = {
            "campaign": self.campaign_name,
            "brand": self.brand,
            "generated_at": self.generated_at,
            "creative_rankings": {
                "overall": self.overall_ranking,
                "by_module": self.creative_rankings
            },
            "module_analyses": {
                module_name: {
                    "summary": analysis.get("summary", ""),
                    "strengths": analysis.get("strengths", []),
                    "weaknesses": analysis.get("weaknesses", []),
                    "recommendations": analysis.get("recommendations", [])
                }
                for module_name, analysis in self.module_analyses.items()
            },
            "master_summary": self.master_summary,
            "recommendations": self.recommendations
        }
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def generate_markdown_report(self, output_path: Path) -> str:
        """
        Generate Markdown report for human-readable analysis.
        
        Args:
            output_path: Path to save the Markdown file
            
        Returns:
            The generated Markdown string
        """
        md_lines = []
        
        # Header
        md_lines.append(f"# 📊 NeuroAd Campaign Report: {self.campaign_name}")
        md_lines.append("")
        md_lines.append(f"**Brand:** {self.brand}")
        md_lines.append(f"**Generated:** {self.generated_at}")
        md_lines.append("")
        
        # Executive Summary
        md_lines.append("## 📝 Executive Summary")
        md_lines.append("")
        md_lines.append(self.master_summary)
        md_lines.append("")
        
        # Module Analyses
        for module_name, analysis in self.module_analyses.items():
            md_lines.append(f"## 📈 {module_name.upper()} Analysis")
            md_lines.append("")
            
            # Summary
            md_lines.append("### Summary")
            md_lines.append("")
            md_lines.append(analysis.get("summary", "No summary available."))
            md_lines.append("")
            
            # Strengths
            strengths = analysis.get("strengths", [])
            if strengths:
                md_lines.append("### ✅ Strengths")
                md_lines.append("")
                for strength in strengths:
                    md_lines.append(f"- {strength}")
                md_lines.append("")
            
            # Weaknesses
            weaknesses = analysis.get("weaknesses", [])
            if weaknesses:
                md_lines.append("### ⚠️ Weaknesses")
                md_lines.append("")
                for weakness in weaknesses:
                    md_lines.append(f"- {weakness}")
                md_lines.append("")
            
            # Recommendations
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                md_lines.append("### 💡 Recommendations")
                md_lines.append("")
                for rec in recommendations:
                    md_lines.append(f"- {rec}")
                md_lines.append("")
        
        # Overall Ranking
        md_lines.append("## 🏆 Overall Creative Ranking")
        md_lines.append("")
        
        if self.overall_ranking:
            for i, creative in enumerate(self.overall_ranking, 1):
                md_lines.append(f"{i}. **{Path(creative).stem}**")
            md_lines.append("")
        else:
            md_lines.append("No overall ranking available.")
            md_lines.append("")
        
        # Recommendations
        md_lines.append("## 🎯 Key Recommendations")
        md_lines.append("")
        
        if self.recommendations:
            for i, rec in enumerate(self.recommendations, 1):
                md_lines.append(f"{i}. {rec}")
            md_lines.append("")
        else:
            md_lines.append("No specific recommendations available.")
            md_lines.append("")
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_content = "\n".join(md_lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return markdown_content
    
    def generate_all_reports(self, output_dir: Path) -> Dict[str, Path]:
        """
        Generate both JSON and Markdown reports.
        
        Args:
            output_dir: Directory to save reports
            
        Returns:
            Dictionary with paths to generated files
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = output_dir / f"{self.campaign_name}_report.json"
        md_path = output_dir / f"{self.campaign_name}_report.md"
        
        self.generate_json_report(json_path)
        self.generate_markdown_report(md_path)
        
        return {
            "json": json_path,
            "markdown": md_path
        }


def generate_master_summary(
    module_analyses: Dict[str, Dict[str, Any]],
    brand: str
) -> str:
    """
    Generate master summary using LLM.
    
    Args:
        module_analyses: Dictionary of module analysis results
        brand: Brand name
        
    Returns:
        Master summary string
    """
    # Build context from all module analyses
    context_parts = []
    for module_name, analysis in module_analyses.items():
        context_parts.append(f"### {module_name.upper()} Analysis")
        context_parts.append(f"- Summary: {analysis.get('summary', 'N/A')[:500]}")
        context_parts.append(f"- Strengths: {', '.join(analysis.get('strengths', []))}")
        context_parts.append(f"- Weaknesses: {', '.join(analysis.get('weaknesses', []))}")
        context_parts.append("")
    
    context = "\n".join(context_parts)
    
    system_prompt = """Du bist ein Marketing-Experte.
Analysiere die Ergebnisse aller Scoring-Module und generiere eine zusammenfassende Bewertung.
Formuliere präzise, strukturiert und in deutscher Sprache."""
    
    user_prompt = f"""Analysiere die Ergebnisse aller Scoring-Module für die Marke '{brand}':

{context}

Gib eine zusammenfassende Bewertung ab:
1. Was ist die Gesamtwirkung der Werbekampagne?
2. Welche Module zeigen starke Ergebnisse?
3. Welche Module benötigen Verbesserung?
4. Was sind die wichtigsten Handlungsempfehlungen?

Formuliere eine strukturierte Zusammenfassung in deutscher Sprache."""
    
    return ask_llm(system_prompt, user_prompt, MODEL_JUDGE)


def generate_final_recommendations(
    module_analyses: Dict[str, Dict[str, Any]],
    brand: str
) -> List[str]:
    """
    Generate final recommendations using LLM.
    
    Args:
        module_analyses: Dictionary of module analysis results
        brand: Brand name
        
    Returns:
        List of recommendations
    """
    # Collect all recommendations from modules
    all_recommendations = []
    for module_name, analysis in module_analyses.items():
        for rec in analysis.get("recommendations", []):
            all_recommendations.append(f"[{module_name}] {rec}")
    
    context = "\n".join(all_recommendations)
    
    system_prompt = """Du bist ein Marketing-Strategie-Experte.
Aggregiere alle Empfehlungen zu einer konsolidierten Handlungsempfehlungsliste.
Formuliere präzise und umsetzbar."""
    
    user_prompt = f"""Aggregiere die folgenden Empfehlungen für die Marke '{brand}':

{context}

Gib eine konsolidierte Liste von 5-10 Handlungsempfehlungen ab.
Jede Empfehlung sollte konkret und umsetzbar sein."""
    
    response = ask_llm(system_prompt, user_prompt, MODEL_JUDGE)
    
    # Parse response into list
    recommendations = []
    for line in response.strip().split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
            # Remove numbering
            line = line.lstrip('0123456789.-* ')
            if line:
                recommendations.append(line)
    
    return recommendations
