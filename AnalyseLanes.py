import pandas as pd
import numpy as np
from pathlib import Path
import igraph as ig
import textwrap

BASE = Path(__file__).parent
DATA = BASE / "data" / "DataSet.txt"
OUTPUT = BASE / "output"
PLOTS = BASE / "plots"

# Quando rodamos o projeto, os arquivos txt gerados serão salvos na pasta OUTPUT
for d in (OUTPUT,):
    d.mkdir(parents=True, exist_ok=True)

# usando o contexto do DataSet criado a partir de uma enquente do whatsapp no grupo da sala
lines = [ln.strip() for ln in DATA.read_text(encoding="utf-8").splitlines() if ln.strip()]
# Cabeçalhos previstos para padronização
lane_headers = ["MID", "Top", "Jg", "Sup", "ADC"]

dataset = {}
current = None
for ln in lines:
    if ln in lane_headers:
        current = ln
        dataset[current] = []
    else:
        if current is not None:
            dataset[current].append(ln)

students = sorted({name for names in dataset.values() for name in names})
lanes = lane_headers

# Aqui ocorre a geraçao da matriz de incidencia, onde cada lane escolhida terá o valor 1 e 0 para a que não escolheu. Aluno X Lane
incidence = pd.DataFrame(0, index=students, columns=lanes, dtype=int)
for lane, names in dataset.items():
    for name in names:
        incidence.at[name, lane] = 1

# As saídas são salva em txt
(OUTPUT/"incidence_matrix.txt").write_text(incidence.to_string(), encoding="utf-8")

# Aqui a geraçao a matriz de similaridade, definindo maior peso em suas escolhas de acordo com o valor (mais proximo de 1 = mais peso). Aluno X Aluno
def jaccard(a,b):
    a = np.array(a, dtype=bool)
    b = np.array(b, dtype=bool)
    inter = np.logical_and(a,b).sum()
    union = np.logical_or(a,b).sum()
    return inter/union if union>0 else 0.0

sim = pd.DataFrame(0.0, index=students, columns=students)
for i,s1 in enumerate(students):
    for j,s2 in enumerate(students):
        if j>=i:
            v = jaccard(incidence.loc[s1].values, incidence.loc[s2].values)
            sim.at[s1,s2] = v
            sim.at[s2,s1] = v

# Novamente salvando em TXT mas dessa vez a de similaridade
(OUTPUT/"student_similarity_jaccard.txt").write_text(sim.round(3).to_string(), encoding="utf-8")

# Matriz de coocorrencia, sendo que o valor 0 na matriz diz que ngm joga as duas lanes ao mesmo tempo. Demais valores indicam a qtd de alunos que marcaram a mesma opção de rota. Lane x Lane
cooc = pd.DataFrame(0, index=lanes, columns=lanes, dtype=int)
for i,l1 in enumerate(lanes):
    for j,l2 in enumerate(lanes):
        if j>=i:
            cnt = int(((incidence[l1] & incidence[l2]).sum()))
            cooc.at[l1,l2] = cnt
            cooc.at[l2,l1] = cnt

# Salvando em txt a matriz de coocorrencia
(OUTPUT/"lane_cooccurrence.txt").write_text(cooc.to_string(), encoding="utf-8")

# Criaçao dos grafos, usamos a biblioteca igraph 
labels = students + lanes
g_bip = ig.Graph()
g_bip.add_vertices(len(labels))
g_bip.vs["name"] = labels
g_bip.vs["type"] = [True]*len(students) + [False]*len(lanes)
edges = []
for s in students:
    for l in lanes:
        if incidence.at[s,l]==1:
            edges.append((labels.index(s), labels.index(l)))
g_bip.add_edges(edges)

# Grafo de similaridade dos estudantes, ponderado
g_sim = ig.Graph()
g_sim.add_vertices(len(students))
g_sim.vs["name"] = students
sim_edges = []
weights = []
for i,s1 in enumerate(students):
    for j,s2 in enumerate(students):
        if j>i and sim.at[s1,s2] > 0:
            sim_edges.append((i,j))
            weights.append(float(sim.at[s1,s2]))
g_sim.add_edges(sim_edges)
g_sim.es["weight"] = weights

# Grafo de co-ocorrencia das lanes, ponderado
g_co = ig.Graph()
g_co.add_vertices(len(lanes))
g_co.vs["name"] = lanes
co_edges = []
co_weights = []
for i,l1 in enumerate(lanes):
    for j,l2 in enumerate(lanes):
        if j>i and cooc.at[l1,l2] > 0:
            co_edges.append((i,j))
            co_weights.append(int(cooc.at[l1,l2]))
g_co.add_edges(co_edges)
g_co.es["weight"] = co_weights

