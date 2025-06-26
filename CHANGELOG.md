# 📝 CHANGELOG - Video to Article (SMN)

Historial de cambios y mejoras de la herramienta "Video > Text AI Converter for SMN".

---

## Versión actual (06/2025)

- Conversión de vídeo a transcripción con Whisper API.
- Generación de artículo con ChatGPT (GPT-4) a partir de la transcripción.
- Prompts personalizados por **site**.
- Prompts personalizados por **editor**.
- Prompts personalizados por **categoría del artículo**.
- Posibilidad de añadir instrucciones adicionales al prompt.
- Copia del artículo en Markdown + descarga en HTML.

---

## Mejoras implementadas

### ✅ Manejo de errores mejorado

- Distinción entre errores de OpenAI API, errores de FileNotFound, y errores generales.
- Visualización de los errores en la interfaz de usuario.

### ✅ Word count (número de palabras)

- Después de generar el artículo, se calcula el número de palabras y se muestra al editor.

### ✅ Detección automática del idioma de la transcripción

- Al usar `response_format="verbose_json"`, se muestra en la app el idioma detectado por Whisper.
- Muy útil para saber si se debe ajustar el prompt de generación del artículo.

### ✅ Selector de categoría

- Añadido selector **"Select the type of content"** con la opción inicial:
  - Gastronomía (restaurants, bars, street food)
- Se carga el prompt de la categoría desde `/prompts/category/food.txt` si se selecciona.

### ✅ Selector de idioma de output del artículo

- Añadido selector **"Select language for article output"**.
- Se cargan dinámicamente los prompts desde `/prompts/languages/*.txt`.
- Si se selecciona un idioma, se añade su prompt al `full_prompt` final.

### ✅ Control de tamaño de archivo máximo

- Se añade validación: vídeos > 25 MB no se envían a Whisper API.
- Si el archivo supera 25 MB, se muestra mensaje de error claro y se detiene el proceso.

---

## Cambios de UX / visuales

- Mensajes y etiquetas de los selectores en inglés.
- Cambiada la etiqueta del botón "Generar artículo" a "✍️ Create article".
- Orden coherente de los selectores (site → editor → category → language → extra prompt).

---

## Ideas en backlog (pendientes / propuestas)

- Añadir editor de texto enriquecido (menú visual con negritas, cursivas, listas, etc).
- Posibilidad de dividir vídeos largos en fragmentos de audio para transcribir partes (procesar vídeos > 25 MB).
- Guardar automáticamente los artículos generados en carpetas locales (`articulos_guardados/`).
- Re-generación de titulares Discover sin repetir toda la generación del artículo.
- Mejor integración con el flujo de trabajo del editor en WordPress.

---

Fin del changelog.