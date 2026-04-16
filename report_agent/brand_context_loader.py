#!/usr/bin/env python3
"""
brand_context_loader.py — Brand Context Loader

Loads brand context from:
- brand_profile.json (structured brand information)
- Phase_4_STORM_Report.md (unstructured STORM report)
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class BrandContextLoader:
    """Loader for brand context information."""
    
    def __init__(self, raw_data_dir: Path = Path("raw_data")):
        """
        Initialize the brand context loader.
        
        Args:
            raw_data_dir: Base directory for raw data
        """
        self.raw_data_dir = raw_data_dir
    
    def load_brand_context(
        self, 
        campaign_name: str, 
        brand: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load brand context for a campaign.
        
        Args:
            campaign_name: Name of the campaign
            brand: Optional brand name (if not in campaign name)
            
        Returns:
            Dictionary with brand context information
        """
        context = {
            "brand": brand or self._extract_brand_from_campaign(campaign_name),
            "brand_profile": None,
            "storm_report": None,
            "has_context": False
        }
        
        # Try to find brand profile
        brand_profile = self._find_brand_profile(campaign_name, brand)
        if brand_profile:
            context["brand_profile"] = brand_profile
            context["has_context"] = True
        
        # Try to find STORM report
        storm_report = self._find_storm_report(campaign_name, brand)
        if storm_report:
            context["storm_report"] = storm_report
            context["has_context"] = True
        
        return context
    
    def _extract_brand_from_campaign(self, campaign_name: str) -> str:
        """Extract brand name from campaign name."""
        # Common patterns: "brand_model", "brand_vs_brand", etc.
        parts = campaign_name.replace("_vs_", "_").split("_")
        return parts[0] if parts else "unbekannt"
    
    def _find_brand_profile(
        self, 
        campaign_name: str, 
        brand: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Find and load brand_profile.json."""
        brand_name = brand or self._extract_brand_from_campaign(campaign_name)
        
        # Search for brand profile in raw_data
        if self.raw_data_dir.exists():
            for folder in self.raw_data_dir.iterdir():
                if folder.is_dir():
                    profile_path = folder / "brand_profile.json"
                    if profile_path.exists():
                        try:
                            with open(profile_path, 'r', encoding='utf-8') as f:
                                profile = json.load(f)
                                # Check if brand matches
                                if profile.get("brand", "").lower() == brand_name.lower():
                                    return profile
                        except Exception:
                            continue
        
        return None
    
    def _find_storm_report(
        self, 
        campaign_name: str, 
        brand: Optional[str]
    ) -> Optional[str]:
        """Find and load Phase_4_STORM_Report.md."""
        brand_name = brand or self._extract_brand_from_campaign(campaign_name)
        
        # Search for STORM report in raw_data
        if self.raw_data_dir.exists():
            for folder in self.raw_data_dir.iterdir():
                if folder.is_dir():
                    storm_path = folder / "Phase_4_STORM_Report.md"
                    if storm_path.exists():
                        try:
                            with open(storm_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Check if brand is mentioned
                                if brand_name.lower() in content.lower():
                                    return content
                        except Exception:
                            continue
        
        return None
    
    def load_storm_report(self, storm_path: Path) -> Optional[str]:
        """Load a specific STORM report file."""
        if storm_path.exists():
            try:
                with open(storm_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        return None
    
    def load_brand_profile(self, profile_path: Path) -> Optional[Dict[str, Any]]:
        """Load a specific brand profile file."""
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None


def extract_brand_from_campaign_dir(campaign_dir: Path) -> str:
    """
    Extract brand name from campaign directory path.
    
    Args:
        campaign_dir: Path to campaign directory
        
    Returns:
        Extracted brand name
    """
    # Get campaign name from path
    campaign_name = campaign_dir.name
    
    # Common patterns
    if "_vs_" in campaign_name:
        # "apple_vs_samsung" -> "apple"
        return campaign_name.split("_vs_")[0]
    elif "_" in campaign_name:
        # "nike_2026" -> "nike"
        return campaign_name.split("_")[0]
    
    return campaign_name


def get_brand_context(
    campaign_dir: Path,
    raw_data_dir: Path = Path("raw_data")
) -> Dict[str, Any]:
    """
    Convenience function to get brand context for a campaign.
    
    Args:
        campaign_dir: Path to campaign directory
        raw_data_dir: Base directory for raw data
        
    Returns:
        Dictionary with brand context
    """
    brand = extract_brand_from_campaign_dir(campaign_dir)
    loader = BrandContextLoader(raw_data_dir)
    return loader.load_brand_context(campaign_dir.name, brand)
