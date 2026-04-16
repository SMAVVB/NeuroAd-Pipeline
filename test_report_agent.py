#!/usr/bin/env python3
"""
Test script for report_agent with apple_vs_samsung campaign.
"""

import sys
sys.path.insert(0, '.')

from report_agent.report_orchestrator import generate_report
import asyncio


async def main():
    print("=" * 60)
    print("NeuroAd Report Agent Test")
    print("=" * 60)
    print()
    
    try:
        result = await generate_report(
            campaign_name='apple_vs_samsung',
            brand='apple_vs_samsung',
            campaign_base_dir='campaigns',
            raw_data_dir='raw_data',
            output_dir='reports'
        )
        
        print()
        print("=" * 60)
        print("✅ Report generation complete!")
        print("=" * 60)
        print()
        print(f"Campaign: {result['campaign']}")
        print(f"Brand: {result['brand']}")
        print(f"Output: {result['output_paths']}")
        print()
        
        # Print module results
        print("Module Results:")
        for module_result in result['module_results']:
            print(f"  - {module_result['module']}: {module_result['status']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
