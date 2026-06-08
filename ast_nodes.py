from dataclasses import dataclass, field
from typing import List, Dict, Any, Union

@dataclass
class JSONNode:
    """Clase base para todos los nodos del AST de JSON."""
    pass

@dataclass
class JSONPrimitive(JSONNode):
    """Representa un valor primitivo: string, number, true, false, null."""
    value: str

@dataclass
class JSONArray(JSONNode):
    """Representa un arreglo JSON [ element, ... ]."""
    elements: List[JSONNode] = field(default_factory=list)

@dataclass
class JSONObject(JSONNode):
    """Representa un objeto JSON { key: value, ... }."""
    # Las claves siempre son strings en JSON
    attributes: Dict[str, JSONNode] = field(default_factory=dict)
