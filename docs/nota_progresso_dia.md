# Nota de progresso — TCC Previsão de Demanda (Olist)

Resumo do que foi feito e decidido na sessão de hoje (Sprint 7 e início do Sprint de Machine Learning), com as justificativas de cada decisão técnica. Uso: continuar a definição de escolhas em outra ferramenta, mantendo coerência com o que já foi construído.

---

## Contexto herdado (sessões anteriores, para referência)

- Pipeline: Bronze → Silver → Gold já implementado e validado no PostgreSQL.
- Granularidade da previsão: **por categoria de produto, mensal**.
- Definição de demanda: `COUNT(*)` de `order_items` (cada linha = 1 unidade vendida), considerando apenas pedidos com `order_status = 'delivered'`.
- Decisão de Pareto (agrupar categorias de cauda longa em "outras") foi **adiada para versão futura** — todas as 74 categorias originais permanecem na Gold.
- Camada Gold (`gold.monthly_category_sales`) foi corrigida para incluir um **grid completo** (todo mês × toda categoria, via `generate_series` + `CROSS JOIN` + `LEFT JOIN` com `COALESCE(demand, 0)`), evitando que meses sem venda simplesmente desaparecessem da agregação. Validado com invariante: `SUM(demand)` na Gold = `COUNT(*)` na Silver de `order_items` (bateu).

---

## 1. Exploração de dados (EDA) realizada hoje

Gráficos gerados a partir da Gold (`gold.monthly_category_sales`):

- Demanda mensal total (linha do tempo)
- Distribuição da demanda (histograma + boxplot)
- Top 10 categorias por volume
- Top 5 categorias ao longo do tempo
- Percentual de linhas com demanda zero: **28,32%**
- Sazonalidade mensal (média por mês, ano-agnóstico)

### Achados e decisões derivadas:

**a) Pico de novembro/2017** — investigado e explicado: coincide com a Black Friday (24/nov/2017). O aumento é distribuído entre várias categorias top (não concentrado em uma só), consistente com efeito de evento de plataforma, não tendência de nicho. **Limitação:** só existe 1 Black Friday completa no dataset, então não dá pra validar estatisticamente como padrão recorrente — é conhecimento de negócio, não padrão aprendido com confiança estatística.

**b) Meses de ramp-up da plataforma (set-dez/2016)** — identificados como tendo demanda artificialmente baixa (não é sazonalidade real, é a Olist ainda tendo poucos vendedores cadastrados). **Decisão:** remover esses meses do **treino do modelo**, mas manter intactos na Gold (a Gold deve preservar o histórico fiel; a decisão de não usá-los é de modelagem, não de engenharia de dados).

**c) 28,32% das observações têm demanda = 0** — decisão derivada: **não usar MAPE puro** como métrica (quebra matematicamente com zeros). Usar **MAE, RMSE e WAPE** (Weighted Absolute Percentage Error, que divide soma de erros pela soma da demanda real, não linha a linha).

**d) Distribuição de demanda fortemente assimétrica à direita**, com muitos outliers — reflexo direto de não ter aplicado o Pareto ainda (cauda longa de categorias). Motivou preferência por modelos baseados em árvore (Random Forest, Gradient Boosting) sobre Regressão Linear pura, já que lidam melhor com essa assimetria sem precisar de transformação logarítmica.

**e) Sazonalidade mensal (gráfico bruto) está enviesada** — meses set-dez têm menos anos completos de dado disponível (só 2017, enquanto jan-ago têm 2017+2018), então a comparação entre meses não é justa. Recalcular após excluir ramp-up antes de tirar qualquer conclusão de sazonalidade.

---

## 2. Preocupação levantada: só 24 meses de histórico é suficiente para um TCC (e possível publicação)?

- Avaliação: não deve prejudicar a **nota do TCC** (bancas valorizam mais rigor metodológico e reconhecimento de limitações do que métricas perfeitas). Pode ser mais escrutinado em **peer review de revista** (mesmo B3/B4).
- Mitigação: documentar explicitamente a limitação, definir horizonte de previsão curto (1-3 meses, não 12), e usar abordagem de **modelo global** (todas as categorias treinadas juntas, não uma série por categoria) — isso multiplica o volume de amostras de treino disponível.
- Pesquisa feita: encontrado artigo publicado em **outubro/2025, conferência IEEE** ("Leveraging Multiple Models to Enhance Sales Demand Forecasting in Brazilian E-commerce"), usando o mesmo dataset Olist, também na granularidade de categoria — serve de precedente acadêmico. Outro paper (Garnier & Belletoile, Cdiscount) defende exatamente a abordagem de modelo global com Tree Boosting para séries curtas de e-commerce, o que dá respaldo teórico à escolha de arquitetura de modelo já feita.

