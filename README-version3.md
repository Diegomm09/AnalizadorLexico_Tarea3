# Analizador y Traductor JSON a XML (Compiladores)

## Descripcion General
Este proyecto es una herramienta de software capaz de leer un archivo escrito en un lenguaje similar a JSON (JSON simplificado), analizar su estructura para comprobar que este correctamente escrito, y finalmente traducirlo de manera automatica a formato XML. 

## Objetivo del Proyecto
El objetivo principal es demostrar en la practica los conceptos teoricos de la materia Compiladores y Lenguajes de Bajo Nivel. El proyecto transforma texto plano (JSON) en otra estructura de datos distinta (XML) simulando el proceso interno que realiza un compilador o un transpilador real al interpretar codigo de programacion. Todo el proceso es auditable mediante un archivo global de logs.

---

## Explicacion Simple de las Tres Fases

El programa divide su trabajo en tres grandes etapas secuenciales:

* **Fase 1: Analisis lexico**
  Lee el texto crudo caracter por caracter e identifica palabras, simbolos y numeros validos (llamados "tokens"). Por ejemplo, detecta que `"nombre"` es un literal de cadena y que `:` es el simbolo de dos puntos.
  
* **Fase 2: Analisis sintactico descendente**
  Recibe la lista de tokens de la Fase 1 y revisa que esten en el orden correcto segun las reglas gramaticales del JSON. Si detecta un error de sintaxis (por ejemplo, una coma sobrante), usa un mecanismo llamado "Panic Mode" para intentar recuperarse y seguir revisando el resto del archivo sin detenerse por completo.

* **Fase 3: Traduccion dirigida por sintaxis a XML**
  Una vez que la estructura es validada, el traductor recorre la informacion recopilada y escribe su equivalente en lenguaje XML. Si hubieron errores en la Fase 2, esta fase produce un XML parcial para salvar la mayor cantidad de datos posible.

---

## Explicacion Tecnica de la Arquitectura

1. **Flujo de Ejecucion:** El archivo `programa.py` actua como orquestador. Toma la entrada, invoca al Lexer, recoge los tokens y los pasa al Parser. El Parser construye un **Arbol de Sintaxis Abstracta (AST)** en memoria utilizando nodos (clases) definidos en `ast_nodes.py`. Finalmente, se le pasa el nodo raiz al `XMLTranslator`.
2. **Lexer:** Creado desde cero, itera sobre el `InputStream`. Reconoce tokens mediante expresiones regulares sencillas y bifurcaciones condicionales. Reporta fallos en `ErrorReporter`.
3. **Parser LL(1) / Descenso Recursivo:** Se definio una gramatica con factorizacion por la izquierda. El parser verifica el token actual (`lookahead`) y consume tokens mientras desciende por las funciones de produccion (`element()`, `object()`, `attributes_list()`). Implementa sincronizacion usando conjuntos FIRST y FOLLOW para el *Panic Mode*.
4. **Traductor (AST a XML):** La traduccion se independizo de la lectura ("spaghetti code") introduciendo un AST. `translator.py` posee un metodo `translate(node)` que viaja recursivamente por los objetos y arreglos del arbol emitiendo nodos XML tabulados.
5. **Logger de Doble Via:** La auditoria y el control de errores se maneja con la libreria nativa `logging`. Posee un `StreamHandler` en consola con colores ANSI y un `FileHandler` en el archivo plano `server.log` con codificacion utf-8-sig para evadir problemas en editores de texto tradicionales de Windows.

## Estructura de Carpetas

```text
/
├── lexer/                      # Modulo del analizador lexico
│   ├── lexer.py                # Analizador lexico principal
│   ├── token.py                # Definicion de Tokens
│   └── input_stream.py         # Lector de caracteres
├── ast_nodes.py                # Definicion de Nodos del Arbol AST
├── parser.py                   # Analizador sintactico
├── translator.py               # Traductor XML a partir del AST
├── programa.py                 # Orquestador del programa
├── logger.py                   # Configurador del sistema de trazas
├── server.log                  # Archivo de auditoria general (Global Log)
├── ejemplo/                    # Archivos de prueba (fuente.txt, entrada.txt)
└── salidas_ejecucion/          # Carpetas autogeneradas con las salidas de las 3 fases
```

---

## Requisitos para Ejecutar

* Python 3.8 o superior instalado en el equipo.
* Una terminal (Se recomienda encarecidamente **PowerShell** en Windows).

---

## Formas de Ejecucion

### Ejecucion con archivo de entrada

Si deseas analizar un JSON especifico, ejecuta el programa pasandole la ruta del archivo:

