---
name: video-prompt
description: Normativa del prompt de vídeo — genera a partir del contenido de un segmento del storyboard un prompt de generación de vídeo dividido por franjas temporales, con cortes permitidos dentro del segmento
---

# Prompt de vídeo (segmento del storyboard → video_prompt)

A partir de la description de un segmento del storyboard (con su estructura de sub-planos 【镜头N】 y sus diálogos/narración) / atmosphere / duration, genera el `video_prompt` que dirige la generación de vídeo por IA. **Un segmento del storyboard = un vídeo de 8-15 segundos, con cortes permitidos en su interior**: entre segmentos puede haber planos distintos (cambio de tamaño de plano/ángulo/sujeto), enlazados con corte en seco; pero **en ningún momento se cruza de escena** ni hay flashbacks.

## Formato

La **primera línea del `video_prompt` es la cabecera de información**: primero presenta qué personajes y qué escena aparecen en este vídeo y después vienen las franjas temporales. Personajes y escenas se citan siempre con @ (durante la generación se sustituyen por los marcadores de imagen de referencia correspondientes, para que el modelo de vídeo empareje primero «quién» y «dónde»).

```
Personajes en escena: @Javier, @Lucía; Escena: @Cafetería.
0-3 s: @Cafetería, plano corto, la cámara se mece con un leve vaivén de respiración y se acerca lentamente hacia @Javier; él mira el teléfono con la cabeza gacha, los dedos golpean una y otra vez la mesa, expresión ansiosa.
3-6 s: Corte a un plano general de la puerta; suena el timbre, @Lucía empuja la puerta y entra, trayendo consigo una ráfaga de aire frío.
6-9 s: Vuelta al plano medio; @Lucía se acerca sonriendo y se sienta; Javier dice: "Al fin llegas."
```

Reglas de la cabecera:
- Lista solo los personajes que realmente salen en este segmento del storyboard y la escena vinculada; no listes a los que no salen
- Si un atrezzo tiene una aparición notable, puede añadirse a la cabecera (p. ej. `; Atrezzo: @Carta`)
- La cabecera va en línea propia y termina en punto; después vienen las franjas temporales

Divide en segmentos de 3 segundos, cada segmento en su propia línea separado por saltos de línea, con rangos temporales contiguos (sin solapes ni huecos).

## Correspondencia con la descripción del storyboard

`description` es la única fuente de contenido del video_prompt (imágenes, acciones, diálogos y narración están todos en ella); reglas de conversión:

- Cada `【镜头N】` de la `description` se corresponde con **1-2 segmentos contiguos de 3 segundos**, en el mismo orden, sin omisiones, sin fusiones y sin sub-planos nuevos
- Los diálogos/narración se extraen del «NombreDelPersonaje dice: "…"» / «Narración: …» dentro del `【镜头N】` correspondiente y se asignan a los segmentos mapeados de ese sub-plano; **no inventes diálogos nuevos fuera de la description**
- Las acciones visuales se rigen por la `description`; `atmosphere` solo se usa para completar la luz, la tonalidad y la atmósfera de cada segmento

## Estructura interna del segmento

Organiza el contenido de cada segmento en este orden (los puntos sin contenido pueden omitirse, pero la acción/la imagen son obligatorios):

**Rango temporal + @referencia de escena + tamaño de plano/movimiento de cámara + @referencia de personaje + acción principal·expresión + diálogo/narración + atmósfera e iluminación**

