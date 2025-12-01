# Análise de Preferência de Lanes no League of Legends
# Intergrantes: Igor Ramos, Guilherme Vicente, Isaque Castro, Gabriel Forconi, João Pedro Messias

Nesse trabalho conseguimos identificar:

* A relação entre alunos e lanes (matriz de incidência)
* Quais alunos têm perfis de escolha semelhantes (Jaccard)
* Quais lanes aparecem juntas com mais frequência (coocorrência)
* Métricas de redes que mostram centralidade e estrutura dos grafos

# Estrutura do projeto

O script principal `AnalyseLanes.py` processa os dados de entrada e gera os arquivos de saída na pasta output/.

```
MATTRAB/
│
├── data/
│   └── DataSet.txt 
│
├── output/
│   ├── incidence_matrix.txt
│   ├── student_similarity_jaccard.txt 
│   ├── lane_cooccurrence.txt 
│   ├── student_similarity_metrics.txt 
│   ├── lane_cooccurrence_metrics.txt 
│
├── plots/  
│   ├── grafo_bipartido.png
│   ├── grafo_similaridade_alunos.png
│   └── grafo_coocorrencia_lanes.png
│   
├── AnalyseLanes.py 
│
└── README.md
```

## Como rodar

1. Instale as dependências com o comando: `pip install pandas numpy python-igraph`
2. Verifique que o arquivo `DataSet.txt` está dentro da pasta `data/`.
3. Execute o script: `python AnalyseLanes.py`
4. Os resultados serão gerados automaticamente na pasta:

* output para tabelas representando as matrizes.

## Assim que for rodado serão criados (em formato TXT):

1.  **`incidence_matrix.txt`**: Matriz de Incidência (Aluno × Lane) - Mostra quais lanes cada aluno escolheu.
2.  **`student_similarity_jaccard.txt`**: Matriz de Similaridade (Jaccard) - Indica o quanto as escolhas entre dois alunos se parecem.
3.  **`lane_cooccurrence.txt`**: Matriz de Coocorrência de Lanes - Conta quantos alunos escolheram duas lanes ao mesmo tempo.
4.  **Métricas de Redes** (em dois arquivos): Para alunos (grafo de similaridade) e lanes (grafo de coocorrência): Degree, Strength, Betweenness, Closeness, Eigenvector, Clustering.

## Visualização dos Grafos (Pasta plots/)

5. O script utiliza a biblioteca igraph para gerar imagens PNG dos grafos.
6. grafo_bipartido.png: Visualização da relação direta entre Alunos e Lanes.
7. grafo_similaridade_alunos.png: Grafo ponderado onde a força da aresta representa a similaridade de Jaccard entre os alunos.
8. grafo_coocorrencia_lanes.png: Grafo ponderado onde a força da aresta (e o rótulo da aresta) representa a frequência com que duas Lanes foram escolhidas juntas.

## Análise rápida dos resultados
* Alunos com Jaccard alto têm perfis parecidos.
* Lanes com coocorrência alta costumam aparecer juntas entre as escolhas.
* Valores altos de eigenvector ou strength indicam influência estrutural no grafo.
* Betweenness alto revela alunos que conectam diferentes grupos.