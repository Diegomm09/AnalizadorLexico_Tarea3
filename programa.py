"""
programa.py – Orquestador del analizador lexico, sintactico y traductor a XML
para el lenguaje JSON simplificado.

Uso desde consola (Powershell):
    python programa.py
    o
    python programa.py ruta/al/archivo.json
"""

import argparse
import os
import sys
import traceback
from datetime import datetime

from lexer.input_stream import InputStream
from lexer.lexer import Lexer
from lexer.error_reporter import ErrorReporter
from parser import Parser
from translator import XMLTranslator
from logger import get_logger

logger = get_logger()

def generar_salida_lexico(tokens_list):
    """Agrupa tokens por linea para cumplir con la Tarea 1"""
    if not tokens_list:
        return "No se encontraron tokens."
        
    lineas = {}
    for t in tokens_list:
        if t.line not in lineas:
            lineas[t.line] = []
        lineas[t.line].append(t.type.name)
        
    resultado = []
    for num_linea in sorted(lineas.keys()):
        resultado.append(f"Linea {num_linea}: " + " ".join(lineas[num_linea]))
    return "\n".join(resultado)

def main():
    logger.info("==================================================")
    logger.info("Iniciando ejecucion de programa.py (Orquestador Principal)")
    
    arg_parser = argparse.ArgumentParser(
        description="Analizador y Traductor de JSON simplificado a XML."
    )

    arg_parser.add_argument(
        "infile",
        nargs="?",
        default="ejemplo/entrada.txt",
        help="Ruta del archivo fuente de entrada (JSON simplificado). Si no se provee, usa ejemplo/entrada.txt",
    )
    arg_parser.add_argument(
        "--ansi-errors",
        dest="ansi_errors",
        action="store_true",
        help="Muestra errores lexicos en consola con colores ANSI.",
    )

    args = arg_parser.parse_args()

    in_path = args.infile
    ansi_errors = args.ansi_errors

    logger.info(f"Fecha y hora de ejecucion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not os.path.isfile(in_path):
        logger.error(f"El archivo de entrada no existe: {in_path}")
        logger.error("Ejecucion abortada.")
        sys.exit(1)

    # Crear la carpeta de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("salidas_ejecucion", f"ejecucion_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    out_lexico = os.path.join(output_dir, "salida_fase_1_lexico.txt")
    out_sintactico = os.path.join(output_dir, "salida_fase_2_sintactico.txt")
    out_xml = os.path.join(output_dir, "salida_fase_3_traduccion.xml")

    # Envuelto en un bloque TRY para capturar caidas del codigo en los logs
    try:
        with open(in_path, "r", encoding="utf-8") as f:
            text = f.read().lstrip("\ufeff")

        logger.info(f"Ruta del archivo de entrada: {in_path}")

        # ==========================================
        # 1. FASE 1: Analisis Lexico
        # ==========================================
        logger.info("\n=== FASE 1: ANALISIS LEXICO ===")
        logger.info(f"[ENTRADA FASE 1] Contenido completo del JSON de entrada:\n{text}\n-------------------")
        
        stream = InputStream(text)
        reporter = ErrorReporter(ansi=ansi_errors)
        lexer = Lexer(stream, reporter)
        
        # Consumimos todos los tokens y errores
        tokens_list = []
        for kind, obj in lexer.tokenize():
            if kind == "TOKEN":
                tokens_list.append(obj)
            elif kind == "ERROR":
                reporter.add(obj)
        
        if reporter.has_errors():
            logger.warning(f"Se encontraron {len(reporter._errors)} errores lexicos durante la tokenizacion.")
            errores_str = ""
            for e in reporter._errors:
                errores_str += f"Error en linea {e.line}, col {e.col}: {e.hint}\n"
            logger.warning(f"Errores lexicos:\n{errores_str}")

        # Guardar archivo de salida Fase 1
        contenido_lexico = generar_salida_lexico(tokens_list)
        with open(out_lexico, "w", encoding="utf-8") as f:
            f.write(contenido_lexico)
            
        logger.info(f"[SALIDA FASE 1] Salida completa generada por la Fase 1 guardada en: {out_lexico}")
        logger.info(f"Vista previa de tokens (Fase 1):\n{contenido_lexico[:500]} ...\n-------------------")

        # ==========================================
        # 2. FASE 2: Analisis Sintactico
        # ==========================================
        logger.info("\n=== FASE 2: ANALISIS SINTACTICO ===")
        logger.info(f"[ENTRADA FASE 2] Recibiendo la Secuencia de {len(tokens_list)} Tokens de la Fase 1.")
        
        syntax_parser = Parser(tokens_list)
        ast_root = syntax_parser.parse()

        contenido_sintactico = ""
        if syntax_parser.had_errors:
            logger.warning("[SALIDA FASE 2] Analisis Sintactico finalizado CON ERRORES (Se aplico Panic Mode). Arbol AST parcial generado.")
            contenido_sintactico = "ESTADO: Completado con errores (Panic Mode aplicado).\nERRORES ENCONTRADOS:\n"
            for err in syntax_parser.syntax_errors:
                msg = f"Linea {err.line}, Col {err.col}: {err.message} (Token: {err.token.type.name})"
                contenido_sintactico += msg + "\n"
                logger.warning(f"Error Sintactico: {msg}")
        else:
            logger.info("[SALIDA FASE 2] Analisis Sintactico finalizado EXITOSAMENTE. Arbol AST generado en memoria sin errores.")
            contenido_sintactico = "ESTADO: Completado con exito. JSON lexica y sintacticamente correcto.\nARBOL AST GENERADO EN MEMORIA."

        with open(out_sintactico, "w", encoding="utf-8") as f:
            f.write(contenido_sintactico)
            
        logger.info(f"Salida de la Fase 2 guardada en: {out_sintactico}\n-------------------")

        # ==========================================
        # 3. FASE 3: Traduccion a XML
        # ==========================================
        logger.info("\n=== FASE 3: TRADUCCION A XML ===")
        logger.info("[ENTRADA FASE 3] Recibiendo el Arbol AST de la Fase 2.")
        
        translator = XMLTranslator(had_errors=syntax_parser.had_errors)
        xml_output = translator.translate(ast_root)
        
        logger.info(f"[SALIDA FASE 3] XML generado completo:\n\n{xml_output}\n-------------------")

        # Guardar archivo de salida Fase 3
        with open(out_xml, "w", encoding="utf-8") as f:
            f.write(xml_output)
        
        logger.info(f"Ruta donde se guardo el XML (Fase 3): {out_xml}")

        # Resultado final
        logger.info("\n=== RESULTADO FINAL DE LA EJECUCION ===")
        logger.info(f"Directorio de salidas: {output_dir}")
        logger.info(f"1. Lexico:     {out_lexico}")
        logger.info(f"2. Sintactico: {out_sintactico}")
        logger.info(f"3. Traduccion: {out_xml}")
        
        if reporter.has_errors() or syntax_parser.had_errors:
            logger.warning("El proceso finalizo pero se detectaron errores lexicos o sintacticos (verificados en logs).")
        else:
            logger.info("El proceso finalizo con exito total. Ningun error encontrado.")
            
        logger.info("================ FIN DE LA EJECUCION ================\n")

    except Exception as e:
        logger.error("\nERROR GRAVE: El programa ha fallado inesperadamente debido a un problema en el codigo.")
        logger.error(f"Traza del error (Stacktrace):\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
