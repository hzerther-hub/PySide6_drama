---
name: extractor
description: Regras e métodos para extração de personagens, cenas e props
---

# Guia de Extração de Personagens, Cenas e Props

## Regras de Extração de Personagens

Campos dos personagens extraídos (correspondência um a um com os parâmetros da ferramenta `save_dedup_characters`):
- **name** (obrigatório): nome completo do personagem
- **role**: posicionamento do personagem — protagonista/coadjuvante/figurante
- **appearance**: descrição da aparência (300-500 caracteres) — sexo, idade aparente, traços do rosto, físico, presença. **Não gere os traços de personalidade em campo separado; converta-os em presença exterior e expressões incorporadas à descrição da aparência** (ex.: "personalidade fria" deve ser escrito como "olhar gélido, expressão contida, raramente sorri")
- **styling**: figurino e maquiagem — penteado, roupas, maquiagem, acessórios etc.
- **description**: história de fundo e relacionamentos (complemento opcional)

## Regras de Extração de Cenas

Campos das cenas extraídas (correspondência um a um com os parâmetros da ferramenta `save_dedup_scenes`):
- **location** (obrigatório): nome concreto do local
- **time**: período do dia (ex.: dia/entardecer/madrugada); o mesmo local em outro período conta como nova cena
- **prompt**: descrição da cena — espaço, ambientação, textura de época, elementos visuais-chave (fundo puro, sem pessoas)
- **lighting**: luz da cena — fontes de luz, tonalidade, contraste claro-escuro, atmosfera

## Regras de Extração de Props

**Princípio central: antes extrair de menos do que de mais.** Props são ativos de alto custo, usados para gerar imagens de item único em fundo branco e referenciados em closes de vídeo; só valem extração os props essenciais à trama. Um episódio costuma ter **0-3** props-chave; se houver mais de 3, ordene por importância na trama e mantenha apenas os 3 primeiros.

É preciso atender **simultaneamente** às duas condições abaixo — nenhuma é dispensável:
1. **Impulsiona diretamente a trama**: o surgimento, a entrega, o dano ou a descoberta do item dispara uma virada do enredo (ex.: arma do crime, lembrança/talismã, documento decisivo, presente de amor, prova decisiva).
2. **Merece imagem própria**: os storyboards seguintes darão closes nele ou ele reaparece, exigindo aparência fixa.

**Três perguntas de triagem** (pergunte e responda a si mesmo para cada prop candidato; se qualquer resposta for "não", descarte):
- (1) A trama continua de pé se ele for removido? → Se sim, **não extraia** (é apenas um cenário de fundo)
- (2) É apenas um objeto cotidiano de uso casual (celular, palitos, copo, cigarro, guarda-chuva)? → Se sim, **não extraia**
- (3) Faz parte da ambientação da cena (mesas e cadeiras, luminárias, portas e janelas, quadros de parede, louça de mesa)? → Se sim, **não extraia** (isso pertence à descrição da cena)

**O que não conta como prop**: objetos comuns de uso casual que não afetam o rumo da trama; ambientação e móveis da cena; itens mencionados uma única vez e nunca mais; o vestuário habitual do personagem (vai para o styling do personagem).

Se nenhum prop se qualificar, **não force a extração** — basta passar um array vazio ao chamar `save_dedup_props`.

Campos dos props extraídos (correspondência um a um com os parâmetros da ferramenta `save_dedup_props`):
- **name** (obrigatório): nome do prop
- **type**: categoria — cotidiano/arma/transporte/decoração/documento etc.
- **description**: aparência do item — descreva apenas o aspecto físico do objeto em si (material, cor, forma, tamanho, grau de novo/desgaste, marcas de uso etc.); não descreva a função na trama nem relações com personagens ou outros elementos

Props **não precisam de prompt de imagem** — o prompt final de um prop é gerado especificamente pelo Agent de geração de prompts antes da geração da imagem (padrão de item único em fundo branco).

## Passos de Uso

1. Chame `read_script_for_extraction` para ler o roteiro do episódio atual
2. Chame `read_existing_characters` para ver os personagens já existentes no projeto e os já vinculados ao episódio atual
3. Chame `read_existing_scenes` para ver as cenas já existentes no projeto e as já vinculadas ao episódio atual
4. Chame `read_existing_props` para ver os props já existentes no projeto e os já vinculados ao episódio atual
5. Extraia apenas os personagens, cenas e props realmente envolvidos no episódio atual
6. Chame `save_dedup_characters` para salvar os personagens e vinculá-los automaticamente ao episódio atual
7. Chame `save_dedup_scenes` para salvar as cenas e vinculá-las automaticamente ao episódio atual
8. Chame `save_dedup_props` para salvar os props e vinculá-los automaticamente ao episódio atual

## Regras do Episódio Atual

- O objetivo é completar os personagens, cenas e props de que o "episódio atual" precisa, não revarrer o projeto inteiro
- Se um ativo já existe no projeto mas ainda não está vinculado ao episódio atual, reutilize-o e vincule-o ao episódio atual
- Regras de deduplicação: personagens/props casam por nome exato; cenas casam por [local + período] exato; em caso de correspondência, prefira reutilizar — não crie duplicatas
- Deduplicação de nomes próximos: quando o nome traz um qualificador entre parênteses ou um apelido, compare pela parte principal antes do parêntese (ex.: "Ana (protagonista)" e "Ana" são o mesmo personagem/prop — reutilize o existente); o normalized_name retornado por read_existing_characters / read_existing_props é o nome normalizado, e normalized_location faz o mesmo papel para as cenas — julgue com base neles
