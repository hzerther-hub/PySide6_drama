---
name: video-prompt
description: Padrão do prompt de vídeo — gera, a partir do conteúdo de um segmento de storyboard, um prompt de geração de vídeo dividido por tempo, com cortes permitidos dentro do segmento
---

# Prompt de Vídeo (segmento de storyboard → video_prompt)

A partir do description de um único segmento de storyboard (contendo a estrutura de subplanos 【镜头N】 e as falas/narração), do atmosphere e do duration, gere o `video_prompt` que dirige a geração de vídeo por IA. **Um segmento de storyboard = um vídeo de 8-15 segundos, com cortes permitidos internamente**: entre segmentos podem haver planos diferentes (mudança de enquadramento/ângulo/sujeito), emendados por corte seco; mas **nunca se atravessam cenários** e não há flashbacks.

## Formato

A **primeira linha do `video_prompt` é o cabeçalho informativo**: primeiro apresente quais personagens e cenários aparecem neste vídeo, e então siga com as fatias de tempo. Personagens e cenários são sempre referenciados com @ (na geração são substituídos pelas marcas das imagens de referência correspondentes, para o modelo de vídeo primeiro alinhar "quem" e "onde").

```
Personagens: @João, @Maria; Cenário: @Cafeteria.
0-3s: @Cafeteria, plano próximo, a câmera oscila levemente como respiração e avança devagar em direção a @João; ele olha para o celular, os dedos batem repetidamente na mesa, expressão ansiosa.
3-6s: corta para um plano geral da porta; a campainha toca, @Maria empurra a porta e entra, trazendo uma rajada de ar frio.
6-9s: corta de volta ao plano médio, @Maria caminha sorrindo até João e se senta; João diz: "Você finalmente chegou."
```

Regras do cabeçalho:
- Liste apenas os personagens que realmente aparecem neste segmento de storyboard e o cenário vinculado — não liste quem não aparece
- Quando um prop tem participação notável, ele pode ser acrescentado ao cabeçalho (ex.: `; Props: @Carta`)
- O cabeçalho ocupa linha própria, termina com ponto, e depois vêm as fatias de tempo

Divida em fatias de 3 segundos, cada fatia em linha própria separada por quebras de linha, com faixas de tempo contíguas (sem sobreposição, sem lacunas).

## Mapeamento com a Descrição do Storyboard

O `description` é a única fonte de conteúdo do video_prompt (visual, ações, falas e narração estão todos nele); regras de conversão:

- Cada `【镜头N】` do `description` mapeia para **1-2 fatias contínuas de 3 segundos** — mesma ordem, sem omissões, sem fusões, sem criar subplanos novos
- As falas/narração são extraídas de "NomeDoPersonagem diz: "…"" e "Narração: …" dentro do `【镜头N】` correspondente e atribuídas às fatias mapeadas daquele subplano; **não invente falas novas além do description**
- As ações visuais seguem o `description`; o `atmosphere` serve apenas para completar a luz, a tonalidade e a atmosfera de cada fatia

## Estrutura Dentro da Fatia

Organize cada fatia nesta ordem (itens sem conteúdo podem ser omitidos, mas ação/visual são obrigatórios):

**Faixa de tempo + referência @ do cenário + enquadramento/movimento de câmera + referência @ do personagem + ação principal·expressão + fala/narração + atmosfera e luz**

- **A primeira fatia deve estabelecer o espaço**: cenário + posição de câmera + posição e estado dos personagens, para o público saber num relance onde estamos e a quem olhar
- **Cortes**: a fatia seguinte a um corte começa com palavra de emenda como "corta para / volta para", e reexplica enquadramento e sujeito; os pontos de corte devem alinhar com a estrutura `【镜头N】` do `description` do storyboard
- **Enquadramento/movimento de câmera (regra rígida)**: cada fatia deve indicar tanto o **enquadramento** (plano próximo/plano médio/plano geral/close) quanto uma **instrução de movimento de câmera**; dentro de um mesmo subplano o movimento é contínuo e pode trocar após um corte. Escreva na forma "enquadramento inicial + modo de movimento + velocidade/ritmo", ex.: "avanço lento e uniforme do plano médio até o close do rosto", "travelling lateral acompanhando o personagem, com paralaxe fluindo ao fundo". Proibido deixar a fatia inteira só com "câmera fixa" sem informação de movimento — a câmera precisa "se mover" (deslocamento, zoom, seguimento, oscilação de respiração contam) para evitar quadros parados estilo slide. Veja o vocabulário na seção "Padrões de Movimento de Câmera"
- **Ação**: uma ação principal por fatia, com verbos concretos e visíveis (andar, virar-se, erguer o olhar, apertar, parar)
- **Toda emoção vira descrição visível**: nada de palavras abstratas como "ele está muito triste / o clima está tenso" — escreva "ele abaixa a cabeça, os dedos apertam a borda do copo, a respiração fica mais pesada"
- **Fala/narração**: escreva "NomeDoPersonagem diz: "fala"", narração como "Narração: conteúdo"; fala longa que não cabe em 3 segundos é dividida em várias fatias; fatias sem fala podem registrar som ambiente/som de ação (ex.: "as máquinas rugem sem parar")

## Regras de Referência

