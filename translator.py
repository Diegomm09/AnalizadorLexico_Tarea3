from ast_nodes import JSONNode, JSONObject, JSONArray, JSONPrimitive
from logger import get_logger

logger = get_logger()

class XMLTranslator:
    def __init__(self, had_errors: bool = False):
        self.had_errors = had_errors

    def translate(self, root_node: JSONNode) -> str:
        """Traduce el AST de JSON a un string con formato XML."""
        logger.info("Iniciando traduccion a XML...")
        
        xml_lines = []
        
        # Advertencia estandar si el origen esta corrupto
        if self.had_errors:
            xml_lines.append("<!-- ADVERTENCIA: EL JSON ORIGEN ESTA CORRUPTO. ESTA ES UNA TRADUCCION PARCIAL -->")
            logger.warning("Generando XML con advertencia de archivo corrupto.")

        # Envoltorio raíz genérico (solución para raíces múltiples en XML)
        xml_lines.append("<root>")
        
        if root_node is not None:
            # Empezamos con nivel de indentación 1 dentro del root
            inner_xml = self._translate_node(root_node, indent_level=1)
            # Como inner_xml ya viene con saltos de línea y tabulaciones, lo agregamos
            if inner_xml.strip():
                xml_lines.append(inner_xml)
        
        xml_lines.append("</root>")
        logger.info("Traduccion a XML finalizada.")
        
        return "\n".join(xml_lines)

    def _translate_node(self, node: JSONNode, indent_level: int) -> str:
        tabs = "\t" * indent_level
        
        if isinstance(node, JSONPrimitive):
            return node.value

        elif isinstance(node, JSONArray):
            if not node.elements:
                return "" # Array vacío
            
            lines = []
            for elem in node.elements:
                elem_xml = self._translate_node(elem, indent_level + 1)
                
                # Si el elemento interior es complejo (objeto/array), formatea en varias líneas
                if isinstance(elem, (JSONObject, JSONArray)) and elem_xml.strip():
                    lines.append(f"{tabs}<item>\n{elem_xml}\n{tabs}</item>")
                else:
                    # Si es primitivo, en una sola línea
                    lines.append(f"{tabs}<item>{elem_xml}</item>")
                    
            return "\n".join(lines)

        elif isinstance(node, JSONObject):
            if not node.attributes:
                return "" # Objeto vacío
            
            lines = []
            for key, val in node.attributes.items():
                # En JSON las claves vienen con comillas (ej. "nombre"), las quitamos para el tag XML
                clean_key = key.strip('"\'')
                # Por si la clave tiene espacios u caracteres no válidos en XML, los reemplazamos
                clean_key = clean_key.replace(" ", "_")
                
                val_xml = self._translate_node(val, indent_level + 1)
                
                if isinstance(val, (JSONObject, JSONArray)) and val_xml.strip():
                    lines.append(f"{tabs}<{clean_key}>\n{val_xml}\n{tabs}</{clean_key}>")
                else:
                    lines.append(f"{tabs}<{clean_key}>{val_xml}</{clean_key}>")
                    
            return "\n".join(lines)

        return ""
