# 🔎 Estudos — *RAG from First Principles* (Jia Huang)

> **A melhor forma de estudar um livro técnico é ler e praticar ao mesmo tempo.**
> Leia uma seção, feche o livro e escreva o código com as próprias mãos. Só depois confira o gabarito.

Este repositório registra meu estudo de *RAG from First Principles* (Packt, em inglês). O livro percorre o *pipeline* de *Retrieval-Augmented Generation*: importar dados, dividir em pedaços, gerar embeddings, armazenar vetores, tratar a consulta antes e o resultado depois da busca, gerar a resposta e avaliar o sistema.
Os cadernos estão em português e mantêm os termos técnicos no original. Cada seção aponta para a página do PDF e, quando cabe, traz um exercício que monta **uma peça do RAG do zero**.

## 🔁 O método

| Passo | O que fazer | Onde |
|---|---|---|
| 1. Ler | Ler a seção indicada | PDF do livro (página no caderno) |
| 2. Praticar | Escrever a solução do 🧪 exercício **sem olhar a resposta** | `praticar/capXX_*.ipynb` |
| 3. Conferir | Comparar com o gabarito | `resolvidos/capXX_*.ipynb` |
| 4. Resumir | Explicar com as próprias palavras nas células 📝 | `praticar/` |
| 5. Registrar | Commit + push | GitHub |

## 📚 Conteúdo (30 exercícios)

| Cap. | Peça do RAG | O que se constrói |
|---|---|---|
| 1 | *Data import* | carregador de .txt, JSON com filtro, CSV → documentos, limpeza de HTML, divisão de Markdown por títulos |
| 2 | *Chunking* | contagem de tokens, chunking fixo × por frases × recursivo, *summary index*, **HyDE** |
| 3 | *Embedding* | cosseno × produto escalar, busca semântica, BM25 × TF-IDF |
| 4 | *Vector storage* | banco vetorial mínimo com filtro e remoção, índice **IVF** com k-médias (recall × tempo), *upsert* com hash |
| 5 | *Pre-retrieval* | **Text-to-SQL** com `sqlite3`, *self-query* (filtro de metadados em JSON), *multi-query*, roteador |
| 6 | *Index optimization* | *sentence window*, busca híbrida com **RRF** |
| 7 | *Post-retrieval* | **MMR**, peso por recência, compressão de contexto, correção no estilo CRAG |
| 8 | *Generation* | RAG completo com citações e "não sei" |
| 9 | *Evaluation* | hit rate@3 e MRR, fidelidade com **LLM-as-a-judge** |
| 10 | *Agentic RAG* | laço com *function calling*: o modelo decide quando buscar |

A base de conhecimento (`comum/corpus.py`) é **inventada**: regras de uma biblioteca fictícia. Por isso pode ser enviada ao modelo sem risco.

## 🛠️ Melhorias e escolhas

- O livro usa LangChain, LlamaIndex e Milvus. Aqui cada técnica é **implementada à mão** (NumPy, `rank_bm25`, scikit-learn, `sqlite3`) para entender o mecanismo; depois fica fácil reconhecer o mesmo conceito nos *frameworks*.
- Os modelos são acessados pelo **OpenRouter** com o SDK da OpenAI (`comum/ia.py`), com controle de custo (`gasto()`).
- A chave fica **cifrada pelo Windows (DPAPI)** em `%USERPROFILE%\.secrets\openrouter.dpapi`, ou na variável `OPENROUTER_API_KEY`. Ela nunca vai para o código.
- 17 dos 30 exercícios rodam **sem internet**. O teste automático (`ferramentas/testar_cadernos.py`) executa o gabarito offline e separa erros de código (0) de células que dependem do modelo.

## ▶️ Como usar

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-estudos.txt
# chave do OpenRouter: variável de ambiente OPENROUTER_API_KEY (ou arquivo DPAPI, ver comum/ia.py)
$env:OPENROUTER_API_KEY="teste"; $env:IA_BASE_URL="http://127.0.0.1:9/v1"
.venv\Scripts\python.exe ferramentas\testar_cadernos.py resolvidos   # teste offline do gabarito
```

Abra `praticar/cap01_*.ipynb` no VS Code e escolha o kernel `.venv`. O [Guia de Estudos (PDF)](Guia_de_Estudos.pdf) explica o passo a passo.

## ⚖️ Direitos autorais

O livro **não** está neste repositório. Para estudar, use a sua própria cópia. O código oficial (licença MIT) está em [PacktPublishing/RAG-from-First-Principles](https://github.com/PacktPublishing/RAG-from-First-Principles).
Os exercícios, os cadernos, os scripts e o guia são autorais e estão sob licença [MIT](LICENSE).
