"""Exercícios práticos criados para estudar o livro, montando um RAG do zero, peça por peça.

Formato: (capítulo, início do título da seção, nome, enunciado em Markdown, solução em Python).
Usam a base inventada de comum/corpus.py (Biblioteca Municipal Aurora). As chamadas ao modelo passam por comum/ia.py
(OpenRouter); o resto roda sem internet. Os exemplos são originais (não copiados do livro).
"""

EXERCICIOS = [
    # ---------------- 1. Importação de dados ----------------
    (1, "Reading simple text", "Um carregador de documentos",
     "Escreva `carregar_txt(caminho)` que devolve um dicionário `{\"texto\": ..., \"metadados\": {\"fonte\", \"tamanho\"}}`. "
     "Grave dois arquivos .txt temporários com textos da base `DOCS` e carregue os dois.",
     '''import tempfile, os
def carregar_txt(caminho):
    with open(caminho, encoding="utf-8") as f:
        t = f.read()
    return {"texto": t, "metadados": {"fonte": os.path.basename(caminho), "tamanho": len(t)}}
pasta = tempfile.mkdtemp()
for d in DOCS[:2]:
    with open(os.path.join(pasta, d["id"] + ".txt"), "w", encoding="utf-8") as f:
        f.write(d["texto"])
docs = [carregar_txt(os.path.join(pasta, n)) for n in sorted(os.listdir(pasta))]
print([d["metadados"] for d in docs])'''),
    (1, "Parsing specific elements with the JSON", "Extraindo campos de JSON",
     "Converta `DOCS` para uma string JSON e, de volta, extraia só os documentos atualizados a partir de 2025, "
     "guardando `id` e `titulo` como metadados e `texto` como conteúdo (como faz um *JSON loader* com `jq_schema`).",
     '''bruto = json.dumps(DOCS, ensure_ascii=False)
docs = [{"conteudo": d["texto"], "metadados": {"id": d["id"], "titulo": d["titulo"]}}
        for d in json.loads(bruto) if d["data"] >= "2025-01-01"]
print(len(docs), [d["metadados"]["titulo"] for d in docs])'''),
    (1, "Importing table data in CSV", "Uma linha de CSV = um documento",
     "Monte um CSV (em memória, com `io.StringIO`) com colunas `servico, preco, observacao` para impressão e cópias. "
     "Transforme cada linha num documento de texto do tipo \"servico: ...; preco: ...\".",
     '''import csv, io
csv_txt = "servico,preco,observacao\\nimpressao pb,0.30,por pagina\\nimpressao colorida,1.50,por pagina\\ncopia obra rara,,nao permitida\\n"
docs = ["; ".join(f"{k}: {v or '-'}" for k, v in linha.items()) for linha in csv.DictReader(io.StringIO(csv_txt))]
print("\\n".join(docs))'''),
    (1, "Crawling and parsing web", "Limpando HTML para indexar",
     "Com `html.parser`, extraia de um HTML de exemplo só o texto útil (títulos e parágrafos), ignorando `<script>`, "
     "`<nav>` e `<footer>`.",
     '''from html.parser import HTMLParser
html = "<nav>Menu Início</nav><h1>Eventos</h1><p>Clube de leitura na 1ª quinta.</p><script>track()</script><p>Contação aos sábados.</p><footer>© Aurora</footer>"
class Limpador(HTMLParser):
    IGNORAR = {"script", "style", "nav", "footer"}
    def __init__(self):
        super().__init__(); self.pilha, self.partes = [], []
    def handle_starttag(self, tag, attrs): self.pilha.append(tag)
    def handle_endtag(self, tag):
        if self.pilha: self.pilha.pop()
    def handle_data(self, data):
        if data.strip() and not (set(self.pilha) & self.IGNORAR): self.partes.append(data.strip())
l = Limpador(); l.feed(html); print(" | ".join(l.partes))'''),
    (1, "Markdown file titles", "Dividindo Markdown pelos títulos",
     "Escreva um Markdown com `#` e `##` sobre a biblioteca e divida em seções, guardando em cada pedaço o caminho dos "
     "títulos (por ex. `Serviços > Empréstimo`).",
     '''md_txt = """# Serviços
Texto geral.
## Empréstimo
Até 5 livros por 14 dias.
## Impressão
R$ 0,30 por página.
# Espaços
## Sala de estudos
40 lugares."""
secoes, caminho = [], {}
for linha in md_txt.splitlines():
    m = re.match(r"(#+)\\s+(.*)", linha)
    if m:
        nivel = len(m.group(1)); caminho = {k: v for k, v in caminho.items() if k < nivel}; caminho[nivel] = m.group(2)
        secoes.append({"titulos": " > ".join(caminho[k] for k in sorted(caminho)), "texto": ""})
    elif linha.strip():
        secoes[-1]["texto"] += linha.strip() + " "
for s in secoes: print(s)'''),

    # ---------------- 2. Chunking ----------------
    (2, "Context window limits", "Quantos tokens cabem?",
     "Conte os tokens de cada documento da base com `contar_tokens` e o total. Se o limite de contexto fosse de 300 tokens, "
     "a base inteira caberia num único *prompt*?",
     '''tok = {d["id"]: contar_tokens(d["texto"]) for d in DOCS}
print(tok, "total:", sum(tok.values()), "-> cabe" if sum(tok.values()) <= 300 else "-> não cabe")'''),
    (2, "Different chunking strategies", "Três estratégias de chunking",
     "Junte todos os textos e divida de três jeitos: (a) tamanho fixo de 200 caracteres com sobreposição de 40; "
     "(b) por frases, agrupando até 200 caracteres; (c) recursivo, tentando separar por `\\n\\n`, depois `. `, depois espaço. "
     "Compare quantos pedaços cada um gera e se algum corta palavras.",
     '''texto = "\\n\\n".join(d["texto"] for d in DOCS)
def fixo(t, tam=200, sobre=40): return [t[i:i + tam] for i in range(0, len(t), tam - sobre)]
def por_frases(t, tam=200):
    pedacos, atual = [], ""
    for f in re.split(r"(?<=[.!?])\\s+", t):
        if len(atual) + len(f) > tam and atual: pedacos.append(atual.strip()); atual = ""
        atual += f + " "
    return pedacos + [atual.strip()] if atual.strip() else pedacos
def recursivo(t, tam=200, seps=("\\n\\n", ". ", " ")):
    if len(t) <= tam or not seps: return [t]
    partes, saida, atual = t.split(seps[0]), [], ""
    for p in partes:
        cand = (atual + seps[0] + p) if atual else p
        if len(cand) <= tam: atual = cand
        else:
            if atual: saida.append(atual)
            atual = p if len(p) <= tam else ""
            if len(p) > tam: saida += recursivo(p, tam, seps[1:])
    return saida + ([atual] if atual else [])
for nome, f in [("fixo", fixo), ("frases", por_frases), ("recursivo", recursivo)]:
    ps = f(texto); print(nome, len(ps), "pedaços | começa no meio de palavra:", sum(1 for p in ps[1:] if p[:1].isalnum() and p[:1].islower()))'''),
    (2, "Advanced indexing techniques", "Indexar o resumo, devolver o documento",
     "Para cada documento, peça ao modelo um resumo de uma frase. Indexe os **resumos** (busca por palavras), mas devolva o "
     "**texto completo** do documento encontrado (ideia de *multi-vector / summary index*). Teste com \"posso levar meu cachorro?\".",
     '''resumos = {d["id"]: perguntar(f"Resuma em uma frase curta, em português:\\n{d['texto']}") for d in DOCS}
def busca_palavras(q, textos):
    qs = set(re.findall(r"\\w+", q.lower()))
    return max(textos, key=lambda k: len(qs & set(re.findall(r"\\w+", textos[k].lower()))))
achado = busca_palavras("posso levar meu cachorro na biblioteca?", resumos)
print(resumos[achado]); print("->", next(d["texto"] for d in DOCS if d["id"] == achado))'''),
    (2, "Workflow of HyDE", "HyDE: buscar com uma resposta hipotética",
     "Implemente HyDE: peça ao modelo uma resposta **hipotética** para \"quanto pago se atrasar um livro?\", gere o embedding "
     "dessa resposta e use para buscar o documento mais parecido. Compare com buscar pelo embedding da própria pergunta.",
     '''q = "quanto pago se atrasar um livro?"
E_docs = embeddings([d["texto"] for d in DOCS])
hipotese = perguntar(f"Escreva um parágrafo curto que responderia: {q}")
for nome, v in [("pergunta", embeddings(q)[0]), ("HyDE", embeddings(hipotese)[0])]:
    s = similaridade(E_docs, v); i = int(np.argmax(s)); print(nome, DOCS[i]["titulo"], round(float(s[i]), 3))'''),

    # ---------------- 3. Embeddings ----------------
    (3, "Measuring similarity", "Cosseno, produto escalar e distância",
     "Para dois vetores de exemplo, calcule similaridade de cosseno, produto escalar e distância euclidiana. Depois "
     "normalize os vetores e mostre que o produto escalar passa a ser igual ao cosseno.",
     '''a, b = np.array([3.0, 1.0, 2.0]), np.array([1.0, 0.5, 4.0])
cos = a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
print(round(cos, 4), a @ b, round(np.linalg.norm(a - b), 4))
an, bn = a / np.linalg.norm(a), b / np.linalg.norm(b); print(round(an @ bn, 4))'''),
    (3, "Modern embedding models", "Busca semântica com embeddings",
     "Gere os embeddings dos 12 documentos com `embeddings()` e, para 3 perguntas escritas com palavras **diferentes** das "
     "do texto (ex.: \"tem internet sem fio?\"), mostre o documento mais similar.",
     '''E = embeddings([d["titulo"] + ". " + d["texto"] for d in DOCS])
for q in ["tem internet sem fio?", "posso ir com meu cão-guia?", "até que horas fica aberta no domingo?"]:
    s = similaridade(E, embeddings(q)[0]); print(q, "->", DOCS[int(np.argmax(s))]["titulo"])'''),
    (3, "Sparse embedding", "BM25 (esparso) × TF-IDF",
     "Indexe os documentos com `rank_bm25.BM25Okapi` e com TF-IDF do scikit-learn (cosseno). Para \"multa atraso bloqueio\", "
     "mostre o top-3 de cada um.",
     '''from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
toks = [re.findall(r"\\w+", d["texto"].lower()) for d in DOCS]
q = "multa atraso bloqueio"
bm = BM25Okapi(toks).get_scores(q.split())
vec = TfidfVectorizer(); M = vec.fit_transform(d["texto"] for d in DOCS)
tf = (M @ vec.transform([q]).T).toarray().ravel()
for nome, s in [("BM25", bm), ("TF-IDF", tf)]:
    print(nome, [DOCS[i]["titulo"] for i in np.argsort(-s)[:3]])'''),

    # ---------------- 4. Armazenamento vetorial ----------------
    (4, "How are vectors stored", "Um banco vetorial mínimo",
     "Escreva a classe `BancoVetorial` com `adicionar(id, vetor, metadados)`, `buscar(vetor, k, filtro=None)` e `remover(id)`, "
     "guardando os vetores normalizados numa matriz NumPy. Teste com vetores TF-IDF dos documentos (sem precisar do modelo).",
     '''from sklearn.feature_extraction.text import TfidfVectorizer
class BancoVetorial:
    def __init__(self): self.ids, self.meta, self.M = [], [], None
    def adicionar(self, id_, v, meta):
        v = v / np.linalg.norm(v); self.ids.append(id_); self.meta.append(meta)
        self.M = v[None, :] if self.M is None else np.vstack([self.M, v])
    def remover(self, id_):
        i = self.ids.index(id_); self.ids.pop(i); self.meta.pop(i); self.M = np.delete(self.M, i, axis=0)
    def buscar(self, v, k=3, filtro=None):
        s = self.M @ (v / np.linalg.norm(v))
        ordem = [i for i in np.argsort(-s) if filtro is None or filtro(self.meta[i])]
        return [(self.ids[i], round(float(s[i]), 3)) for i in ordem[:k]]
vec = TfidfVectorizer().fit([d["texto"] for d in DOCS])
banco = BancoVetorial()
for d in DOCS: banco.adicionar(d["id"], vec.transform([d["texto"]]).toarray()[0], {"data": d["data"]})
q = vec.transform(["multa por atraso"]).toarray()[0]
print(banco.buscar(q)); print(banco.buscar(q, filtro=lambda m: m["data"] >= "2025")); banco.remover("d05"); print(banco.buscar(q))'''),
    (4, "Indexing in vector databases", "Índice IVF: buscar só nos grupos próximos",
     "Gere 20.000 vetores aleatórios de dimensão 64. Agrupe com k-médias (100 grupos) e, para uma consulta, procure só "
     "nos 5 grupos mais próximos (ideia do IVF). Compare tempo e *recall@10* com a busca exata.",
     '''import time
from sklearn.cluster import KMeans
rng = np.random.default_rng(0)
X = rng.normal(size=(20_000, 64)).astype("float32"); q = rng.normal(size=64).astype("float32")
km = KMeans(100, n_init=1, random_state=0).fit(X)
t = time.perf_counter(); exato = np.argsort(np.linalg.norm(X - q, axis=1))[:10]; t_exato = time.perf_counter() - t
t = time.perf_counter()
grupos = np.argsort(np.linalg.norm(km.cluster_centers_ - q, axis=1))[:5]
cand = np.where(np.isin(km.labels_, grupos))[0]
aprox = cand[np.argsort(np.linalg.norm(X[cand] - q, axis=1))[:10]]; t_ivf = time.perf_counter() - t
print(f"candidatos {len(cand)} | recall@10 {len(set(exato) & set(aprox)) / 10:.1f} | exato {t_exato*1000:.1f} ms | IVF {t_ivf*1000:.1f} ms")'''),
    (4, "Vector retrieval", "Métrica certa para o vetor certo",
     "Mostre com um exemplo que, para vetores **não normalizados**, o ranking por produto escalar pode diferir do ranking "
     "por cosseno (um vetor longo \"ganha\" só por ser grande).",
     '''q = np.array([1.0, 0.0])
docs = {"curto_alinhado": np.array([1.0, 0.1]), "longo_desalinhado": np.array([5.0, 4.0])}
for nome, v in docs.items():
    print(nome, "produto:", round(q @ v, 2), "cosseno:", round(q @ v / np.linalg.norm(v), 3))'''),
    (4, "Data maintenance", "Atualizar documentos sem duplicar",
     "Implemente um *upsert*: ao reindexar, se o `id` já existe e o texto mudou (compare um hash `hashlib.sha256`), "
     "substitua; se não mudou, ignore. Mostre o relatório de inseridos, atualizados e ignorados.",
     '''import hashlib
indice = {}
def upsert(docs):
    rel = {"inseridos": 0, "atualizados": 0, "ignorados": 0}
    for d in docs:
        h = hashlib.sha256(d["texto"].encode()).hexdigest()
        if d["id"] not in indice: rel["inseridos"] += 1
        elif indice[d["id"]] != h: rel["atualizados"] += 1
        else: rel["ignorados"] += 1; continue
        indice[d["id"]] = h
    return rel
print(upsert(DOCS))
novos = [dict(d) for d in DOCS]; novos[2]["texto"] += " Agora também pelo aplicativo."
print(upsert(novos))'''),

    # ---------------- 5. Pré-recuperação ----------------
    (5, "Text-to-SQL", "Pergunta em português vira SQL",
     "Crie no `sqlite3` a tabela `emprestimos(leitor, livro, data_saida, devolvido)` com algumas linhas. Peça ao modelo o "
     "SQL para \"quantos livros ainda não foram devolvidos?\" (passe o esquema no *prompt* e peça só o SQL), execute e mostre.",
     '''import sqlite3
con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE emprestimos (leitor TEXT, livro TEXT, data_saida TEXT, devolvido INTEGER)")
con.executemany("INSERT INTO emprestimos VALUES (?,?,?,?)", [("ana", "Dom Casmurro", "2025-05-01", 1), ("bia", "Vidas Secas", "2025-05-03", 0),
    ("caio", "O Cortiço", "2025-05-04", 0), ("ana", "Iracema", "2025-05-10", 0)])
esquema = "emprestimos(leitor TEXT, livro TEXT, data_saida TEXT, devolvido INTEGER 0/1)"
sql = perguntar(f"Esquema SQLite: {esquema}\\nEscreva só o SQL, sem explicação e sem ```, para: quantos livros ainda não foram devolvidos?")
sql = sql.strip().strip("`").removeprefix("sql").strip()
print(sql); print(con.execute(sql).fetchall())'''),
    (5, "Self-query retriever", "O modelo cria o filtro de metadados",
     "Peça ao modelo para transformar \"regras de multa atualizadas em 2025\" num JSON `{\"consulta\": ..., \"data_minima\": ...}`. "
     "Aplique o filtro de data nos `DOCS` e faça a busca por palavras só nos que passaram.",
     '''pedido = "regras de multa atualizadas em 2025"
resp = perguntar(f'Converta em JSON com as chaves "consulta" (palavras-chave) e "data_minima" (AAAA-MM-DD ou null). Só o JSON.\\nPedido: {pedido}',
                 response_format={"type": "json_object"})
f = json.loads(resp); print(f)
cands = [d for d in DOCS if not f.get("data_minima") or d["data"] >= f["data_minima"]]
qs = set(re.findall(r"\\w+", f["consulta"].lower()))
print(max(cands, key=lambda d: len(qs & set(re.findall(r"\\w+", d["texto"].lower()))))["titulo"])'''),
    (5, "Query translation", "Reescrita de consulta e multi-query",
     "Para a pergunta vaga \"e se eu esquecer de devolver?\", peça ao modelo 3 reformulações diferentes. Busque com cada uma "
     "(BM25) e junte os resultados sem repetição.",
     '''from rank_bm25 import BM25Okapi
bm = BM25Okapi([re.findall(r"\\w+", d["texto"].lower()) for d in DOCS])
vars_ = perguntar("Reescreva de 3 formas diferentes, uma por linha, sem numerar: e se eu esquecer de devolver o livro da biblioteca?").splitlines()
achados = []
for v in [x for x in vars_ if x.strip()]:
    i = int(np.argmax(bm.get_scores(re.findall(r"\\w+", v.lower()))))
    if DOCS[i]["titulo"] not in achados: achados.append(DOCS[i]["titulo"])
print(vars_); print(achados)'''),
    (5, "Query routing", "Roteador de consultas",
     "Peça ao modelo para classificar cada pergunta em `\"sql\"` (dados de empréstimos), `\"documentos\"` (regras da biblioteca) "
     "ou `\"conversa\"` (cumprimentos), respondendo só com a palavra. Teste com 3 perguntas.",
     '''def rotear(q):
    r = perguntar(f'Classifique em sql, documentos ou conversa. Responda só a palavra.\\n- sql: números sobre empréstimos\\n- documentos: regras e serviços da biblioteca\\n- conversa: cumprimentos\\nPergunta: {q}', temperature=0)
    return r.strip().lower().strip(".")
for q in ["quantos empréstimos a Ana fez?", "a sala de estudos tem tomada?", "oi, tudo bem?"]:
    print(q, "->", rotear(q))'''),

    # ---------------- 6. Otimização de índices ----------------
    (6, "From small to large", "Indexar frases, devolver a janela",
     "Divida todos os textos em frases, indexe cada frase (BM25) e, ao encontrar a melhor frase, devolva também a frase "
     "anterior e a seguinte do mesmo documento (*sentence window*).",
     '''from rank_bm25 import BM25Okapi
frases = [(d["id"], i, f) for d in DOCS for i, f in enumerate(re.split(r"(?<=\\.)\\s+", d["texto"]))]
bm = BM25Okapi([re.findall(r"\\w+", f.lower()) for _, _, f in frases])
k = int(np.argmax(bm.get_scores("garrafa de água".split())))
doc, i, _ = frases[k]
janela = [f for d, j, f in frases if d == doc and abs(j - i) <= 1]
print(" ".join(janela))'''),
    (6, "Hybrid retrieval", "Busca híbrida com RRF",
     "Combine o ranking do BM25 com o ranking semântico (embeddings) usando *Reciprocal Rank Fusion*: "
     "score = Σ 1/(60 + posição). Mostre o top-3 de cada método e o fundido para \"onde estudar com notebook?\".",
     '''from rank_bm25 import BM25Okapi
q = "onde estudar com notebook?"
bm = BM25Okapi([re.findall(r"\\w+", d["texto"].lower()) for d in DOCS]).get_scores(re.findall(r"\\w+", q.lower()))
sem = similaridade(embeddings([d["texto"] for d in DOCS]), embeddings(q)[0])
rk = {nome: list(np.argsort(-s)) for nome, s in [("bm25", bm), ("semantico", sem)]}
rrf = {i: sum(1 / (60 + r.index(i) + 1) for r in rk.values()) for i in range(len(DOCS))}
for nome, r in rk.items(): print(nome, [DOCS[i]["titulo"] for i in r[:3]])
print("RRF", [DOCS[i]["titulo"] for i in sorted(rrf, key=rrf.get, reverse=True)[:3]])'''),

    # ---------------- 7. Pós-recuperação ----------------
    (7, "Common retrieval post-processing", "Reordenar com MMR (diversidade)",
     "Implemente *Maximal Marginal Relevance*: escolha k = 3 documentos equilibrando relevância para a consulta e "
     "diferença em relação aos já escolhidos (λ = 0,5). Use vetores TF-IDF para rodar sem o modelo.",
     '''from sklearn.feature_extraction.text import TfidfVectorizer
vec = TfidfVectorizer().fit([d["texto"] for d in DOCS])
D = vec.transform([d["texto"] for d in DOCS]).toarray(); q = vec.transform(["multa atraso livro"]).toarray()[0]
def cos(a, b): return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
def mmr(q, D, k=3, lam=0.5):
    escolhidos, resto = [], list(range(len(D)))
    while len(escolhidos) < k:
        melhor = max(resto, key=lambda i: lam * cos(q, D[i]) - (1 - lam) * max([cos(D[i], D[j]) for j in escolhidos], default=0))
        escolhidos.append(melhor); resto.remove(melhor)
    return escolhidos
print("só relevância:", [DOCS[i]["id"] for i in np.argsort([-cos(q, d) for d in D])[:3]])
print("MMR:", [DOCS[i]["id"] for i in mmr(q, D)])'''),
    (7, "Difference between LangChain", "Peso por recência",
     "Os documentos d04 e d05 falam de multa, mas d05 é a versão antiga. Combine similaridade (TF-IDF) com um peso de "
     "recência `0,99 ** dias_desde_atualizacao/30` e mostre que d04 passa à frente.",
     '''from datetime import date
from sklearn.feature_extraction.text import TfidfVectorizer
vec = TfidfVectorizer().fit([d["texto"] for d in DOCS])
q = vec.transform(["multa por atraso"]).toarray()[0]
hoje = date(2025, 6, 1)
for d in DOCS:
    if d["id"] in ("d04", "d05"):
        v = vec.transform([d["texto"]]).toarray()[0]; sim = float(v @ q / (np.linalg.norm(v) * np.linalg.norm(q)))
        dias = (hoje - date.fromisoformat(d["data"])).days
        print(d["id"], round(sim, 3), round(sim * 0.99 ** (dias / 30), 3))'''),
    (7, "Compression", "Comprimir o contexto",
     "Peça ao modelo para extrair, de cada um dos 3 documentos recuperados, **só as frases** relevantes para a pergunta "
     "\"quantos livros posso pegar e por quanto tempo?\". Compare os tokens antes e depois.",
     '''q = "quantos livros posso pegar e por quanto tempo?"
recuperados = [DOCS[2], DOCS[3], DOCS[6]]
comprimido = [perguntar(f"Copie apenas as frases que ajudam a responder '{q}'. Se nenhuma ajudar, responda NADA.\\n\\n{d['texto']}") for d in recuperados]
antes = sum(contar_tokens(d["texto"]) for d in recuperados); depois = sum(contar_tokens(c) for c in comprimido if c.strip() != "NADA")
print(comprimido); print(antes, "->", depois, "tokens")'''),
    (7, "Correction", "Avaliar a recuperação antes de responder",
     "Implemente um passo de correção (ideia do CRAG): para cada documento recuperado, peça ao modelo \"relevante\" ou "
     "\"irrelevante\"; se nenhum for relevante, responda \"não encontrei na base\" em vez de inventar.",
     '''def corrigir(q, docs):
    bons = [d for d in docs if "irrelevante" not in perguntar(f"O texto ajuda a responder '{q}'? Responda relevante ou irrelevante.\\n\\n{d['texto']}", temperature=0).lower()]
    return bons or None
for q in ["qual o preço da impressão colorida?", "a biblioteca vende café?"]:
    bons = corrigir(q, DOCS[9:12])
    print(q, "->", [d["titulo"] for d in bons] if bons else "não encontrei na base")'''),

    # ---------------- 8. Geração ----------------
    (8, "Improving LLM output", "Resposta com citações",
     "Monte o RAG completo: recupere os 3 documentos mais relevantes (BM25), coloque no *prompt* com `[id]` e instrua o "
     "modelo a responder **só** com base neles, citando os ids. Teste com uma pergunta respondível e uma que não está na base.",
     '''from rank_bm25 import BM25Okapi
bm = BM25Okapi([re.findall(r"\\w+", (d["titulo"] + " " + d["texto"]).lower()) for d in DOCS])
SISTEMA = "Você responde dúvidas da Biblioteca Aurora usando SÓ os trechos dados. Cite os ids entre colchetes. Se a resposta não estiver nos trechos, diga que não sabe."
def rag(q, k=3):
    top = np.argsort(-bm.get_scores(re.findall(r"\\w+", q.lower())))[:k]
    ctx = "\\n".join(f"[{DOCS[i]['id']}] {DOCS[i]['texto']}" for i in top)
    return perguntar(f"Trechos:\\n{ctx}\\n\\nPergunta: {q}", sistema=SISTEMA, temperature=0)
print(rag("Quanto custa imprimir 10 páginas coloridas?")); print(rag("A biblioteca tem estacionamento?"))'''),

    # ---------------- 9. Avaliação ----------------
    (9, "Evaluation system for RAG", "Métricas de recuperação: hit rate e MRR",
     "Monte um pequeno conjunto de avaliação (6 perguntas → id correto) e calcule *hit rate@3* e MRR do BM25. Sem modelo.",
     '''from rank_bm25 import BM25Okapi
bm = BM25Okapi([re.findall(r"\\w+", (d["titulo"] + " " + d["texto"]).lower()) for d in DOCS])
avaliacao = [("que dia a biblioteca fecha?", "d01"), ("preciso de comprovante de endereço?", "d02"), ("posso renovar o empréstimo?", "d03"),
             ("quanto é a multa por dia?", "d04"), ("tem livros em braile?", "d10"), ("aceitam revistas como doação?", "d09")]
hits, rr = 0, 0.0
for q, certo in avaliacao:
    ordem = [DOCS[i]["id"] for i in np.argsort(-bm.get_scores(re.findall(r"\\w+", q.lower())))]
    pos = ordem.index(certo) + 1; hits += pos <= 3; rr += 1 / pos
print(f"hit@3 = {hits / len(avaliacao):.2f} | MRR = {rr / len(avaliacao):.2f}")'''),
    (9, "Evaluation frameworks", "Fidelidade com modelo-juiz",
     "Para uma pergunta, gere a resposta do RAG e peça ao modelo forte (`MODELO_FORTE`) uma nota de 1 a 5 de **fidelidade** "
     "(a resposta só afirma o que está no contexto?) em JSON `{\"nota\": n, \"motivo\": \"...\"}`.",
     '''ctx = DOCS[3]["texto"]
resposta = perguntar(f"Contexto: {ctx}\\nPergunta: quanto custa atrasar 3 livros por 2 dias? Responda usando só o contexto.")
juiz = perguntar(f'Avalie a FIDELIDADE da resposta ao contexto (1 a 5). JSON {{"nota": n, "motivo": "..."}}.\\nContexto: {ctx}\\nResposta: {resposta}',
                 modelo=MODELO_FORTE, response_format={"type": "json_object"}, temperature=0)
print(resposta); print(json.loads(juiz))'''),

    # ---------------- 10. Paradigmas complexos ----------------
    (10, "Agentic RAG", "Agentic RAG: o modelo decide se busca",
     "Ofereça ao modelo uma ferramenta `buscar_documentos(consulta)` via *function calling*. Num laço, se ele pedir a ferramenta, "
     "execute a busca (BM25) e devolva o resultado; pare quando ele responder em texto. Teste com uma pergunta que exige "
     "duas buscas (\"quanto custa imprimir 5 páginas e em que dias posso doar livros?\").",
     '''from rank_bm25 import BM25Okapi
bm = BM25Okapi([re.findall(r"\\w+", (d["titulo"] + " " + d["texto"]).lower()) for d in DOCS])
def buscar_documentos(consulta):
    top = np.argsort(-bm.get_scores(re.findall(r"\\w+", consulta.lower())))[:2]
    return "\\n".join(f"[{DOCS[i]['id']}] {DOCS[i]['texto']}" for i in top)
ferramentas = [{"type": "function", "function": {"name": "buscar_documentos", "description": "Busca nas regras da Biblioteca Aurora",
    "parameters": {"type": "object", "properties": {"consulta": {"type": "string"}}, "required": ["consulta"]}}}]
msgs = [{"role": "system", "content": "Use a ferramenta para buscar antes de responder. Responda em português e cite os ids."},
        {"role": "user", "content": "Quanto custa imprimir 5 páginas em preto e branco e em que dias posso doar livros?"}]
for passo in range(5):
    r = conversar(msgs, tools=ferramentas).choices[0].message
    if not r.tool_calls:
        print(r.content); break
    msgs.append(r)
    for chamada in r.tool_calls:
        arg = json.loads(chamada.function.arguments); print("🔎", arg)
        msgs.append({"role": "tool", "tool_call_id": chamada.id, "content": buscar_documentos(**arg)})
print(gasto())'''),
]
