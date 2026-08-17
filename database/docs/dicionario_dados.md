# Dicionário de Dados — Previsão de Demanda no Varejo (Olist)

## Decisões de escopo já travadas

- **Granularidade da demanda:** por categoria de produto (`product_category_name`)
- **Periodicidade:** mensal
- **Definição de "demanda":** quantidade de itens vendidos (não receita) por categoria, por mês, considerando apenas pedidos efetivamente concluídos (ver nota sobre `order_status` abaixo)

Essa definição precisa ficar explícita no TCC, porque "demanda" é um conceito que varia de contexto (pode ser pedidos, itens, receita, ou até demanda "não atendida" por ruptura de estoque — que este dataset não permite medir, já que só registra vendas realizadas).

---

## Tabelas do dataset e uso no pipeline

| Tabela (arquivo original) | Uso no pipeline | Camada |
|---|---|---|
| `olist_orders_dataset` | Essencial — data do pedido, status | Bronze → Silver |
| `olist_order_items_dataset` | Essencial — item vendido, produto, quantidade | Bronze → Silver |
| `olist_products_dataset` | Essencial — liga produto à categoria | Bronze → Silver |
| `product_category_name_translation` | Essencial — tradução da categoria (PT→EN) | Bronze → Silver |
| `olist_order_payments_dataset` | Opcional — não afeta demanda em quantidade; pode virar feature futura (ticket médio, parcelamento) | Não usada na v1 |
| `olist_order_reviews_dataset` | Opcional — não afeta demanda diretamente; poderia virar feature de "satisfação por categoria" em versão futura | Não usada na v1 |
| `olist_customers_dataset` | Opcional — útil se quiser segmentar por região no futuro | Não usada na v1 |
| `olist_sellers_dataset` | Opcional — útil se quiser segmentar por vendedor/região | Não usada na v1 |
| `olist_geolocation_dataset` | Não usada — granularidade geográfica não faz parte do escopo atual | Descartada |

**Por que descartar tabelas ativamente?** Um erro comum em projetos de portfólio é importar tudo "porque tá disponível". Isso infla a Bronze sem necessidade e sugere, numa entrevista, que você não sabe justificar escopo. Aqui, geolocation e reviews não têm relação causal direta com a série de demanda mensal por categoria — então ficam de fora da v1, mas eu documento a decisão (isso é uma boa prática de engenharia: decisões de escopo documentadas, não silenciosas).

---

## Colunas relevantes por tabela

### `olist_orders_dataset` (núcleo temporal)

| Coluna | Tipo | Descrição | Relevância |
|---|---|---|---|
| `order_id` | string (PK) | Identificador único do pedido | Chave de junção |
| `order_status` | string | Status do pedido (delivered, shipped, canceled, unavailable, etc.) | **Crítica** — define o que conta como demanda real |
| `order_purchase_timestamp` | timestamp | Data/hora da compra | **Crítica** — base do agrupamento mensal |
| `order_approved_at` | timestamp | Data de aprovação do pagamento | Não usada na v1 |
| `order_delivered_customer_date` | timestamp | Data de entrega | Não usada na v1 (poderia alimentar uma análise de lead time depois) |
| `order_estimated_delivery_date` | timestamp | Data estimada de entrega | Não usada na v1 |

**Decisão de negócio a documentar no TCC:** apenas pedidos com `order_status = 'delivered'` devem contar como demanda efetiva. Pedidos cancelados ou indisponíveis não representam demanda atendida, e incluí-los infla artificialmente a série. Isso é uma regra de negócio que pertence à camada **Silver**.

### `olist_order_items_dataset` (quantidade vendida)

| Coluna | Tipo | Descrição | Relevância |
|---|---|---|---|
| `order_id` | string (FK) | Liga ao pedido | Chave de junção |
| `order_item_id` | int | Número sequencial do item dentro do pedido | Usado para contar quantidade (cada linha = 1 unidade vendida) |
| `product_id` | string (FK) | Liga ao produto | Chave de junção com `products` |
| `price` | decimal | Preço do item | Não usada na v1 (poderia virar feature de receita depois) |
| `freight_value` | decimal | Valor do frete | Não usada na v1 |

