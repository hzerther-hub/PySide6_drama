---
name: fight-cinematography
description: Manual de movimento de câmera para combate em alta velocidade — fórmulas de posicionamento de câmera, anotações de velocidade e modo de escrita no prompt para segmentos de luta/perseguição/clímax
---

# Manual de Movimento de Câmera para Combate em Alta Velocidade (exclusivo para segmentos de luta/ação em alta velocidade)

## Quando Ativar (julgamento automático)

Quando o segmento ou algum subplano dentro dele trouxer ações em alta velocidade como **luta, investida, perseguição, esquiva com contra-ataque, chute voador, explosão de golpe pesado, ser arremessado pelo impacto**, o movimento de câmera sai das "fórmulas de posicionamento" e das "anotações de velocidade" deste manual, com prioridade sobre o vocabulário básico de câmera; segmentos de diálogo, de preparação e de transição não usam este manual.

A lógica central são apenas duas coisas: **rápido** e **antecipação** — fabricar velocidade, amplificar velocidade. A câmera serve a três propósitos:
1. Deixar o público ver com clareza a trajetória das ações
2. Reforçar o impacto na direção do ataque
3. Usar a velocidade da câmera para criar sensação de opressão

## Fórmulas de Posicionamento (10)

Cada fórmula = combinação de posição/movimento + golpes aplicáveis + modo de escrita no prompt (a escrita pode ser embutida direto no início do `【镜头N】` do `description`):

| # | Fórmula | Golpes aplicáveis | Escrita no prompt |
|---|---|---|---|
| 1 | Choque de partida: posição baixa + avanço veloz | soco pesado, investida, primeiro confronto | câmera em ângulo baixo a 0.5 metros, avanço veloz de baixo para cima, capturando a poeira levantada pela colisão em alta velocidade dos dois lados e o volume da onda de choque, ângulo LOW reforçando a opressão |
| 2 | Acompanhamento lateral: câmera orbital + troca de foco | combos, troca de ataque e defesa, confronto dinâmico | ORBIT cercando em semi-envolvente por trás do atacante, foco travado nos fios de cabelo e na barra da roupa do atingido, foco trocado no instante do impacto |
| 3 | Acompanhamento rente ao chão: vista rente ao solo + acompanhamento em posição baixa | rasteira, rolagem no chão, ações em baixa altura | a câmera rente ao chão em ângulo baixo segue varrendo o movimento das pernas, os detritos do solo passam rentes à frente |
| 4 | Perseguição aérea: contra-plongée baixo + tilt-up veloz | chute voador, chute giratório, sequência de chutes no ar | contra-plongée em posição baixa, TILT UP veloz acompanhando o personagem em pleno ar, enfatizando a sensação de suspensão |
| 5 | Instante do impacto: parada brusca congelada + leve tremor | golpe certeiro, ponto de explosão | close no instante do impacto, imagem com desfoque de alta velocidade de 0.15 segundos, o local atingido deixa pós-imagem, leve tremor de recuo na câmera |
| 6 | Arremessado pelo impacto: recuo veloz + rastreio | corpo lançado por golpe pesado, repulsão | a câmera recua velozmente, rastreando na direção da esteira de voo do personagem, o fundo se rasga em profundidade |
| 7 | Colagem extrema: vista de acompanhamento + avanço em DOLLY | sequência de socos, golpes combinados | DOLLY avança na horizontal, câmera colada ao limite nos dois lutadores em corpo a corpo, fazendo o público sentir a opressão do vento dos socos |
| 8 | Esquiva com contra-ataque: avanço reverso + troca de foco | esquiva, defesa e contra-ataque | a câmera avança veloz por trás do atacante, PAN chicoteia na horizontal para a direção do contra-ataque, PUSH avança rápido sobre a ação do contra-golpe, o foco salta do atacante ao contra-atacante num instante |
| 9 | Contra-ataque em contraplongée: ângulo baixo + recuo veloz | reação de baixo para cima, golpe em pleno ar | abre em contra-plongée de ângulo baixo, recua veloz conforme o personagem sobe, expandindo num instante do close em contraplongée para um plano geral aéreo |
| 10 | Fechamento congelado: avanço lento em plano próximo + recuo lento | fechar o golpe, apresentação, acumular força para o próximo golpe | MCU com avanço lento congelando a postura do personagem, depois PULL recuando devagar com o fundo em desfoque, preservando a tensão do instante antes da explosão do próximo golpe |

