#!/usr/bin/env python3
"""
report_orchestrator.py — Main Entry Point for Report Generation

Coordinates all interpreters and generates comprehensive reports.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from config_core import MODEL_JUDGE, ask_llm

from report_agent.brand_context_loader import BrandContextLoader, extract_brand_from_campaign_dir
from report_agent.interpreters.tribe_interpreter import TribeInterpreter
from report_agent.interpreters.mirofish_interpreter import MiroFishInterpreter
from report_agent.interpreters.clip_interpreter import ClipInterpreter
from report_agent.interpreters.vinet_interpreter import ViNetInterpreter
from report_agent.report_builder import ReportBuilder, generate_master_summary, generate_final_recommendations


class ReportOrchestrator:
    """Orchestrator for multi-module report generation."""
    
    def __init__(
        self, 
        campaign_dir: Path,
        brand: Optional[str] = None,
        raw_data_dir: Path = Path("raw_data"),
        output_dir: Path = Path("reports")
    ):
        """
        Initialize the report orchestrator.
        
        Args:
            campaign_dir: Path to campaign directory
            brand: Optional brand name
            raw_data_dir: Base directory for raw data
            output_dir: Directory for output reports
        """
        self.campaign_dir = campaign_dir
        self.brand = brand or extract_brand_from_campaign_dir(campaign_dir)
        self.raw_data_dir = raw_data_dir
        self.output_dir = output_dir
        
        # Initialize interpreters
        self.interpreters = {
            "tribe": TribeInterpreter(),
            "mirofish": MiroFishInterpreter(),
            "clip": ClipInterpreter(),
            "vinet": ViNetInterpreter()
        }
        
        # Load brand context
        self.brand_context = self._load_brand_context()
        
        # Report builder
        self.report_builder = ReportBuilder(
            campaign_name=campaign_dir.name,
            brand=self.brand
        )
    
    def _load_brand_context(self) -> Dict[str, Any]:
        """Load brand context from files."""
        loader = BrandContextLoader(self.raw_data_dir)
        return loader.load_brand_context(self.campaign_dir.name, self.brand)
    
    def _get_scores_path(self, module_name: str) -> Path:
        """Get scores path for a module."""
        return self.campaign_dir / "scores"
    
    def _load_module_scores(
        self, 
        module_name: str,
        interpreter
    ) -> List[Dict[str, Any]]:
        """
        Load scores for a module from all assets.
        
        Args:
            module_name: Name of the module
            interpreter: Interpreter instance
            
        Returns:
            List of score dictionaries
        """
        scores_dir = self._get_scores_path(module_name)
        if not scores_dir.exists():
            return []
        
        scores_list = []
        
        # MiroFish: Load from pipeline_results_final.json
        if module_name == "mirofish":
            results_path = scores_dir / "pipeline_results_final.json"
            if results_path.exists():
                with open(results_path) as f:
                    pipeline_results = json.load(f)
                # Return all assets with mirofish_score
                return [{"asset_path": item.get("asset_path", "unknown"), **item} for item in pipeline_results
                        if "mirofish" in item]
            return []
        
        # ViNet: Primary pattern is *_saliency_scores.json
        if module_name == "vinet":
            score_files = list(scores_dir.glob("*_saliency_scores.json"))
        else:
            # Other modules: *_module_scores.json
            score_files = list(scores_dir.glob(f"*_{module_name}_scores.json"))
        
        for score_file in score_files:
            try:
                scores = interpreter.load_scores(score_file)
                scores_list.append(scores)
            except Exception as e:
                print(f"Warning: Could not load {score_file.name}: {e}")
                continue
        
        return scores_list
    
    async def run_module_interpreter(
        self, 
        module_name: str,
        interpreter
    ) -> Dict[str, Any]:
        """
        Run a single module interpreter.
        
        Args:
            module_name: Name of the module
            interpreter: Interpreter instance
            
        Returns:
            Analysis result dictionary
        """
        scores_list = self._load_module_scores(module_name, interpreter)
        if module_name == "mirofish" and scores_list:
            transformed = []
            for item in scores_list:
                miro = item.get("mirofish", {})
                llm = miro.get("llm_scores", {})
                sentiment = llm.get("positive_sentiment", 0.5)
                virality = llm.get("virality_score", 0.5)
                score = round(sentiment * 0.6 + virality * 0.4, 3)
                grade = "A" if score >= 0.85 else "B" if score >= 0.70 else "C"
                transformed.append({
                    "asset_path": item.get("asset_path", "unknown"),
                    "social_score": score,
                    "grade": grade,
                    "resonance_metrics": {
                        "target_audience_match": sentiment,
                        "emotional_resonance": sentiment,
                        "shareability": virality,
                        "brand_affinity": 1 - llm.get("controversy_risk", 0.2)
                    }
                })
            scores_list = transformed
        # Transform MiroFish data to expected format
        if module_name == "mirofish" and scores_list:
            transformed = []
            for item in scores_list:
                miro = item.get("mirofish", {})
                llm = miro.get("llm_scores", {})
                sentiment = llm.get("positive_sentiment", 0.5)
                virality = llm.get("virality_score", 0.5)
                transformed.append({"asset_path": item.get("asset_path", "unknown"), "social_score": round(sentiment * 0.6 + virality * 0.4, 3), "grade": "A" if (sentiment*0.6+virality*0.4) >= 0.85 else "B" if (sentiment*0.6+virality*0.4) >= 0.70 else "C", "resonance_metrics": {"target_audience_match": sentiment, "emotional_resonance": sentiment, "shareability": virality, "brand_affinity": 1 - llm.get("controversy_risk", 0.2)}})
            scores_list = transformed
        
        if not scores_list:
            return {
                "module": module_name,
                "status": "no_data",
                "summary": f"No {module_name} scores found",
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "creative_rankings": []
            }
        
        # Interpret scores
        analysis_results = []
        for scores in scores_list:
            result = interpreter.interpret(scores, self.brand_context)
            analysis_results.append(result)
        
        # Combine results
        combined_analysis = self._combine_module_results(analysis_results)
        
        return {
            "module": module_name,
            "status": "success",
            "summary": combined_analysis.get("summary", ""),
            "strengths": combined_analysis.get("strengths", []),
            "weaknesses": combined_analysis.get("weaknesses", []),
            "recommendations": combined_analysis.get("recommendations", []),
            "creative_rankings": combined_analysis.get("creative_rankings", []),
            "metrics": combined_analysis.get("metrics", {})
        }
    
    def _combine_module_results(
        self, 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Combine results from multiple creatives for a module."""
        if not results:
            return {}
        
        # Take the first result as base
        combined = results[0].copy()
        
        # Combine strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        all_recommendations = []
        
        for result in results:
            all_strengths.extend(result.get("strengths", []))
            all_weaknesses.extend(result.get("weaknesses", []))
            all_recommendations.extend(result.get("recommendations", []))
        
        combined["strengths"] = list(set(all_strengths))
        combined["weaknesses"] = list(set(all_weaknesses))
        combined["recommendations"] = list(set(all_recommendations))
        
        return combined
    
    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate complete report for the campaign.
        
        Returns:
            Report dictionary
        """
        print(f"📊 Generating report for campaign: {self.campaign_dir.name}")
        print(f"   Brand: {self.brand}")
        print()
        
        # 1. Run all interpreters in parallel
        print("🚀 Running module interpreters...")
        interpreter_tasks = [
            self.run_module_interpreter(name, interp)
            for name, interp in self.interpreters.items()
        ]
        module_results = []
        for task in interpreter_tasks:
            module_results.append(await task)
        
        # 2. Store module analyses
        for result in module_results:
            module_name = result["module"]
            if result["status"] == "success":
                self.report_builder.add_module_analysis(module_name, result)
                print(f"   ✓ {module_name}: {len(result.get('creative_rankings', []))} creatives analyzed")
            else:
                print(f"   ⚠ {module_name}: {result['summary']}")
        
        print()
        
        # 3. Generate overall ranking
        print("🏆 Generating overall ranking...")
        overall_ranking = self._generate_overall_ranking(module_results)
        self.report_builder.set_overall_ranking(overall_ranking)
        
        # 4. Generate master summary
        print("🧠 Generating master summary...")
        master_summary = generate_master_summary(
            self.report_builder.module_analyses,
            self.brand
        )
        self.report_builder.set_master_summary(master_summary)
        
        # 5. Generate final recommendations
        print("💡 Generating recommendations...")
        recommendations = generate_final_recommendations(
            self.report_builder.module_analyses,
            self.brand
        )
        self.report_builder.set_recommendations(recommendations)
        
        # 6. Generate output files
        print()
        print("📝 Generating output files...")
        output_paths = self.report_builder.generate_all_reports(self.output_dir)
        
        print(f"   ✓ JSON: {output_paths['json']}")
        print(f"   ✓ Markdown: {output_paths['markdown']}")
        
        return {
            "campaign": self.campaign_dir.name,
            "brand": self.brand,
            "output_paths": output_paths,
            "module_results": module_results
        }
    
    def _generate_overall_ranking(
        self, 
        module_results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate overall creative ranking from all modules.
        
        Args:
            module_results: List of module analysis results
            
        Returns:
            List of creative paths ranked by overall performance
        """
        # Collect all creative paths
        all_creatives = set()
        for result in module_results:
            if result["status"] == "success":
                for ranking in result.get("creative_rankings", []):
                    if isinstance(ranking, str):
                        all_creatives.add(ranking)
                    elif isinstance(ranking, dict):
                        all_creatives.add(ranking.get("asset_path", ""))
        
        if not all_creatives:
            return []
        
        # Score each creative
        creative_scores = {}
        for creative in all_creatives:
            score = 0
            for result in module_results:
                if result["status"] == "success":
                    rankings = result.get("creative_rankings", [])
                    for i, ranking in enumerate(rankings):
                        if isinstance(ranking, str) and ranking == creative:
                            score += len(rankings) - i  # Higher score for better rank
                        elif isinstance(ranking, dict) and ranking.get("asset_path") == creative:
                            score += ranking.get("composite_score", 0) * 100
            
            creative_scores[creative] = score
        
        # Sort by score
        sorted_creatives = sorted(
            creative_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [creative for creative, _ in sorted_creatives]


async def generate_report(
    campaign_name: str,
    brand: Optional[str] = None,
    campaign_base_dir: Path = Path("campaigns"),
    raw_data_dir: Path = Path("raw_data"),
    output_dir: Path = Path("reports")
) -> Dict[str, Any]:
    """
    Main entry point for report generation.
    
    Args:
        campaign_name: Name of the campaign
        brand: Optional brand name
        campaign_base_dir: Base directory for campaigns
        raw_data_dir: Base directory for raw data
        output_dir: Directory for output reports
        
    Returns:
        Report dictionary with results
    """
    campaign_dir = campaign_base_dir / campaign_name
    
    if not campaign_dir.exists():
        raise FileNotFoundError(f"Campaign directory not found: {campaign_dir}")
    
    orchestrator = ReportOrchestrator(
        campaign_dir=campaign_dir,
        brand=brand,
        raw_data_dir=raw_data_dir,
        output_dir=output_dir
    )
    
    return await orchestrator.generate_report()


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate NeuroAd campaign reports"
    )
    parser.add_argument(
        "campaign",
        help="Name of the campaign directory"
    )
    parser.add_argument(
        "--brand",
        help="Brand name (optional, auto-detected if not provided)"
    )
    parser.add_argument(
        "--campaign-dir",
        default="campaigns",
        help="Base directory for campaigns (default: campaigns)"
    )
    parser.add_argument(
        "--raw-data-dir",
        default="raw_data",
        help="Base directory for raw data (default: raw_data)"
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    
    args = parser.parse_args()
    
    # Run the async function
    result = asyncio.run(generate_report(
        campaign_name=args.campaign,
        brand=args.brand,
        campaign_base_dir=Path(args.campaign_dir),
        raw_data_dir=Path(args.raw_data_dir),
        output_dir=Path(args.output_dir)
    ))
    
    print()
    print("✅ Report generation complete!")
    print(f"   Campaign: {result['campaign']}")
    print(f"   Brand: {result['brand']}")
    print(f"   Output: {result['output_paths']}")


if __name__ == "__main__":
    main()
