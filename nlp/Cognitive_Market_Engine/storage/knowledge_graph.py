"""
KNOWLEDGE GRAPH — NetworkX-based entity relationship graph

Tracks:
- Entities (central banks, companies, people, assets)
- Relationships (influences, correlates, opposes, depends_on)
- Event connections and propagation paths
- Temporal evolution of relationships

Powers scenario generation, hidden truth detection, and causal chain analysis.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple, Any
from collections import defaultdict

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("[KG] WARNING: networkx not installed. Using basic fallback. pip install networkx")


class KnowledgeGraph:
    """
    Financial knowledge graph tracking entities, relationships, and event propagation.
    
    Nodes = entities (Fed, S&P500, USD, etc.)
    Edges = relationships (influences, correlates_with, opposes, etc.)
    
    Features:
    - Temporal relationship tracking
    - Influence propagation simulation
    - Community detection for correlated assets
    - Persistence via JSON
    """
    
    # Relationship types with default weights
    RELATIONSHIP_TYPES = {
        "influences": 0.7,
        "correlates_with": 0.5,
        "opposes": -0.5,
        "depends_on": 0.8,
        "reacts_to": 0.6,
        "competes_with": -0.3,
        "regulates": 0.9,
        "trades_in": 0.4,
        "hedges_against": -0.6,
        "leads": 0.65,
        "lags": 0.45,
        "causes": 0.85,
    }
    
    # Pre-defined entity categories
    ENTITY_TYPES = {
        "central_bank", "government", "company", "index", "currency",
        "commodity", "bond", "crypto", "sector", "region",
        "person", "event_type", "policy", "indicator"
    }
    
    def __init__(self, persist_path: str = None):
        """
        Initialize knowledge graph.
        
        Args:
            persist_path: Path to save/load graph. Defaults to data/knowledge_graph.json
        """
        if persist_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            persist_path = os.path.join(data_dir, "knowledge_graph.json")
        
        self.persist_path = persist_path
        
        if HAS_NETWORKX:
            self.graph = nx.DiGraph()
        else:
            # Fallback: adjacency list
            self._nodes = {}       # node_id -> attributes
            self._edges = {}       # (src, tgt) -> attributes
            self._neighbors = defaultdict(set)
            self.graph = None
        
        self._load_seed_knowledge()
        self._try_load()
        
        print(f"[KG] Initialized: {self.node_count()} nodes, {self.edge_count()} edges")
    
    # ========================================================================
    # CORE GRAPH OPERATIONS
    # ========================================================================
    
    def add_entity(self, entity_id: str, entity_type: str = "unknown", 
                   attributes: Dict = None):
        """
        Add or update an entity node.
        
        Args:
            entity_id: Unique identifier (e.g., "FEDERAL_RESERVE", "SPX", "USD")
            entity_type: Category from ENTITY_TYPES
            attributes: Additional properties
        """
        attrs = {
            "entity_type": entity_type,
            "created_at": datetime.now().isoformat(),
            "mention_count": 1,
            **(attributes or {})
        }
        
        if HAS_NETWORKX:
            if self.graph.has_node(entity_id):
                existing = self.graph.nodes[entity_id]
                existing["mention_count"] = existing.get("mention_count", 0) + 1
                existing.update({k: v for k, v in attrs.items() 
                               if k != "mention_count"})
            else:
                self.graph.add_node(entity_id, **attrs)
        else:
            if entity_id in self._nodes:
                self._nodes[entity_id]["mention_count"] = (
                    self._nodes[entity_id].get("mention_count", 0) + 1
                )
                self._nodes[entity_id].update({k: v for k, v in attrs.items()
                                              if k != "mention_count"})
            else:
                self._nodes[entity_id] = attrs
    
    def add_relationship(self, source: str, target: str, 
                         rel_type: str = "influences",
                         weight: float = None, 
                         evidence: str = None, 
                         event_id: str = None):
        """
        Add or strengthen a relationship edge.
        
        Args:
            source: Source entity
            target: Target entity
            rel_type: Relationship type from RELATIONSHIP_TYPES
            weight: Strength (-1 to 1). Defaults to type's default weight
            evidence: Text evidence for this relationship
            event_id: Event that established this relationship
        """
        # Auto-create nodes
        if not self._has_node(source):
            self.add_entity(source)
        if not self._has_node(target):
            self.add_entity(target)
        
        if weight is None:
            weight = self.RELATIONSHIP_TYPES.get(rel_type, 0.5)
        
        edge_attrs = {
            "rel_type": rel_type,
            "weight": weight,
            "last_updated": datetime.now().isoformat(),
            "observation_count": 1,
        }
        if evidence:
            edge_attrs["last_evidence"] = evidence[:500]
        if event_id:
            edge_attrs["last_event_id"] = event_id
        
        if HAS_NETWORKX:
            if self.graph.has_edge(source, target):
                existing = self.graph[source][target]
                existing["observation_count"] = existing.get("observation_count", 0) + 1
                # Weighted moving average of weight
                alpha = 0.3
                existing["weight"] = alpha * weight + (1 - alpha) * existing.get("weight", 0.5)
                existing["last_updated"] = edge_attrs["last_updated"]
                if evidence:
                    existing["last_evidence"] = edge_attrs["last_evidence"]
                if event_id:
                    existing["last_event_id"] = event_id
            else:
                self.graph.add_edge(source, target, **edge_attrs)
        else:
            key = (source, target)
            if key in self._edges:
                self._edges[key]["observation_count"] = (
                    self._edges[key].get("observation_count", 0) + 1
                )
                alpha = 0.3
                self._edges[key]["weight"] = (
                    alpha * weight + (1 - alpha) * self._edges[key].get("weight", 0.5)
                )
                self._edges[key]["last_updated"] = edge_attrs["last_updated"]
                if evidence:
                    self._edges[key]["last_evidence"] = edge_attrs["last_evidence"]
                if event_id:
                    self._edges[key]["last_event_id"] = event_id
            else:
                self._edges[key] = edge_attrs
                self._neighbors[source].add(target)
    
    def _has_node(self, node_id: str) -> bool:
        if HAS_NETWORKX:
            return self.graph.has_node(node_id)
        return node_id in self._nodes
    
    def node_count(self) -> int:
        if HAS_NETWORKX:
            return self.graph.number_of_nodes()
        return len(self._nodes)
    
    def edge_count(self) -> int:
        if HAS_NETWORKX:
            return self.graph.number_of_edges()
        return len(self._edges)
    
    # ========================================================================
    # ANALYSIS METHODS
    # ========================================================================
    
    def get_influence_chain(self, entity: str, depth: int = 3) -> List[Dict]:
        """
        Trace influence propagation from an entity.
        
        Returns list of {entity, depth, cumulative_influence} dicts.
        """
        results = []
        visited = {entity}
        
        if HAS_NETWORKX:
            frontier = [(entity, 1.0, 0)]
            while frontier:
                current, cum_weight, current_depth = frontier.pop(0)
                if current_depth >= depth:
                    continue
                for successor in self.graph.successors(current):
                    if successor not in visited:
                        edge_weight = self.graph[current][successor].get("weight", 0.5)
                        new_cum = cum_weight * edge_weight
                        if abs(new_cum) > 0.05:
                            results.append({
                                "entity": successor,
                                "depth": current_depth + 1,
                                "cumulative_influence": round(new_cum, 4),
                                "relationship": self.graph[current][successor].get("rel_type", ""),
                                "from": current
                            })
                            visited.add(successor)
                            frontier.append((successor, new_cum, current_depth + 1))
        else:
            frontier = [(entity, 1.0, 0)]
            while frontier:
                current, cum_weight, current_depth = frontier.pop(0)
                if current_depth >= depth:
                    continue
                for neighbor in self._neighbors.get(current, set()):
                    if neighbor not in visited:
                        edge_data = self._edges.get((current, neighbor), {})
                        edge_weight = edge_data.get("weight", 0.5)
                        new_cum = cum_weight * edge_weight
                        if abs(new_cum) > 0.05:
                            results.append({
                                "entity": neighbor,
                                "depth": current_depth + 1,
                                "cumulative_influence": round(new_cum, 4),
                                "relationship": edge_data.get("rel_type", ""),
                                "from": current
                            })
                            visited.add(neighbor)
                            frontier.append((neighbor, new_cum, current_depth + 1))
        
        results.sort(key=lambda x: abs(x["cumulative_influence"]), reverse=True)
        return results
    
    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest directed path between two entities."""
        if not HAS_NETWORKX:
            return None
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_entity_centrality(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get most influential entities by PageRank."""
        if not HAS_NETWORKX:
            # Fallback: sort by mention count
            sorted_nodes = sorted(
                self._nodes.items(),
                key=lambda x: x[1].get("mention_count", 0),
                reverse=True
            )
            return [(n, d.get("mention_count", 0)) for n, d in sorted_nodes[:top_n]]
        
        try:
            pr = nx.pagerank(self.graph, weight="weight")
            sorted_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)
            return sorted_pr[:top_n]
        except Exception:
            return []
    
    def find_communities(self) -> List[Set[str]]:
        """Find clusters of related entities."""
        if not HAS_NETWORKX:
            return []
        
        try:
            undirected = self.graph.to_undirected()
            communities = list(nx.connected_components(undirected))
            return sorted(communities, key=len, reverse=True)
        except Exception:
            return []
    
    def get_correlated_entities(self, entity: str) -> List[Dict]:
        """Get entities correlated with the given entity."""
        results = []
        
        if HAS_NETWORKX:
            # Outgoing
            for successor in self.graph.successors(entity):
                edge = self.graph[entity][successor]
                results.append({
                    "entity": successor,
                    "direction": "influences",
                    "weight": edge.get("weight", 0),
                    "rel_type": edge.get("rel_type", ""),
                })
            # Incoming
            for predecessor in self.graph.predecessors(entity):
                edge = self.graph[predecessor][entity]
                results.append({
                    "entity": predecessor,
                    "direction": "influenced_by",
                    "weight": edge.get("weight", 0),
                    "rel_type": edge.get("rel_type", ""),
                })
        else:
            for neighbor in self._neighbors.get(entity, set()):
                edge = self._edges.get((entity, neighbor), {})
                results.append({
                    "entity": neighbor,
                    "direction": "influences",
                    "weight": edge.get("weight", 0),
                    "rel_type": edge.get("rel_type", ""),
                })
            for (src, tgt), edge in self._edges.items():
                if tgt == entity and src != entity:
                    results.append({
                        "entity": src,
                        "direction": "influenced_by",
                        "weight": edge.get("weight", 0),
                        "rel_type": edge.get("rel_type", ""),
                    })
        
        results.sort(key=lambda x: abs(x["weight"]), reverse=True)
        return results
    
    def detect_conflict_pairs(self) -> List[Dict]:
        """Find entity pairs with opposing relationships."""
        conflicts = []
        
        if HAS_NETWORKX:
            for u, v, data in self.graph.edges(data=True):
                if data.get("weight", 0) < 0 or data.get("rel_type") in ("opposes", "competes_with", "hedges_against"):
                    conflicts.append({
                        "entity_a": u,
                        "entity_b": v,
                        "weight": data.get("weight", 0),
                        "rel_type": data.get("rel_type", ""),
                    })
        else:
            for (src, tgt), data in self._edges.items():
                if data.get("weight", 0) < 0 or data.get("rel_type") in ("opposes", "competes_with", "hedges_against"):
                    conflicts.append({
                        "entity_a": src,
                        "entity_b": tgt,
                        "weight": data.get("weight", 0),
                        "rel_type": data.get("rel_type", ""),
                    })
        
        return conflicts
    
    # ========================================================================
    # EVENT INTEGRATION
    # ========================================================================
    
    def integrate_news_event(self, event_data: Dict):
        """
        Process a news event and update the knowledge graph.
        
        Extracts entities and relationships from parsed event data.
        """
        event_id = event_data.get("event_id", "")
        entities = event_data.get("entities", [])
        triples = event_data.get("triples", [])
        
        # Add entities
        for ent in entities:
            if isinstance(ent, dict):
                self.add_entity(
                    ent.get("text", ent.get("name", "")),
                    ent.get("type", "unknown"),
                    {"source_event": event_id}
                )
            elif isinstance(ent, str):
                self.add_entity(ent, attributes={"source_event": event_id})
        
        # Add relationships from semantic triples
        for triple in triples:
            if isinstance(triple, dict):
                subj = triple.get("subject", "")
                pred = triple.get("predicate", "influences")
                obj = triple.get("object", "")
                conf = triple.get("confidence", 0.5)
                
                if subj and obj:
                    # Map predicate to relationship type
                    rel_type = self._map_predicate(pred)
                    self.add_relationship(
                        subj, obj, rel_type,
                        weight=conf, event_id=event_id,
                        evidence=event_data.get("raw_text", "")[:200]
                    )
        
        # Infer relationships between co-mentioned entities
        entity_names = []
        for ent in entities:
            if isinstance(ent, dict):
                entity_names.append(ent.get("text", ent.get("name", "")))
            elif isinstance(ent, str):
                entity_names.append(ent)
        
        for i in range(len(entity_names)):
            for j in range(i + 1, len(entity_names)):
                if entity_names[i] and entity_names[j]:
                    self.add_relationship(
                        entity_names[i], entity_names[j],
                        "correlates_with", weight=0.3,
                        event_id=event_id
                    )
    
    def _map_predicate(self, predicate: str) -> str:
        """Map NLP predicate to relationship type."""
        pred_lower = predicate.lower()
        
        mapping = {
            "raise": "influences", "cut": "influences",
            "boost": "influences", "lower": "influences",
            "impact": "influences", "affect": "influences",
            "cause": "causes", "lead": "leads",
            "react": "reacts_to", "respond": "reacts_to",
            "regulate": "regulates", "control": "regulates",
            "compete": "competes_with", "rival": "competes_with",
            "oppose": "opposes", "counter": "opposes",
            "hedge": "hedges_against", "protect": "hedges_against",
            "correlate": "correlates_with", "track": "correlates_with",
            "depend": "depends_on", "rely": "depends_on",
            "trade": "trades_in", "buy": "trades_in", "sell": "trades_in",
        }
        
        for keyword, rel_type in mapping.items():
            if keyword in pred_lower:
                return rel_type
        
        return "influences"
    
    # ========================================================================
    # PERSISTENCE
    # ========================================================================
    
    def save(self):
        """Save graph to JSON file."""
        data = {
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "node_count": self.node_count(),
                "edge_count": self.edge_count(),
            }
        }
        
        if HAS_NETWORKX:
            data["nodes"] = []
            for node, attrs in self.graph.nodes(data=True):
                data["nodes"].append({"id": node, **attrs})
            
            data["edges"] = []
            for src, tgt, attrs in self.graph.edges(data=True):
                data["edges"].append({"source": src, "target": tgt, **attrs})
        else:
            data["nodes"] = [{"id": nid, **attrs} for nid, attrs in self._nodes.items()]
            data["edges"] = [{"source": src, "target": tgt, **attrs} 
                           for (src, tgt), attrs in self._edges.items()]
        
        with open(self.persist_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[KG] Saved: {self.node_count()} nodes, {self.edge_count()} edges")
    
    def _try_load(self):
        """Load graph from JSON if exists."""
        if not os.path.exists(self.persist_path):
            return
        
        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)
            
            for node in data.get("nodes", []):
                node_id = node.pop("id")
                if HAS_NETWORKX:
                    self.graph.add_node(node_id, **node)
                else:
                    self._nodes[node_id] = node
            
            for edge in data.get("edges", []):
                src = edge.pop("source")
                tgt = edge.pop("target")
                if HAS_NETWORKX:
                    self.graph.add_edge(src, tgt, **edge)
                else:
                    self._edges[(src, tgt)] = edge
                    self._neighbors[src].add(tgt)
            
            print(f"[KG] Loaded existing graph from {self.persist_path}")
        except Exception as e:
            print(f"[KG] Could not load graph: {e}")
    
    # ========================================================================
    # SEED KNOWLEDGE
    # ========================================================================
    
    def _load_seed_knowledge(self):
        """Load fundamental financial relationships."""
        seed_entities = {
            # Central Banks
            "FEDERAL_RESERVE": "central_bank",
            "ECB": "central_bank",
            "BOJ": "central_bank",
            "BOE": "central_bank",
            "PBOC": "central_bank",
            
            # Indices
            "SPX": "index", "NASDAQ": "index", "DJIA": "index",
            "FTSE100": "index", "DAX": "index", "NIKKEI": "index",
            "SHANGHAI_COMP": "index",
            
            # Currencies
            "USD": "currency", "EUR": "currency", "JPY": "currency",
            "GBP": "currency", "CNY": "currency", "CHF": "currency",
            
            # Commodities
            "GOLD": "commodity", "OIL_WTI": "commodity",
            "OIL_BRENT": "commodity", "SILVER": "commodity",
            "COPPER": "commodity", "NATURAL_GAS": "commodity",
            
            # Bonds
            "US_10Y": "bond", "US_2Y": "bond",
            "GERMAN_BUND": "bond", "JGB_10Y": "bond",
            
            # Crypto
            "BTC": "crypto", "ETH": "crypto",
            
            # Indicators
            "CPI": "indicator", "GDP": "indicator",
            "NFP": "indicator", "PMI": "indicator",
            "UNEMPLOYMENT": "indicator", "FED_FUNDS_RATE": "indicator",
        }
        
        for entity_id, entity_type in seed_entities.items():
            self.add_entity(entity_id, entity_type)
        
        seed_relationships = [
            ("FEDERAL_RESERVE", "FED_FUNDS_RATE", "regulates", 0.95),
            ("FEDERAL_RESERVE", "USD", "influences", 0.85),
            ("FEDERAL_RESERVE", "US_10Y", "influences", 0.80),
            ("FEDERAL_RESERVE", "SPX", "influences", 0.70),
            ("FEDERAL_RESERVE", "GOLD", "influences", -0.60),
            
            ("ECB", "EUR", "influences", 0.85),
            ("ECB", "GERMAN_BUND", "influences", 0.80),
            ("ECB", "DAX", "influences", 0.65),
            
            ("BOJ", "JPY", "influences", 0.85),
            ("BOJ", "NIKKEI", "influences", 0.70),
            ("BOJ", "JGB_10Y", "influences", 0.80),
            
            ("USD", "GOLD", "opposes", -0.70),
            ("USD", "EUR", "opposes", -0.65),
            ("USD", "JPY", "opposes", -0.55),
            ("USD", "OIL_WTI", "influences", -0.50),
            
            ("SPX", "NASDAQ", "correlates_with", 0.90),
            ("SPX", "DJIA", "correlates_with", 0.95),
            ("SPX", "FTSE100", "correlates_with", 0.65),
            
            ("OIL_WTI", "OIL_BRENT", "correlates_with", 0.97),
            ("OIL_WTI", "NATURAL_GAS", "correlates_with", 0.40),
            ("GOLD", "SILVER", "correlates_with", 0.85),
            
            ("US_10Y", "US_2Y", "correlates_with", 0.80),
            ("US_10Y", "GERMAN_BUND", "correlates_with", 0.55),
            ("US_10Y", "SPX", "opposes", -0.40),
            
            ("CPI", "FED_FUNDS_RATE", "influences", 0.75),
            ("NFP", "USD", "influences", 0.60),
            ("GDP", "SPX", "influences", 0.55),
            ("UNEMPLOYMENT", "FED_FUNDS_RATE", "influences", -0.50),
            
            ("BTC", "ETH", "correlates_with", 0.80),
            ("BTC", "GOLD", "correlates_with", 0.25),
            ("BTC", "SPX", "correlates_with", 0.35),
        ]
        
        for src, tgt, rel_type, weight in seed_relationships:
            self.add_relationship(src, tgt, rel_type, weight)
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    def get_summary(self) -> Dict:
        """Get graph summary for display."""
        summary = {
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "top_entities": self.get_entity_centrality(10),
            "conflict_pairs": self.detect_conflict_pairs()[:5],
            "communities": len(self.find_communities()),
        }
        
        # Entity type distribution
        type_counts = defaultdict(int)
        if HAS_NETWORKX:
            for _, attrs in self.graph.nodes(data=True):
                type_counts[attrs.get("entity_type", "unknown")] += 1
        else:
            for attrs in self._nodes.values():
                type_counts[attrs.get("entity_type", "unknown")] += 1
        summary["entity_types"] = dict(type_counts)
        
        return summary