- **El primer segmento debe establecer el espacio**: escena + posición de cámara + posición y estado de los personajes, para que el público sepa de un vistazo dónde está y a quién mira
- **Cortes**: el segmento posterior a un corte empieza con un conector tipo «corte a/vuelta a» y vuelve a indicar tamaño de plano y sujeto; los puntos de corte deben alinearse con la estructura de `【镜头N】` de la `description` del storyboard
- **Tamaño de plano/movimiento de cámara (regla dura)**: cada segmento debe indicar a la vez el **tamaño de plano** (plano corto/plano medio/plano general/primerísimo primer plano) y una **instrucción de movimiento de cámara**; el movimiento es continuo dentro de un mismo sub-plano y puede cambiar tras un corte. Se escribe como «tamaño inicial + tipo de movimiento + velocidad/ritmo», p. ej. "plano medio con acercamiento uniforme y lento hasta un primerísimo primer plano del rostro", "travelling lateral sincronizado con el personaje, con parallax en el fondo". Prohibido dejar todo el segmento en un simple "cámara fija" sin información de movimiento — la cámara debe "moverse" (traslación, zoom, seguimiento, vaivén de respiración, todo vale) para evitar cuadros estáticos estilo PPT. El vocabulario de movimientos está en «Normativa de movimiento de cámara», más abajo
- **Acción**: una acción principal por segmento, con verbos concretos y visibles (andar, girarse, alzar la vista, apretar, detenerse)
- **Toda la emoción se convierte en descripción visible**: nada de palabras abstractas tipo "está muy triste/el ambiente está tenso"; escríbelo como "baja la cabeza, los dedos aprietan el borde de la taza, la respiración se hace más pesada"
- **Diálogo/narración**: escribe «NombreDelPersonaje dice: "réplica"», y la narración «Narración: contenido»; una réplica larga que no quepa en 3 segundos se reparte en varios segmentos; un segmento sin diálogo puede anotar sonido ambiental/sonido de acción (p. ej. "las máquinas no dejan de rugir")

## Reglas de referencias

- `@NombreDeEscena` — referencia de escena; el nombre debe coincidir exactamente con el lugar de la lista de escenas
- `@NombreDePersonaje` — referencia de personaje; el nombre debe coincidir exactamente con el nombre de la lista de personajes
- `@NombreDeAtrezzo` — referencia de atrezzo; el nombre debe coincidir exactamente con el nombre de la lista de atrezzo; cita el atrezzo cuando se vea claramente en el cuadro, se use o salga en primerísimo primer plano
- Durante la generación, cada `@nombre` se sustituye automáticamente por el marcador de imagen de referencia correspondiente (p. ej. `@Javier` → `@Imagen1Javier`), así que los nombres deben coincidir con precisión, sin abreviar ni añadir símbolos extra
- **Cada segmento necesita al menos una @ referencia que ancle la imagen**; los segmentos en los que aparece un personaje deben hacer @ a ese personaje; cita solo escenas/personajes/atrezzo ya vinculados a este segmento del storyboard

## Reglas de la línea de tiempo

- Número de segmentos = duración del segmento del storyboard ÷ 3 segundos (redondeo hacia arriba); la suma de los rangos temporales debe ser exactamente igual a la duración total del segmento
- Ritmo del contenido: el primer segmento establece → los intermedios hacen avanzar la acción/el conflicto → el último aterriza en el resultado o en el punto emocional

## Normativa de movimiento de cámara

Cada franja temporal lleva movimiento de cámara, elegido del vocabulario siguiente y coherente con la intención de cámara de los campos `description`/`movement` del storyboard (lo que la description indique de cámara, eso se despliega en el video_prompt; si no indica nada, elige lo que mejor encaje con la imagen):

