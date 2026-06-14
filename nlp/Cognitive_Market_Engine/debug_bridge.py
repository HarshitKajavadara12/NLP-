"""Temporary debug script to inspect NLP sentiment + direction values."""
import sys, os, json
sys.path.insert(0, os.getcwd())
from backtesting.cognitive_signal_bridge import CognitiveSignalBridge
from backtesting.historical_events_generator import HistoricalEventsGenerator

gen = HistoricalEventsGenerator("BTC")
events = gen.generate_events()

bridge = CognitiveSignalBridge("BTC")
bridge.initialize()

for ev in events[:5]:
    sig = bridge.generate_signal(ev)
    a = bridge.event_analyses[-1]
    
    fin_sent = a.nlp_parse.get("financial_sentiment", {})
    aspect_comp = a.nlp_parse.get("aspect_composite_score", 0)
    
    # Phase participant belief shifts 
    phase_bs = {}
    for pk, pr in a.participant_responses.items():
        if pk.startswith("phase_") and isinstance(pr, dict):
            phase_bs[pk] = pr.get("belief_shift", "N/A")
    
    print(f"\n=== {ev.headline[:65]} ===")
    print(f"  FinSent: {json.dumps(fin_sent, default=str)[:120]}")
    print(f"  AspectComp: {aspect_comp:.3f}" if isinstance(aspect_comp, (int,float)) else f"  AspectComp: {aspect_comp}")
    print(f"  Phase BS: {phase_bs}")
    print(f"  -> Direction: {a.final_direction}, Confidence: {a.final_confidence}")
    if sig:
        print(f"  -> TRADE: {sig.action.value} conf={sig.confidence:.3f} size={sig.position_size:.4f}")
    else:
        print(f"  -> No trade")
