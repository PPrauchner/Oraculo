*[English version](0010-core-devolve-codigo-de-erro-nao-mensagem.en.md)*

# `core/` devolve código de erro, não mensagem pronta

O invariante diz que `core/` não conhece Streamlit, e ao pé da letra ele era respeitado: nenhum
módulo de `core/` importa `streamlit`. Mas `core/ingestion/` devolvia coisas assim:

```python
return False, "❌ O Projeto-Alvo não foi processado corretamente."
return None, f"❌ Caminho não encontrado: {directory}"
```

`core/` não chamava `st.error()`, mas decidia **como o erro aparece** (o `❌`) e **em que língua
ele fala** (português). São doze mensagens assim. O acoplamento não estava no import; estava na
string. Isso só ficou visível quando o produto passou a ter duas línguas: uma mensagem já
formatada chega em `pages/` como texto opaco, e não há mais o que traduzir.

**`core/` devolve um código de erro estável e os dados que o descrevem; `pages/` escolhe ícone,
formatação e língua na hora de renderizar.**

```python
return None, ("directory_not_found", {"path": directory})
```

O código é identificador em inglês, como o resto de `core/`, e não muda com a língua da tela —
mesma lógica que fixou o CSV como contrato (ADR-0008). O ícone deixa de ser caractere embutido
no texto e vira decisão de apresentação, resolvida com SVG em `pages/`. Cada mensagem passa a
existir uma vez por língua em `locales/` (ADR-0009), em vez de uma vez, em português, no meio da
lógica de ingestão.

O custo é churn: a assinatura das funções de ingestão muda e os testes que casavam contra o
texto da mensagem passam a casar contra o código. Em troca, esses testes ficam melhores —
casar contra `"directory_not_found"` não quebra quando alguém reescreve a frase.

Rejeitado: **exceções tipadas** (`raise DirectoryNotFound(path)`). É mais idiomático em Python
puro e carrega o mesmo dado, mas troca o estilo de retorno que `core/ingestion/` já usa de forma
consistente por `try/except` espalhado em `pages/` — refatoração maior, para resolver um
problema que o código de erro resolve sem mudar o formato do fluxo.

Rejeitado: **só remover o emoji**, mantendo a mensagem em português. Atende ao pedido literal e
não atende a nenhuma das razões dele: toda mensagem de erro ficaria presa em português num app
cujo padrão passou a ser inglês, e `core/` continuaria decidindo apresentação.