## Anotações de Velocidade (4 tipos, sobrepostas às fórmulas de posicionamento)

| Anotação | Usada para | Efeito | Escrita |
|---|---|---|---|
| Swift acompanhamento veloz | investida, irrupção, perseguição, movimento corpo a corpo | tensão, sensação de velocidade, ritmo forte | avanço/recuo veloz em plano médio; elementos do primeiro plano passam rápido, o fundo ganha desfoque de movimento horizontal |
| Whip panorâmica chicote | virada, esquiva, instante do impacto, mudança súbita de direção | inespero, sensação de explosão | WHIP varre no instante do contato com o alvo, o foco corta no mesmo instante para o atingido |
| Gentle recuo lento | fim da dominação, poeira assentada, exibição do panorama do campo de batalha | tensão após o fecho | a câmera recua lentamente do ponto mais intenso do conflito, foco travado no personagem, o campo de batalha ao fundo se abre aos poucos |
| Shock choque | golpe pesado, explosão, estilhaço, desabamento | abalo profundo | no instante do impacto a câmera faz shake por 0.3 segundos, a imagem treme de leve, as pedras do chão estouram na direção da onda de choque |

## Regras de Escrita (interface com os campos do storyboard)

- `movement`: escolha da tabela acima o nome da fórmula ou uma combinação (ex.: "perseguição aérea (contra-plongée baixo + tilt-up veloz)"), um movimento principal por subplano
- No `【镜头N】` do `description`: comece o subplano com a instrução completa de plano = **posição/ângulo + modo de movimento + advérbio de velocidade + enquadramento**; os números (0.5 metros, 0.15 segundos, 0.3 segundos) permanecem como estão — o video-prompt expande fatia a fatia conforme o description; perder os números é perder a sensação de velocidade
- Os advérbios de velocidade devem ser concretos: veloz/uniforme/lento/rápido depois lento; proibido escrever apenas "avanço" ou "acompanhamento"
- Um movimento de câmera por fatia, contínuo dentro dela; segmentos de luta permitem troca dura de fórmula entre subplanos, com os pontos de corte alinhados ao 【镜头N】
- **Combinação de rápido e lento**: depois de 2-3 subplanos velozes seguidos, use um Gentle recuo lento ou um congelamento de impacto como amortecimento antes de entrar na próxima explosão; um segmento inteiro veloz vira um borrão, um segmento inteiro lento perde a opressão
- Bullet time/câmera lenta seguem sendo truque de realce: respeitam o teto de 1-2 ocorrências por episódio da norma básica e servem apenas para o instante do impacto ou o fechamento congelado

## Modelos Universais (aplicação direta)

- **Abertura veloz**: fórmula 1 (avanço rasante em posição baixa) + Swift
- **Segmento de combos**: fórmula 7 (colagem extrema com DOLLY) ↔ fórmula 2 (ORBIT com troca de foco), corte seco entre subplanos
- **Esquiva com contra-ataque**: fórmula 8 (avanço reverso com troca de foco) + Whip
- **Explosão de golpe pesado**: fórmula 5 (desfoque de 0.15 segundos no impacto) + Shock (shake de 0.3 segundos) → fórmula 6 (recuo veloz na esteira)
- **Fechamento congelado**: fórmula 10 (MCU com avanço lento → Gentle recuo lento), acumulando força para o próximo golpe

## Resumo em Uma Frase

A essência da câmera de luta é "**mover-se o tempo todo**" — usar o movimento de câmera para transmitir ao público a sensação de velocidade e opressão, alternando velocidade extrema e congelamentos breves, completando a acumulação e a emenda nos intervalos entre golpe e golpe.
