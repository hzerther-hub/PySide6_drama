---
name: fight-cinematography
description: Manual de movimiento de cámara para peleas a alta velocidad — fórmulas de posición de cámara, anotaciones de velocidad y redacción de prompts para segmentos de pelea/persecución/punto de explosión
---

# Manual de cámara para peleas a alta velocidad (exclusivo de segmentos de pelea/acción a alta velocidad)

## Cuándo activarlo (decisión automática)

Cuando el segmento o los sub-planos dentro del segmento presenten acciones a alta velocidad como **pelea, carga, persecución, esquiva con contraataque, patada voladora, estallido de golpe pesado, salida despedida por el impacto**, los movimientos de cámara se eligen de las «fórmulas de posición de cámara» y de las «anotaciones de velocidad» de este manual, con prioridad sobre el vocabulario básico de cámara; los segmentos de diálogo, de preparación y de transición no usan este manual.

La lógica de fondo son solo dos cosas: **rapidez** y **anticipación** — fabricar velocidad y amplificarla. El movimiento de cámara sirve a tres propósitos:
1. Que el espectador vea con claridad la trayectoria de la acción
2. Reforzar el impacto de la dirección del ataque
3. Usar la velocidad de la cámara para fabricar sensación de opresión

## Fórmulas de posición de cámara (10)

Cada una = combinación de posición/movimiento + técnicas a las que aplica + redacción del prompt (la redacción puede incrustarse directamente al principio del 【镜头N】 de la `description`):

| # | Fórmula | Técnicas aplicables | Redacción del prompt |
|---|---|---|---|
| 1 | Embestida de partida: posición baja + acercamiento rapidísimo | Puñetazo pesado, embestida, primer enfrentamiento | Posición a 0.5 metros en ángulo bajo, la cámara se acerca rapidísimo de abajo hacia arriba, capturando el polvo que levanta el choque a alta velocidad de ambos y el volumen de la onda de choque; el ángulo LOW refuerza la sensación de opresión |
| 2 | Seguimiento lateral: órbita + cambio de foco | Combos, transiciones ataque-defensa, duelo dinámico | ORBIT rodea en semicírculo desde la espalda del atacante, con el foco clavado en el cabello y el borde de la ropa del golpeado; en el instante del impacto, cambio de foco |
| 3 | Seguimiento a ras de suelo: vista rasante + seguimiento en posición baja | Barrido de pierna, caída y volteo en el suelo, acciones bajas | La cámara, a ras de suelo y en ángulo bajo, sigue barriendo el movimiento de las piernas, con los fragmentos del suelo pasando de frente |
| 4 | Persecución en el aire: contrapicado en posición baja + barrido ascendente rapidísimo | Patada voladora, patada giratoria, combo aéreo de patadas | Contrapicado en posición baja, TILT UP con barrido ascendente vertiginoso siguiendo al personaje en su elevación, acentuando la sensación de suspensión en el aire |
| 5 | Instante del impacto: parada a cuadro + leve vibración | El golpe que conecta, punto de explosión | Primerísimo primer plano del instante del impacto, difuminado de alta velocidad de la imagen durante 0.15 segundos, con estela residual en la parte golpeada y un leve rebote vibratorio de la cámara |
| 6 | Salida despedida: alejamiento rapidísimo + rastreo | Salida volando por un golpe pesado, retroceso empujado | La cámara se aleja rapidísimo y rastrea en la dirección de la estela del personaje despedido, mientras el fondo se desgarra en profundidad |
| 7 | Distancia mínima: plano de seguimiento + avance en DOLLY | Puñetazos encadenados, golpes combinados | DOLLY avanza en horizontal con la cámara a distancia mínima de los dos en plena refriega, para que el espectador sienta la opresión del viento de los puños |
| 8 | Esquiva y contraataque: acercamiento inverso + cambio de foco | Esquiva, defensa y contraataque | La cámara avanza vertiginosamente desde detrás del atacante, PAN la lanza lateralmente hacia la dirección del contraataque, PUSH se acerca rapidísimo a la acción del contraataque, y el foco salta en un instante del atacante al contraatacante |
| 9 | Respuesta en contrapicado: contrapicado + alejamiento rapidísimo | Contraataque desde abajo, golpe aéreo | Arranca en contrapicado de ángulo bajo, se aleja rapidísimo cuando el personaje se eleva, y un primerísimo primer plano en contrapicado se despliega en un instante en panorama aéreo |
| 10 | Cierre a cuadro: acercamiento lento en plano medio-corto + retroceso lento | Recoger la técnica, presentación, cargar el próximo golpe | MCU en plano medio-corto con acercamiento lento que congela la postura del personaje; después PULL retrocede despacio desenfocando el fondo, conservando la tensión del instante previo a la explosión del siguiente golpe |

