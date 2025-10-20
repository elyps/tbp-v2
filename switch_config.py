#!/usr/bin/env python3
"""
Trading Bot Config Switcher
Wechselt zwischen Conservative, Moderate und Aggressive Trading Settings
"""

import yaml
import sys
from pathlib import Path

# Config Profiles
PROFILES = {
    "conservative": {
        "name": "🛡️ Konservativ",
        "desc": "Wenige, hochqualitative Trades (Original Enhanced Pipeline)",
        "trader_config": {
            "signals": {"p_up": 0.55, "p_dn": 0.55},
            "sizing": {"target_vol": 0.10, "cap": 0.03},
            "risk": {
                "max_pos_per_asset": 0.03,
                "max_gross": 0.6,
                "stop_atr_mult": 2.0,
                "trail_atr_mult": 3.0,
                "day_dd_kill": 0.08
            },
            "backtest": {"fee_bps": 2, "slippage_bps": 6}
        }
    },
    "moderate": {
        "name": "⚖️ Moderat",
        "desc": "Balance zwischen Qualität und Quantität",
        "trader_config": {
            "signals": {"p_up": 0.52, "p_dn": 0.52},
            "sizing": {"target_vol": 0.11, "cap": 0.04},
            "risk": {
                "max_pos_per_asset": 0.04,
                "max_gross": 0.7,
                "stop_atr_mult": 1.8,
                "trail_atr_mult": 2.8,
                "day_dd_kill": 0.10
            },
            "backtest": {"fee_bps": 1, "slippage_bps": 4}
        }
    },
    "aggressive": {
        "name": "⚡ Aggressiv",
        "desc": "Viele Trades, auch kleine Gewinne (Kraken Pro optimiert)",
        "trader_config": {
            "signals": {"p_up": 0.48, "p_dn": 0.48},
            "sizing": {"target_vol": 0.12, "cap": 0.05},
            "risk": {
                "max_pos_per_asset": 0.05,
                "max_gross": 0.8,
                "stop_atr_mult": 1.5,
                "trail_atr_mult": 2.5,
                "day_dd_kill": 0.12
            },
            "backtest": {"fee_bps": 0, "slippage_bps": 2}
        }
    }
}


def update_yaml_config(file_path: Path, updates: dict):
    """Aktualisiert YAML Config-Datei mit neuen Werten"""
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Deep update
    for section, values in updates.items():
        if section in config:
            config[section].update(values)
    
    with open(file_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    return config


def switch_profile(profile_name: str):
    """Wechselt zur angegebenen Config-Profil"""
    if profile_name not in PROFILES:
        print(f"❌ Ungültiges Profil: {profile_name}")
        print(f"Verfügbar: {', '.join(PROFILES.keys())}")
        return False
    
    profile = PROFILES[profile_name]
    project_root = Path(__file__).parent
    trader_config = project_root / "trader" / "config.yaml"
    
    if not trader_config.exists():
        print(f"❌ Config nicht gefunden: {trader_config}")
        return False
    
    print(f"\n{profile['name']}")
    print(f"📋 {profile['desc']}")
    print(f"\n🔄 Aktualisiere Config: {trader_config}")
    
    try:
        update_yaml_config(trader_config, profile['trader_config'])
        print("✅ Config erfolgreich aktualisiert!")
        print("\n⚠️  WICHTIG: Bot neu starten für neue Einstellungen!")
        print("   python main.py")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren: {e}")
        return False


def show_current_config():
    """Zeigt die aktuelle Config an"""
    project_root = Path(__file__).parent
    trader_config = project_root / "trader" / "config.yaml"
    
    if not trader_config.exists():
        print(f"❌ Config nicht gefunden: {trader_config}")
        return
    
    with open(trader_config, 'r') as f:
        config = yaml.safe_load(f)
    
    print("\n📊 Aktuelle Config:")
    print(f"  Confidence Threshold: {config['signals']['p_up']}")
    print(f"  Position Cap: {config['sizing']['cap']}")
    print(f"  Max Gross: {config['risk']['max_gross']}")
    print(f"  Stop ATR Mult: {config['risk']['stop_atr_mult']}")
    print(f"  Fees: {config['backtest']['fee_bps']} bps")
    
    # Detect profile
    p_up = config['signals']['p_up']
    if p_up >= 0.55:
        detected = "conservative"
    elif p_up >= 0.52:
        detected = "moderate"
    else:
        detected = "aggressive"
    
    print(f"\n🎯 Erkanntes Profil: {PROFILES[detected]['name']}")


def show_menu():
    """Zeigt das Hauptmenü"""
    print("\n" + "="*60)
    print("🎮 TRADING BOT CONFIG SWITCHER")
    print("="*60)
    
    show_current_config()
    
    print("\n📋 Verfügbare Profile:")
    for key, profile in PROFILES.items():
        print(f"\n  [{key}] {profile['name']}")
        print(f"      → {profile['desc']}")
    
    print("\n  [show] Aktuelle Config anzeigen")
    print("  [exit] Beenden")
    print("\n" + "="*60)


def main():
    """Hauptfunktion"""
    # Direkte Profil-Auswahl via Argument
    if len(sys.argv) > 1:
        profile = sys.argv[1].lower()
        if profile == "show":
            show_current_config()
        elif profile == "exit":
            return
        else:
            switch_profile(profile)
        return
    
    # Interaktives Menü
    while True:
        show_menu()
        choice = input("\n👉 Wähle Profil: ").strip().lower()
        
        if choice == "exit":
            print("👋 Bye!")
            break
        elif choice == "show":
            show_current_config()
        elif choice in PROFILES:
            if switch_profile(choice):
                print("\n✅ Fertig! Bot neu starten:")
                print("   python main.py")
                break
        else:
            print("❌ Ungültige Eingabe!")


if __name__ == "__main__":
    main()
