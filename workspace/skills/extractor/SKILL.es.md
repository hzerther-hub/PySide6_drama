---
name: extractor
description: Normativa y métodos para la extracción de personajes, escenas y atrezzo
---

# Guía de extracción de personajes, escenas y atrezzo

## Normativa de extracción de personajes

Campos del personaje extraído (correspondencia uno a uno con los parámetros de la herramienta `save_dedup_characters`):
- **name** (obligatorio): nombre completo del personaje
- **role**: posicionamiento del personaje — protagonista / secundario / extra
- **appearance**: descripción física (300-500 caracteres) — sexo, edad aparente, rasgos faciales, complexión, presencia. **No emitas los rasgos de personalidad por separado; conviértelos en presencia exterior y gesto, integrándolos en la descripción física** (p. ej. «personalidad fría» debe escribirse como «mirada gélida, expresión contenida, casi nunca sonríe»)
- **styling**: caracterización — peinado, vestuario, maquillaje, accesorios, etc.
- **description**: trasfondo y relaciones del personaje (complemento opcional)

## Normativa de extracción de escenas

Campos de la escena extraída (correspondencia uno a uno con los parámetros de la herramienta `save_dedup_scenes`):
- **location** (obligatorio): nombre concreto del lugar
- **time**: franja horaria (p. ej. día/atardecer/altas horas de la noche); el mismo lugar en otra franja horaria cuenta como escena nueva
- **prompt**: descripción de la escena — espacio, ambientación, textura de época, elementos visuales clave (fondo puro, sin personas)
- **lighting**: luz de la escena — fuentes de luz, tonalidad, claroscuro, atmósfera

## Normativa de extracción de atrezzo

**Principio básico: mejor extraer de menos que de más.** El atrezzo es un activo de alto coste que se usa para generar imágenes de producto sobre fondo blanco y que luego citan los planos de detalle del vídeo; solo merece extraerse el atrezzo crítico para la trama. Un episodio suele tener **0-3** piezas clave de atrezzo; si hay más de 3, ordénalas por importancia dramática y conserva solo las 3 primeras.

Deben cumplirse **las dos condiciones siguientes a la vez**; si falta una, no vale:
1. **Impulsa directamente la trama**: la aparición, la entrega, el deterioro o el descubrimiento del objeto desencadena un giro argumental (p. ej. un arma del crimen, una prenda prenda o recuerdo, un documento clave, un regalo de enamorados, una prueba decisiva).
2. **Merece una imagen generada para sí**: los storyboards posteriores le darán planos de detalle o lo harán reaparecer, así que necesita una apariencia fija.

**Tres preguntas de control** (formúlalas y respóndetelas por cada pieza candidata; si alguna respuesta es «no», descártala):
- (1) ¿La trama sigue en pie si lo eliminas? → Si sigue en pie, **no lo extraigas** (es solo un fondo decorativo)
- (2) ¿Es simplemente un objeto cotidiano que el personaje usa al pasar (móvil, palillos, vaso, cigarrillos, paraguas)? → Si lo es, **no lo extraigas**
- (3) ¿Forma parte de la ambientación de la escena (mesas y sillas, lámparas, puertas y ventanas, cuadros colgados, vajilla)? → Si lo es, **no lo extraigas** (eso pertenece a la descripción de la escena)

**Casos típicos que no son atrezzo**: objetos corrientes que se usan al pasar sin afectar al rumbo de la trama; la ambientación y el mobiliario de la escena; objetos mencionados una sola vez y sin continuidad; la indumentaria habitual del personaje (se integra en su caracterización).

Si no hay ninguna pieza que cumpla las condiciones, **no fuerces la extracción**: basta con pasar un array vacío al llamar a `save_dedup_props`.

Campos de la pieza de atrezzo extraída (correspondencia uno a uno con los parámetros de la herramienta `save_dedup_props`):
- **name** (obligatorio): nombre del atrezzo
- **type**: tipo — cotidiano/arma/transporte/decoración/documento, etc.
- **description**: apariencia del objeto — describe únicamente el aspecto físico del objeto en sí (material, color, forma, tamaño, grado de antigüedad, señales de desgaste, etc.); no escribas su uso argumental ni relaciones con los personajes u otras entidades

El atrezzo **no necesita prompt de imagen** — el prompt definitivo de cada pieza lo genera de forma específica el Agent de generación de prompts antes de crear la imagen (normativa de producto sobre fondo blanco).

## Pasos de uso

1. Llama a `read_script_for_extraction` para leer el guion del episodio actual
2. Llama a `read_existing_characters` para ver los personajes ya existentes del proyecto y los ya vinculados al episodio actual
3. Llama a `read_existing_scenes` para ver las escenas ya existentes del proyecto y las ya vinculadas al episodio actual
4. Llama a `read_existing_props` para ver el atrezzo ya existente del proyecto y el ya vinculado al episodio actual
5. Extrae únicamente los personajes, escenas y atrezzo que el episodio actual implique realmente
6. Llama a `save_dedup_characters` para guardar los personajes y vincularlos automáticamente al episodio actual
7. Llama a `save_dedup_scenes` para guardar las escenas y vincularlas automáticamente al episodio actual
8. Llama a `save_dedup_props` para guardar el atrezzo y vincularlo automáticamente al episodio actual

## Reglas del episodio actual

- El objetivo es completar los personajes, escenas y atrezzo que necesita el «episodio actual», no reescanear todo el proyecto
- Si un elemento ya existe en el proyecto pero no está vinculado al episodio actual, reutilízalo y vincúlalo igualmente al episodio actual
- Reglas de deduplicación: personajes/atrezzo se emparejan por coincidencia exacta de nombre; las escenas, por coincidencia exacta de [lugar + franja horaria]; si hay coincidencia, prioriza reutilizar, no crees duplicados
- Deduplicación por nombres casi iguales: cuando el nombre incluye un calificador entre paréntesis o un alias, compara por la parte principal anterior al paréntesis (p. ej. «Lucía (protagonista)» y «Lucía» se consideran el mismo personaje/pieza de atrezzo — reutiliza el existente); el normalized_name que devuelven read_existing_characters / read_existing_props es el nombre ya normalizado, y normalized_location funciona igual para las escenas — con eso basta para decidir
