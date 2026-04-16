# brand_profile.py
# Analysiert eine Marke und erstellt ein strukturiertes Profil das den Suchbaum steuert.

import os
import json
import sys
import re
from config_core import ask_llm, MODEL_WORKHORSE, MODEL_JUDGE

def build_brand_profile(brand: str, seed_content: str, save_dir: str) -> dict:
    """
    Analysiert die Marke und erstellt brand_profile.json.
    Nutzt Gemma 4 für die Analyse, DeepSeek R1 zur Validierung.
    
    Returns: profile dict
    """
    print(f"\n🔬 [PHASE 0.3] Erstelle Brand-Profil für '{brand}'...")
    
    # SCHRITT 1: Gemma 4 analysiert die Marke
    profile_prompt = f"""Analysiere die Marke '{brand}' basierend auf diesem Seed-Dokument und gib AUSSCHLIESSLICH ein JSON-Objekt zurück. Kein Text davor oder danach, nur reines JSON.

SEED:
{seed_content[:4000]}

Das JSON muss exakt diese Struktur haben:
{{
  "brand": "{brand}",
  "founding_year": <int, Gründungsjahr oder null wenn unbekannt>,
  "size": "<startup|mid|global>",
  "size_reasoning": "<1 Satz warum diese Größe>",
  "primary_markets": [
    {{"country": "<Ländername>", "language": "<Sprachcode de/en/fr/es/pt/etc>", "depth": "<deep|medium|shallow>"}}
  ],
  "active_languages": ["<Sprachcode>"],
  "industry": "<Hauptbranche>",
  "sub_industries": ["<Teilbranche1>", "<Teilbranche2>"],
  "key_competitors": ["<Competitor1>", "<Competitor2>"],
  "historical_periods": [
    {{"label": "<Zeitraum z.B. Founding>", "from_year": <int>, "to_year": <int>, "priority": "<high|medium|low>"}}
  ],
  "query_volume": {{
    "pillars": <int, Anzahl Forschungssäulen: startup=8, mid=12, global=20>,
    "queries_per_pillar": <int, startup=8, mid=12, global=20>,
    "social_depth": "<light|medium|deep>"
  }}
}}

Regeln:
- size=startup: <50M€ Umsatz oder <5 Jahre alt oder nur 1-2 Märkte
- size=mid: 50-500M€ Umsatz oder 5-15 Jahre alt oder 3-10 Märkte  
- size=global: >500M€ Umsatz oder >15 Jahre alt oder >10 Märkte
- primary_markets: maximal 5 Einträge, depth=deep für Heimatmarkt, medium für Top-3, shallow für Rest
- historical_periods: aufsteigend nach from_year, lückenlos von Gründung bis heute
- Gib NUR das JSON zurück, absolut nichts anderes"""

    raw = ask_llm(profile_prompt, f"Erstelle Brand-Profil für {brand}", MODEL_WORKHORSE)
    
    # JSON aus Antwort extrahieren
    profile = None
    
    # Versuche direktes JSON-Parsing
    try:
        profile = json.loads(raw.strip())
    except:
        # Suche JSON-Block in der Antwort
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                profile = json.loads(json_match.group())
            except:
                pass
    
    # Fallback wenn JSON-Parsing fehlschlägt
    if not profile:
        print(f"   ⚠️ JSON-Parsing fehlgeschlagen, nutze Fallback-Profil...")
        current_year = 2026
        founding = None
        profile = {
            "brand": brand,
            "founding_year": founding,
            "size": "mid",
            "size_reasoning": "Fallback-Profil da JSON-Parsing fehlschlug",
            "primary_markets": [{"country": "Deutschland", "language": "de", "depth": "deep"}],
            "active_languages": ["de", "en"],
            "industry": "Consumer Goods",
            "sub_industries": [],
            "key_competitors": [],
            "historical_periods": [
                {"label": "Gründung & Frühphase", "from_year": 2015, "to_year": 2020, "priority": "medium"},
                {"label": "Scale-up", "from_year": 2020, "to_year": 2024, "priority": "high"},
                {"label": "Aktuell", "from_year": 2024, "to_year": current_year, "priority": "high"}
            ],
            "query_volume": {"pillars": 12, "queries_per_pillar": 12, "social_depth": "medium"}
        }
    
    # BUG 1 FIX: founding_year nachermitteln wenn null
    if not profile.get("founding_year"):
        year_prompt = f"""In welchem Jahr wurde die Marke '{brand}' gegründet?
Nutze diesen Text: {seed_content[:2000]}
Antworte NUR mit einer vierstelligen Jahreszahl oder 'unbekannt'. Kein anderer Text."""
        year_raw = ask_llm(year_prompt, "Ermittle Gründungsjahr.", MODEL_WORKHORSE).strip()
        try:
            year = int(re.search(r'\d{4}', year_raw).group())
            if 1900 < year < 2026:
                profile["founding_year"] = year
                print(f"   ✅ Gründungsjahr nachermittelt: {year}")
        except:
            pass

    # Wenn historical_periods leer oder from_year null:
    if profile.get("founding_year"):
        current_year = 2026
        founding = profile["founding_year"]
        age = current_year - founding
        
        # Perioden nur neu generieren wenn sie null-Werte enthalten
        has_nulls = any(p.get("from_year") is None for p in profile.get("historical_periods", []))
        if has_nulls or not profile.get("historical_periods"):
            if age <= 5:
                profile["historical_periods"] = [
                    {"label": "Gründung & Launch", "from_year": founding, "to_year": founding + 2, "priority": "high"},
                    {"label": "Wachstumsphase", "from_year": founding + 2, "to_year": current_year, "priority": "high"}
                ]
            elif age <= 10:
                mid = founding + (age // 2)
                profile["historical_periods"] = [
                    {"label": "Gründung & Early Stage", "from_year": founding, "to_year": mid, "priority": "high"},
                    {"label": "Scale-up", "from_year": mid, "to_year": current_year - 2, "priority": "high"},
                    {"label": "Aktuell", "from_year": current_year - 2, "to_year": current_year, "priority": "high"}
                ]
            else:
                profile["historical_periods"] = [
                    {"label": "Gründungsphase", "from_year": founding, "to_year": founding + 5, "priority": "medium"},
                    {"label": "Etablierungsphase", "from_year": founding + 5, "to_year": founding + 10, "priority": "medium"},
                    {"label": "Wachstumsphase", "from_year": founding + 10, "to_year": current_year - 3, "priority": "high"},
                    {"label": "Aktuell", "from_year": current_year - 3, "to_year": current_year, "priority": "high"}
                ]
            print(f"   ✅ Historische Perioden generiert: {len(profile['historical_periods'])} Abschnitte")
    
    # SCHRITT 2: DeepSeek R1 validiert das Profil
    print(f"   🧐 DeepSeek R1 validiert das Brand-Profil...")
    validation_prompt = f"""Du bist ein Brand-Analyst. Prüfe dieses automatisch generierte Brand-Profil für '{brand}' auf Korrektheit.

PROFIL:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Antworte NUR mit einem JSON-Objekt:
{{
  "approved": <true|false>,
  "corrections": {{
    "founding_year": <korrigierter Wert oder null wenn korrekt>,
    "size": "<korrigierter Wert oder null wenn korrekt>",
    "primary_markets_missing": ["<fehlender Markt>"],
    "notes": "<kurze Begründung>"
  }}
}}"""
    
    validation_raw = ask_llm(validation_prompt, f"Validiere Brand-Profil für {brand}", MODEL_JUDGE)
    
    try:
        json_match = re.search(r'\{.*\}', validation_raw, re.DOTALL)
        if json_match:
            validation = json.loads(json_match.group())
            corrections = validation.get("corrections", {})
            
            # Korrekturen anwenden
            if corrections.get("founding_year"):
                profile["founding_year"] = corrections["founding_year"]
                print(f"   ✅ Gründungsjahr korrigiert: {corrections['founding_year']}")
            if corrections.get("size"):
                profile["size"] = corrections["size"]
                print(f"   ✅ Size korrigiert: {corrections['size']}")
            if corrections.get("notes"):
                profile["validation_notes"] = corrections["notes"]
            
            # FIX 1: Size normalisieren (large → global, small → startup, etc.)
            size_normalization = {
                "large": "global",
                "big": "global",
                "small": "startup",
                "medium": "mid",
                "enterprise": "global",
            }
            current_size = profile.get("size", "mid")
            if current_size in size_normalization:
                profile["size"] = size_normalization[current_size]
                profile["query_volume"]["pillars"] = {"startup": 8, "mid": 12, "global": 20}.get(profile["size"], 12)
                profile["query_volume"]["queries_per_pillar"] = {"startup": 8, "mid": 12, "global": 20}.get(profile["size"], 12)
                print(f"   ✅ Size normalisiert: {current_size} → {profile['size']}")
            
            # FIX 2: Perioden neu generieren wenn founding_year korrigiert wurde
            corrected_founding = profile.get("founding_year")
            has_nulls = any(p.get("from_year") is None for p in profile.get("historical_periods", []))
            periods_start_wrong = (
                profile.get("historical_periods") and
                profile["historical_periods"][0].get("from_year") and
                corrected_founding and
                profile["historical_periods"][0]["from_year"] != corrected_founding and
                profile["historical_periods"][0]["from_year"] < corrected_founding - 1
            )
            
            if has_nulls or periods_start_wrong:
                current_year = 2026
                founding = corrected_founding
                age = current_year - founding
                
                if age <= 5:
                    profile["historical_periods"] = [
                        {"label": "Gründung & Launch", "from_year": founding, "to_year": founding + 2, "priority": "high"},
                        {"label": "Wachstumsphase", "from_year": founding + 2, "to_year": current_year, "priority": "high"}
                    ]
                elif age <= 10:
                    mid = founding + (age // 2)
                    profile["historical_periods"] = [
                        {"label": "Gründung & Early Stage", "from_year": founding, "to_year": mid, "priority": "high"},
                        {"label": "Scale-up", "from_year": mid, "to_year": current_year - 2, "priority": "high"},
                        {"label": "Aktuell", "from_year": current_year - 2, "to_year": current_year, "priority": "high"}
                    ]
                else:
                    profile["historical_periods"] = [
                        {"label": "Gründungsphase", "from_year": founding, "to_year": founding + 5, "priority": "medium"},
                        {"label": "Etablierungsphase", "from_year": founding + 5, "to_year": founding + 10, "priority": "medium"},
                        {"label": "Wachstumsphase", "from_year": founding + 10, "to_year": current_year - 3, "priority": "high"},
                        {"label": "Aktuell", "from_year": current_year - 3, "to_year": current_year, "priority": "high"}
                    ]
                print(f"   ✅ Historische Perioden korrigiert: {len(profile['historical_periods'])} Abschnitte (ab {founding})")
            
            # BUG 3 FIX: Fehlende Märkte aus primary_markets_missing ergänzen
            missing_markets = corrections.get("primary_markets_missing", [])
            if missing_markets:
                existing_countries = [m["country"] for m in profile.get("primary_markets", [])]
                for market_name in missing_markets:
                    if market_name not in existing_countries:
                        # Sprache aus Marktname ableiten
                        lang_map = {
                            "Österreich": "de", "Austria": "de",
                            "Schweiz": "de", "Switzerland": "de",
                            "UK": "en", "United Kingdom": "en",
                            "USA": "en", "Frankreich": "fr", "France": "fr",
                            "Spanien": "es", "Spain": "es",
                            "Italien": "it", "Italy": "it",
                        }
                        lang = lang_map.get(market_name, "en")
                        profile["primary_markets"].append({
                            "country": market_name,
                            "language": lang,
                            "depth": "medium"
                        })
                        print(f"   ✅ Markt hinzugefügt: {market_name}")

            # BUG 3 FIX: validation_notes auf Markt-Erwähnungen scannen
            notes = corrections.get("notes", "")
            if notes:
                market_hints = {
                    "Österreich": {"country": "Österreich", "language": "de", "depth": "medium"},
                    "Schweiz": {"country": "Schweiz", "language": "de", "depth": "medium"},
                    "Austria": {"country": "Österreich", "language": "de", "depth": "medium"},
                    "Switzerland": {"country": "Schweiz", "language": "de", "depth": "medium"},
                    "UK": {"country": "United Kingdom", "language": "en", "depth": "medium"},
                    "United Kingdom": {"country": "United Kingdom", "language": "en", "depth": "medium"},
                }
                existing_countries = [m["country"] for m in profile.get("primary_markets", [])]
                for keyword, market_entry in market_hints.items():
                    if keyword in notes and market_entry["country"] not in existing_countries:
                        profile["primary_markets"].append(market_entry)
                        print(f"   ✅ Markt aus Notes hinzugefügt: {market_entry['country']}")
                
    except Exception as e:
        print(f"   ⚠️ Validierung fehlgeschlagen: {e}")
    
    # BUG 2 FIX: Regelbasierte Size-Nachprüfung als Safety Net
    founding = profile.get("founding_year")
    markets = len(profile.get("primary_markets", []))
    current_year = 2026
    age = (current_year - founding) if founding else None
    
    current_size = profile.get("size", "mid")
    
    # Upgrade-Regeln: wenn mindestens eine Bedingung für größere Kategorie zutrifft
    if current_size == "startup":
        if (age and age > 7) or markets >= 4:
            profile["size"] = "mid"
            profile["query_volume"]["pillars"] = 12
            profile["query_volume"]["queries_per_pillar"] = 12
            print(f"   ✅ Size auf 'mid' hochgestuft (Alter: {age}J, Märkte: {markets})")
    if current_size == "mid":
        if (age and age > 15) or markets >= 8:
            profile["size"] = "global"
            profile["query_volume"]["pillars"] = 20
            profile["query_volume"]["queries_per_pillar"] = 20
            print(f"   ✅ Size auf 'global' hochgestuft")
    
    # Speichern
    profile_path = os.path.join(save_dir, "brand_profile.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Brand-Profil erstellt: size={profile['size']}, märkte={len(profile['primary_markets'])}, pillars={profile['query_volume']['pillars']}")
    return profile