---

## 3. Feature Engineering (`python/modeling/build_features.py`)

Features construídas para o modelo global (uma linha = categoria × mês):

- `month_sin`, `month_cos` — mês codificado como variável **cíclica** (não como inteiro 1-12 puro), para não sugerir falsa distância entre dezembro e janeiro.
- `is_black_friday_month` — flag manual (novembro = 1).
- `demand_lag_1`, `demand_lag_2` — demanda dos 2 meses anteriores, calculada **por categoria** (cada série usa só seu próprio histórico).
- `rolling_mean_3` — média móvel de 3 meses anteriores, também por categoria.
- Linhas com `NaN` nos lags (início de cada série) são **removidas**, nunca preenchidas artificialmente.
- Meses de ramp-up (< 2017-01) removidos antes de qualquer cálculo de feature.

### Bug encontrado e corrigido:
`grouped.shift(1).rolling(window=3).mean().reset_index(level=0, drop=True)` estava com um `reset_index` desnecessário que descartava o índice original correto e o substituía por um índice sequencial novo — causando desalinhamento na hora de atribuir a coluna de volta ao DataFrame (valores de linhas erradas sendo atribuídos, e linhas válidas virando `NaN` por engano). Corrigido usando `.transform(lambda s: s.shift(1).rolling(window=3).mean())`, que preserva o alinhamento correto e respeita os limites de cada categoria. Resultado antes do fix: 883 linhas válidas (errado). Depois do fix: **1.258 linhas** (matematicamente esperado: 1.480 linhas após remover ramp-up, menos 3 primeiros meses de cada uma das 74 categorias = 222 linhas perdidas por causa dos lags/rolling → 1.258).

---

## 4. Estratégia de treino/teste (decidida, ainda não executada com resultado)

- Split **temporal** (nunca embaralhar série temporal).
- **3 meses finais como teste**, restante como treino (~14 meses de treino, considerando os ~17 meses utilizáveis de calendário após remover ramp-up e perdas de lag).
- Justificativa do "3 meses" (não 12): com apenas ~17 meses utilizáveis, reservar 12 para teste deixaria só ~5 meses de treino — insuficiente para aprender qualquer variação temporal, e ainda puniria a avaliação por testar um horizonte muito distante do que o modelo real usaria (previsão de 1-3 meses à frente é o horizonte definido como defensável, dado a limitação de sazonalidade anual).

## 5. Script de treino/avaliação criado (`python/modeling/train_and_evaluate.py`)

- Modelos comparados: Regressão Linear (baseline), Random Forest, Gradient Boosting.
- Encoding: `OneHotEncoder` para `product_category_name` (fit somente no treino, para evitar vazamento de dado), demais features numéricas passam direto.
- Uso de `Pipeline` do scikit-learn (empacota pré-processamento + modelo, evita vazamento de dado e facilita salvar o modelo depois).
- `np.clip(y_pred, 0, None)` — Regressão Linear pode prever valores negativos matematicamente; forçado para zero, já que demanda nunca é negativa.
- Métricas calculadas: MAE, RMSE, WAPE (motivo do WAPE em vez de MAPE: ver item 1c acima).
- **Ainda não executado** — próximo passo é rodar e comparar os 3 modelos.

---

## Pendências / próximos passos

1. Rodar `train_and_evaluate.py` e obter a tabela comparativa dos 3 modelos.
2. Decidir se a decisão de Pareto (categorias de cauda longa → "outras") deve ser revisitada antes de finalizar o modelo, ou realmente ficar como trabalho futuro documentado.
3. Encoding de `product_category_name` já resolvido no script de treino (One-Hot) — não precisa revisitar, a menos que troque de abordagem de modelo.
4. Gráficos de previsão vs. demanda real (para o TCC) — ainda não iniciado.
5. Dashboard Power BI — ainda não iniciado.