# Cálculo das metricas (analisar os vertices de acordo com o peso, quantidade de vertices vizinhos etc)
def compute_metrics(g, weight_attr=None):
    df = pd.DataFrame(index=g.vs["name"])
    df["degree"] = g.degree()
    if g.ecount()>0 and weight_attr:
        df["strength"] = g.strength(weights=g.es[weight_attr])
    else:
        df["strength"] = df["degree"]
    if g.ecount()>0 and weight_attr:
        distances = [1.0/w if w>0 else 1.0 for w in g.es[weight_attr]]
        # Quantas vezes um vertice aparece no "caminho mais curto" entre outros dois vértices.
        df["betweenness"] = g.betweenness(weights=distances)
        # O quao perto um vertice está de todos os outros do grafo.
        df["closeness"] = g.closeness(weights=distances)
    else:
        df["betweenness"] = g.betweenness()
        df["closeness"] = g.closeness()
    # O quao importante o vertice é, considerando também a importância dos vizinhos.    
    df["eigenvector"] = g.eigenvector_centrality(weights=(g.es[weight_attr] if weight_attr and g.ecount()>0 else None))
    # O quanto os vizinhos de um vertice também são vizinhos entre si.
    df["clustering"] = g.transitivity_local_undirected(mode="zero")
    return df

df_sim_metrics = compute_metrics(g_sim, weight_attr="weight") if g_sim.ecount()>0 else compute_metrics(g_sim)
df_co_metrics = compute_metrics(g_co, weight_attr="weight") if g_co.ecount()>0 else compute_metrics(g_co)


(OUTPUT/"student_similarity_metrics.txt").write_text(df_sim_metrics.round(3).to_string(), encoding="utf-8")
(OUTPUT/"lane_cooccurrence_metrics.txt").write_text(df_co_metrics.round(3).to_string(), encoding="utf-8")
print("Iniciando a geração dos gráficos visuais")

# Confirmando que a pasta plots existe - local onde serão salvos os grafos
PLOTS.mkdir(parents=True, exist_ok=True)

# Grafo Bipartido (Alunos e Lanes), já definindo cores diferentes para Alunos (True) e Lanes (False) e ajustando as cores conforme preferência (ex: "lightblue", "salmon")
color_dict = {True: "#ADD8E6", False: "#FA8072"} 
g_bip.vs["color"] = [color_dict[v_type] for v_type in g_bip.vs["type"]]

# Labels e formas
g_bip.vs["label"] = g_bip.vs["name"]
g_bip.vs["shape"] = ["circle" if v_type else "square" for v_type in g_bip.vs["type"]]

# Buildando o grafo
out_bip = PLOTS / "BipGraph.png"
ig.plot(
    g_bip,
    target=str(out_bip),
    layout=g_bip.layout_bipartite(),
    bbox=(1000, 600),
    vertex_size=30,
    vertex_label_size=12,
    edge_color="gray",
    edge_width=0.5,
    margin=50
)
print(f"Grafo bipartido salvo em: {out_bip}")


# Grafo de Similaridade (Alunos), apenas arestas com peso > 0 existem neste grafo
g_sim.vs["label"] = g_sim.vs["name"]
g_sim.vs["color"] = "#ADD8E6"  # Azul claro para alunos

# Aqui fazemos um ajuste na espessura da aresta baseado na similaridade (peso) e dps multiplicamos por um fator para tornar a variaçao visivel
if g_sim.ecount() > 0:
    g_sim.es["width"] = [w * 3 for w in g_sim.es["weight"]]

out_sim = PLOTS / "StudentSimGraph.png"
ig.plot(
    g_sim,
    target=str(out_sim),
    layout="kk",  # Algoritmo Kamada-Kawai, recomendada para organizar clusters
    bbox=(800, 800),
    vertex_size=35,
    vertex_label_size=12,
    edge_curved=0.1,
    margin=50
)
print(f"Grafo de similaridade salvo em: {out_sim}")


# Plot do Grafo de coocorrencia - Lanes
g_co.vs["label"] = g_co.vs["name"]
g_co.vs["color"] = "#FA8072"  # Salmao para lanes

# Espessura baseada na contagem de coocorrencias
if g_co.ecount() > 0:
    # Normalização simples ou uso direto do peso
    g_co.es["width"] = [w for w in g_co.es["weight"]]
    # Adiciona o número de coocorrências como label na aresta
    g_co.es["label"] = [str(int(w)) for w in g_co.es["weight"]]

out_co = PLOTS / "LaneCoocGraph.png"
ig.plot(
    g_co,
    target=str(out_co),
    layout="circle",  # Layout circular é ideal para poucas categorias interconectadas
    bbox=(600, 600),
    vertex_size=45,
    vertex_label_size=14,
    edge_label_size=10,
    margin=50
)
print(f"Grafo de coocorrência salvo em: {out_co}")