```powershell
python programa.py ruta/al/archivo.json
```

### Ejecucion sin archivo de entrada

Puedes ejecutar el programa directamente sin proporcionarle ninguna ruta. Si haces esto, el programa utilizara por defecto el archivo `ejemplo/entrada.txt` incluido en este repositorio:

```powershell
python programa.py
```

---

## Salidas Generadas

Por cada ejecucion, el programa crea automaticamente una nueva carpeta en el directorio `salidas_ejecucion/`. El nombre de la carpeta estara marcado por la fecha y hora exacta, por ejemplo: `salidas_ejecucion/ejecucion_20260528_192300/`.

Dentro de esta carpeta se guardaran tres archivos separados, correspondientes a la salida oficial de cada fase de la tarea:

* **`salida_fase_1_lexico.txt`**: Volcado de la lista completa de componentes lexicos generados linea por linea.
* **`salida_fase_2_sintactico.txt`**: Confirmacion de analisis exitoso o listado completo de los errores sintacticos recuperados mediante el Panic Mode.
* **`salida_fase_3_traduccion.xml`**: El documento final con el formato traducido a XML.

*Si una carpeta con la misma fecha ya existe (ejecuciones concurrentes en el mismo segundo), los archivos internos seran sobrescritos.*

---

## Logs

Para mantener una auditoria total de la aplicacion (incluso si no tienes a la mano los archivos de salida mencionados arriba), el sistema guarda absolutamente todo el comportamiento de la ejecucion en un archivo unico global llamado `server.log`.

Este archivo log garantiza:
* El JSON de entrada original ingresado por el usuario.
* El inicio, el fin y la traza detallada de las 3 fases.
* Los errores interceptados por los analizadores.
* Las rutas en disco en donde se alojaron los archivos resultantes de cada fase.

### Como ver logs en vivo (PowerShell)

Para auditar el programa como un profesional, se sugiere abrir **dos terminales de PowerShell** (o dividir la pantalla en VS Code):

1. **Terminal 1**: Utilizala exclusivamente para vigilar el archivo de log en tiempo real ejecutando este comando:
   ```powershell
   Get-Content .\server.log -Wait -Tail 50
   ```
2. **Terminal 2**: Utilizala para ejecutar el script de python (`python programa.py`). Veras como en la primera terminal los logs empiezan a imprimirse en tiempo real.

---

## Ejemplo de flujo completo

1. Abres la consola y escribes `python programa.py ejemplo/entrada.txt`.
2. La consola imprime con **colores** los titulos en azul, advertencias en amarillo y progreso en verde.
3. El programa detecta que estas usando "entrada.txt". 
4. Imprime el contenido completo, verifica los tokens e informa que la fase 1 culmino.
5. Pasa el analizador sintactico. Supongamos que olvidaste una llave `}`; el log imprimira un `WARNING` en color amarillo alertando la posicion del error, pero informara que continuo creando el arbol por el Panic Mode.
6. Se genera el XML y se imprime en pantalla.
7. Se listan las rutas de los tres archivos de salidas donde quedo todo registrado, ejemplo `salidas_ejecucion/ejecucion_20260528_192533/...`.

---

## Problemas comunes y soluciones

### Notas sobre encoding y PowerShell

En versiones clasicas de Windows, herramientas como `cmd.exe` o `PowerShell` intentan leer los textos usando formatos heredados como Windows-1252. Dado que el software tradicional a menudo inyecta codigo ANSI (para pintar colores) o acentos, el texto puede terminar viendose deforme con caracteres extranos (como `TraducciÃ³n` o `Ãrbol`).

**Decisiones de arquitectura aplicadas para evadir esto:**
1. **Logs Separados:** La consola tiene colores para mejor legibilidad, pero el archivo plano (`server.log`) omite todo tipo de codificacion de color para que jamas veas codigos como `\033[36m` en tu bloc de notas.
2. **Ausencia de Acentos:** Para asegurar una ejecucion y visualizacion inmaculada en cualquier version del sistema operativo global (incluidos sistemas sin espanol nativo configurado), los mensajes, los titulos, los prints e incluso este propio README han sido desprovistos de tildes o caracteres especiales del idioma, favoreciendo tecnicismos ascriptivos (`Analisis`, `Sintactico`, `Traduccion`, `Arbol`).
3. **BOM Evadido:** El programa elimina proactivamente el Byte Order Mark (`\ufeff`) durante la lectura de archivos de texto que pudieron ser generados por editores desfasados de Windows, impidiendo bloqueos lexicos o fallos de crasheo Unicode en consola.