## Anotaciones de velocidad (4, se superponen a las fórmulas de posición)

| Anotación | Para qué | Efecto | Redacción |
|---|---|---|---|
| Swift seguimiento rápido | Cargas, irrupciones, persecuciones, desplazamientos cuerpo a cuerpo | Tensión, sensación de velocidad, ritmo fuerte | Acercamiento/alejamiento rapidísimo en plano medio; los elementos del primer término pasan a toda velocidad y el fondo gana desenfoque de movimiento horizontal |
| Whip látigo de cámara | Giros, esquivas, instante del impacto, cambios bruscos de dirección | Sorpresa, sensación de estallido | WHIP pasa rozando en el instante del contacto con el objetivo, y el foco salta de inmediato al golpeado |
| Gentle retroceso lento | Fin de la contención, asentamiento del polvo, muestra de la configuración del campo de batalla | Tensión tras la conclusión | La cámara retrocede lentamente desde el punto más caliente del choque, con el foco clavado en el personaje mientras el campo de batalla del fondo se va desplegando |
| Shock sacudida | Golpes pesados, explosiones, roturas, derrumbes | Conmoción profunda | En el instante del impacto, shake de la cámara durante 0.3 segundos, con un leve temblor de la imagen y gravilla del suelo reventando en la dirección de la onda de choque |

## Reglas de escritura (acople con los campos del storyboard)

- `movement`: elige de la tabla de arriba el nombre de la fórmula o una combinación (p. ej. «persecución en el aire (contrapicado en posición baja + barrido ascendente rapidísimo)»); un movimiento principal de cámara por sub-plano
- El 【镜头N】 de la `description`: al principio del sub-plano se escribe la instrucción completa del plano = **posición/ángulo + tipo de movimiento + adverbio de velocidad + tamaño de plano**; las cifras (0.5 metros, 0.15 segundos, 0.3 segundos) se conservan tal cual — el video-prompt se despliega segmento a segmento a partir de la description, y perder una cifra es perder la sensación de velocidad
- El adverbio de velocidad debe ser concreto: rapidísimo/velocidad uniforme/despacio/rápido al principio y lento al final; prohibido escribir solo «acercamiento» o «seguimiento»
- Un movimiento de cámara por segmento, continuo dentro del segmento; los segmentos de pelea permiten cambiar de fórmula con corte en seco entre sub-planos, con los puntos de corte alineados con los 【镜头N】
- **Combinar rápido y lento**: tras 2-3 sub-planos rapidísimos seguidos, usa un retroceso lento Gentle o una parada a cuadro del impacto como colchón antes de entrar en la siguiente explosión; todo rapidísimo en el segmento se convierte en un borrón, y todo lento pierde la sensación de opresión
- El bullet time/la cámara lenta siguen siendo trucos de realce: respetan el tope de 1-2 por episodio de la normativa básica y se reservan para el instante del impacto o el cierre a cuadro

## Plantillas universales (aplicación directa)

- **Arranque a alta velocidad**: fórmula 1 (acercamiento rapidísimo en posición baja) + Swift
- **Segmento de combos**: fórmula 7 (distancia mínima con DOLLY) ↔ fórmula 2 (ORBIT con cambio de foco), con corte en seco entre sub-planos
- **Esquiva y contraataque**: fórmula 8 (acercamiento inverso con cambio de foco) + Whip
- **Explosión de golpe pesado**: fórmula 5 (difuminado de 0.15 segundos en el impacto) + Shock (shake de 0.3 segundos) → fórmula 6 (alejamiento rapidísimo con estela)
- **Cierre a cuadro**: fórmula 10 (MCU con acercamiento lento → retroceso lento Gentle), para cargar el próximo golpe

## Resumen en una frase

La esencia de la cámara de pelea es «**no dejar de moverse jamás**» — transmitir al espectador la velocidad y la opresión mediante el movimiento de cámara, alternar lo vertiginoso con el cuadro breve, y aprovechar los resquicios entre técnica y técnica para cargar impulso y enlazar.
