"""
Odin Knowledge Graph Intelligence Engine

A library for intelligent knowledge graph exploration using:
- Personalized PageRank (PPR) for structural importance
- Beam Search for efficient path finding
- NPLL (Neural Probabilistic Logic Learning) for semantic plausibility

Usage:
    from odin import OdinEngine
    
    engine = OdinEngine(db=my_arango_db)
    results = engine.retrieve(seeds=["Patient_123"])
    score = engine.score_edge("Patient_A", "treated_by", "Dr_Smith")
"""

from .engine import OdinEngine

__all__ = ["OdinEngine"]
__version__ = "1.0.0"