**Nota importante:** este dataset não tem uma coluna explícita de "quantidade". A quantidade vendida é inferida pela **contagem de linhas** em `order_items` por pedido/produto — cada linha representa uma unidade. Isso precisa estar claro no TCC, porque não é óbvio para quem só olha o schema.

### `olist_products_dataset` (ligação com categoria)

| Coluna | Tipo | Descrição | Relevância |
|---|---|---|---|
| `product_id` | string (PK) | Identificador do produto | Chave de junção |
| `product_category_name` | string | Categoria em português | **Crítica** — dimensão de agrupamento |

Demais colunas (peso, dimensões, comprimento do nome/descrição) — não usadas na v1, mas candidatas a features futuras se você expandir para um modelo por produto.

### `product_category_name_translation`

| Coluna | Tipo | Descrição | Relevância |
|---|---|---|---|
| `product_category_name` | string (PK) | Categoria em português | Chave de junção |
| `product_category_name_english` | string | Categoria traduzida | Usada para o TCC/dashboard ficarem legíveis em inglês, se desejar |

---

## Qualidade de dados validada durante o desenvolvimento

1. **Nulos em `product_category_name`** — 1,85% dos produtos (610 de 32.951) não têm categoria preenchida. Decisão: agrupar como `'categoria_desconhecida'`, nunca descartar.
2. **`order_status`** — `delivered` representa **97,02%** do volume total de pedidos; demais status (shipped, canceled, unavailable, invoiced, processing, created, approved) somam os 2,98% restantes, excluídos da definição de demanda.
3. **Pedidos sem `order_delivered_customer_date` mesmo com status "delivered"** — inconsistência conhecida do dataset; não impacta a definição de demanda adotada (baseada em `order_purchase_timestamp`, não na data de entrega).
4. **Categorias com pouquíssimo volume** — confirmada a existência de forte cauda longa (ex: `seguros_e_servicos` com 2 unidades vendidas no período inteiro). Avaliado como transformação de modelagem, não de engenharia de dados (ver seção seguinte).
5. **Duplicidade de `order_id` em `order_items`** — comportamento esperado (pedido com múltiplos itens), não é erro.

---

## Decisões efetivamente implementadas no pipeline (atualização pós-modelagem)

- **`order_status = 'delivered'`**: decisão de filtro aplicada na camada Silver (`silver.orders`).
- **Categoria nula**: tratada com `COALESCE(product_category_name, 'categoria_desconhecida')` na Silver — não descartada, para preservar 100% do volume de demanda real.
- **Grid completo (categoria × mês) na Gold**: `gold.monthly_category_sales` inclui todas as combinações possíveis de categoria e mês (via `generate_series` + `CROSS JOIN` + `COALESCE(demand, 0)`), evitando que meses sem venda simplesmente desapareçam da agregação. Validado por invariante: `SUM(demand)` na Gold = `COUNT(*)` de `order_items` na Silver.
- **Cauda longa de categorias (Pareto/ABC)**: avaliada como transformação da camada de **modelagem** (não da Gold/Silver), calculada apenas sobre o período de treino para evitar vazamento de dado. Adotada como estudo comparativo formal (com/sem Pareto), não como filtro definitivo na base.
- **Meses de ramp-up da plataforma (set–dez/2016)**: identificados como tendo demanda artificialmente baixa (não sazonal, reflexo do início de operação da Olist); removidos do treino do modelo, mas mantidos intactos na Gold.
- **Modelo operacional final**: Naive (mês anterior), cenário Sem Pareto — venceu Regressão Linear, Random Forest e Gradient Boosting em WAPE, MAE e RMSE, em ambos os cenários testados.

---

## Referência de arquitetura

Pipeline: `bronze` (réplica fiel da fonte) → `silver` (dado limpo, regras de negócio universais) → `gold` (modelado para a pergunta de previsão de demanda) → camada de modelagem em Python (transformações específicas do modelo, como Pareto e remoção de ramp-up).
