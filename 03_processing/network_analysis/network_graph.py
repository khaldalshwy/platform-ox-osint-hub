from typing import List, Dict, Any, Tuple

class EntityNetworkGraph:
    """
    محرك تحليل الشبكات والعلاقات (Social & Entity Network Analysis)
    يبني مصفوفة الروابط بين الكيانات (أشخاص، منظمات، سفن، أحداث)،
    ويحسب المركزية (Centrality) ويصدر ملفات GEXF لبرنامج Gephi ومخططات تفاعلية.
    """
    def __init__(self):
        self.nodes = {} # id -> metadata
        self.edges = [] # list of (source, target, weight, relation_type)

    def add_entity_node(self, node_id: str, label: str, node_type: str):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "degree": 0
            }

    def add_relationship(self, source: str, target: str, relation_type: str = "مرتبط", weight: float = 1.0):
        self.edges.append({
            "source": source,
            "target": target,
            "relation": relation_type,
            "weight": weight
        })
        if source in self.nodes:
            self.nodes[source]["degree"] += 1
        if target in self.nodes:
            self.nodes[target]["degree"] += 1

    def build_from_events(self, events: List[Dict[str, Any]]):
        """بناء الشبكة تلقائياً من قائمة الأحداث والكيانات المشتركة"""
        for ev in events:
            ev_id = f"EV_{ev.get('id', 'temp')}"
            self.add_entity_node(ev_id, ev.get("title", "")[:30], "EVENT")

            loc = ev.get("location_name")
            if loc:
                loc_id = f"LOC_{loc}"
                self.add_entity_node(loc_id, loc, "LOCATION")
                self.add_relationship(ev_id, loc_id, "وقع في", 1.5)

            cat = ev.get("event_category")
            if cat:
                cat_id = f"CAT_{cat}"
                self.add_entity_node(cat_id, cat, "CATEGORY")
                self.add_relationship(ev_id, cat_id, "يصنف كـ", 1.0)

    def get_top_central_nodes(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """استخراج أكثر الكيانات مركزية وتأثيراً في الشبكة"""
        sorted_nodes = sorted(self.nodes.values(), key=lambda x: x["degree"], reverse=True)
        return sorted_nodes[:top_n]

    def export_gexf(self) -> str:
        """تصدير الشبكة بصيغة GEXF المعيارية لبرنامج Gephi"""
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
        xml.append('  <graph defaultedgetype="undirected">')
        xml.append('    <nodes>')
        for n in self.nodes.values():
            xml.append(f'      <node id="{n["id"]}" label="{n["label"]}" />')
        xml.append('    </nodes>')
        xml.append('    <edges>')
        for idx, e in enumerate(self.edges):
            xml.append(f'      <edge id="{idx}" source="{e["source"]}" target="{e["target"]}" weight="{e["weight"]}" />')
        xml.append('    </edges>')
        xml.append('  </graph>')
        xml.append('</gexf>')
        return "\n".join(xml)

if __name__ == "__main__":
    net = EntityNetworkGraph()
    sample_events = [
        {"id": 1, "title": "تحركات في باب المندب", "location_name": "باب المندب", "event_category": "بحري"},
        {"id": 2, "title": "تفريغ سفينة في الحديدة", "location_name": "الحديدة", "event_category": "تجاري"},
        {"id": 3, "title": "عبور ناقلة نفط عبر باب المندب", "location_name": "باب المندب", "event_category": "بحري"}
    ]
    net.build_from_events(sample_events)
    top = net.get_top_central_nodes()
    print(f"[*] العقد المركزية الأكثر تأثيراً: {top}")