- **Narración básica**: acercamiento lento (de plano medio a primerísimo primer plano, velocidad uniforme, fondo desenfocándose poco a poco), alejamiento revelador (de primerísimo primer plano a plano general, rápido al principio y lento al final), travelling lateral de seguimiento (moviéndose junto a la persona, parallax en el fondo), grúa ascendente/descendente (subida/bajada vertical que revela el espacio), órbita en arco (90-180 grados alrededor del personaje), caminar en primera persona (a la altura de la mirada, leve vaivén como de respiración)
- **Emoción y atmósfera**: cámara en mano jadeante (leve temblor que se acentúa tras el movimiento), ángulo de mirón furtivo (obstrucción en primer término por la rendija de una puerta/ventana), pulso cardíaco (acercamiento/alejamiento sincronizados con el ritmo emocional), sincronía con la respiración (micro acercamiento al inhalar, alejamiento lento al exhalar)
- **Detalle psicológico**: enfoque de mirada (acercamiento paulatino hacia el objeto mirado, transferencia de foco), temblor de miedo (vibración fina e irregular), órbita tierna (órbita lenta en ángulo pequeño con el foco clavado en el rostro), persecución a toda velocidad (seguimiento pegado al objetivo en movimiento, desenfoque de movimiento), zigzag de pelea (conmutación rápida entre los dos combatientes), picado en vuelo (descenso desde las alturas con micro sacudida al aterrizar)
- **Peleas a alta velocidad**: solo cuando la `description` del storyboard indique explícitamente cámara de pelea se despliega tal cual figure en la description (ninguna posición, velocidad o cifra se puede perder): acercamiento rapidísimo desde plano bajo, seguimiento rozando el suelo, barrido ascendente vertiginoso, seguimiento a distancia mínima, alejamiento inverso con cambio de foco, alejamiento vertiginoso con estela, difuminado de alta velocidad de 0.15 segundos en el instante del impacto, shake de choque de 0.3 segundos
- **Ángulos especiales**: contrapicado extremo, ángulo holandés, plano sobre el hombro, punto de vista subjetivo
- **Transiciones de ritmo**: látigo rápido de cámara (la dirección del látigo coincide con la dirección del movimiento del segmento siguiente), transición por oclusión (un objeto del primer término barre la pantalla y corta en ese instante), parada súbita a cuadro congelado (frenado hasta la quietud fija, solo para segmentos del punto de explosión)

Requisitos de redacción:
- La instrucción de cámara aparece ligada al tamaño de plano y a la velocidad: "acercamiento lento desde plano general hasta plano medio", no solo "acercamiento"
- Adverbios de velocidad concretos: velocidad uniforme/lento/rapidísimo/rápido al principio y lento al final/de lento a rápido
- Un movimiento de cámara por segmento; continuo dentro del segmento, solo cambia en los puntos de corte
- Bullet time/primerísimo primer plano a cámara lenta/ojo de pez/diorama son trucos de realce: se usan solo cuando la `description` del storyboard los indica explícitamente, como máximo 1-2 veces por episodio
- El vaivén en mano y el vaivén de respiración cuentan como «micro-movimiento»: sirven en los segmentos que en principio escribirías como cámara fija, en sustitución de la quietud total

## Prohibiciones

- Cambios de escena, flashbacks (un segmento ocurre dentro de una única escena)
- Referenciar escenas/personajes fuera de las listas
- Descripción psicológica abstracta, metáforas literarias (el modelo solo entiende imágenes visibles)
- Sobreactuación: nada de gritos, berros, alborotos ni llantos desconsolados; el susto se escribe como microrreacción (quedarse paralizado, las pupilas se encogen, aspirar bruscamente, medio paso atrás); el diálogo en tono y volumen cotidianos (si la trama extrema exige de verdad una explosión, cúbrela escribiendo explícitamente «explosión emocional» en ese segmento)
- Cámara lenta y quietud que estiran el tiempo: por defecto nada de cámara lenta ni largas miradas inmóviles; excepción: los sub-planos de punto de explosión en los que la `description` del storyboard indique explícitamente bullet time/primerísimo primer plano a cámara lenta/parada a cuadro congelado pueden usarse conforme a la description. Cada segmento sigue necesitando un movimiento de cámara visible o un avance de la acción; no se admite el «plano puramente estático»
- Un idioma que no coincida con la directiva de idioma de la sesión

## Guardado

Llama a `update_storyboard` para actualizar únicamente el campo `video_prompt` de ese segmento del storyboard; no modifiques ningún otro campo ni vuelvas a desglosar todo el episodio. La plataforma añadirá automáticamente guardas de interpretación y de ritmo en la petición real de generación; no hace falta repetir estos requisitos dentro del prompt.