- `@NomeDoCenário` — referência de cenário; o nome deve coincidir exatamente com o local na lista de cenas
- `@NomeDoPersonagem` — referência de personagem; o nome deve coincidir exatamente com o nome na lista de personagens
- `@NomeDoProp` — referência de prop; o nome deve coincidir exatamente com o nome na lista de props; referencie o prop quando estiver claramente visível no quadro, for usado ou aparecer em close
- Na geração, cada `@nome` é substituído automaticamente pela marca da imagem de referência correspondente (ex.: `@João` → `@Imagem1João`); portanto os nomes devem casar com precisão — não abrevie nem acrescente símbolos extras
- **Cada fatia precisa de pelo menos uma referência @ ancorando o quadro**; fatias em que um personagem aparece devem @ esse personagem; referencie apenas cenários/personagens/props já vinculados a este segmento de storyboard

## Regras de Linha do Tempo

- Número de fatias = duration do segmento de storyboard ÷ 3 segundos (arredondado para cima); a soma das faixas de tempo das fatias deve ser igual à duração total do segmento
- Ritmo do conteúdo: a primeira fatia estabelece → as do meio avançam a ação/conflito → a última pousa no resultado ou no ponto emocional

## Padrões de Movimento de Câmera

Cada fatia de tempo carrega um movimento de câmera, escolhido do vocabulário abaixo e coerente com a intenção de câmera dos campos `description`/`movement` do storyboard (o que o description declarar de câmera, o video_prompt expande; se o description não declara, escolha o mais adequado ao visual):

- **Narrativa básica**: avanço lento (plano médio → close, uniforme, fundo esvaindo em desfoque), recuo revelador (close → plano geral, rápido no começo e lento no fim), travelling lateral de acompanhamento (move-se com o personagem, paralaxe fluindo ao fundo), grua de elevação/descida (sobe/desce na vertical revelando o espaço), órbita em arco (90-180 graus ao redor do personagem), caminhada em primeira pessoa (altura do olhar, leve ondulação de respiração)
- **Emoção e atmosfera**: ofego com câmera na mão (tremor sutil que se acentua após o movimento), ângulo de espião (vista estreita com oclusão no primeiro plano), pulso cardíaco (avanço/recuo sincronizado ao ritmo emocional, avanço lento na calma/rápido na tensão), sintonia com a respiração (avança de leve ao inspirar, recua devagar ao expirar)
- **Psicologia e detalhe**: foco no olhar (avanço pausado em direção ao objeto observado, com transferência de foco), tremor de pavor (vibração fina e irregular), órbita terna (órbita lenta de ângulo pequeno com foco travado no rosto), cauda em alta velocidade (segue de perto o alvo em movimento, com desfoque de movimento), travessia de luta (alternância rápida entre os dois lutadores), mergulho aéreo (queda de grande altura, com leve choque ao pousar)
- **Combate em alta velocidade**: só quando o `description` do storyboard declarar explicitamente câmera de luta, expanda exatamente como descrito (posição, velocidade e números — nenhum pode se perder): avanço rasante veloz em posição baixa, acompanhamento rente ao chão, tilt-up veloz, acompanhamento colado em distância extrema, avanço reverso com troca de foco, recuo veloz na esteira do voo, desfoque de alta velocidade de 0.15 segundos no instante do impacto, shake de choque de 0.3 segundos
- **Ângulos especiais**: contra-plongée extremo, inclinação holandesa (dutch angle), plano próximo sobre o ombro, ponto de vista subjetivo (POV)
- **Transições de ritmo**: panorâmica chicote (a direção do chicote coincide com a direção de movimento da fatia seguinte), transição por obstrução (objeto do primeiro plano varre e oclui no instante do corte), parada brusca congelada (desacelera até congelar — apenas em fatias de clímax)

Exigências de escrita:
- A instrução de câmera vem sempre casada com enquadramento e velocidade: "avança lentamente do plano geral até o plano médio"; nunca escreva apenas "avanço"
- Advérbios de velocidade concretos: uniforme/lento/veloz/rápido depois lento/lento que acelera
- Um movimento de câmera por fatia; contínuo dentro da fatia, trocando apenas nos pontos de corte
- Bullet time / close em câmera lenta / olho de peixe / maquete em miniatura são truques de realce — use apenas quando o `description` do storyboard os declarar explicitamente, no máximo 1-2 por episódio
- Tremor na mão e ondulação de respiração são "micromovimentos" que podem ser usados nas fatias que você escreveria como câmera fixa, substituindo a imobilidade total

## Proibições

- Troca entre cenários, flashbacks (um segmento acontece dentro de um único cenário)
- Referenciar nomes de cenários/personagens fora das listas
- Descrição psicológica abstrata, metáforas literárias (o modelo só reconhece imagens visíveis)
- Atuação exagerada: não escreva gritos, urros, alvoroços, choro alto; susto vira microrreação (congelar, pupilas se fecharem de leve, aspirar o ar de repente, meio passo para trás); falas em tom e volume cotidianos (quando o enredo extremo realmente exigir explosão, escreva explicitamente "explosão emocional" na fatia para sobrepor)
- Câmera lenta e paralisação: por padrão não use câmera lenta nem escreva longas paradas olhando fixamente; exceção: subplanos de clímax com bullet time/close em câmera lenta/parada brusca congelada declarados explicitamente no `description` do storyboard podem ser usados conforme o description. Cada fatia ainda precisa de movimento de câmera visível ou avanço de ação — "plano puramente estático" não é permitido
- Idioma que não corresponde à diretiva de idioma da sessão

## Salvamento

Chame `update_storyboard` para atualizar apenas o campo `video_prompt` deste segmento de storyboard; não mexa nos demais campos e não redesmonte o episódio inteiro. A plataforma acrescenta automaticamente as salvaguardas de atuação e ritmo na requisição real de geração; o prompt não precisa repetir essas exigências.
