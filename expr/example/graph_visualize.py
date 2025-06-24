import networkx as nx
import matplotlib.pyplot as plt

# GraphML 파일 경로
graphml_file = "/Users/junokim/Desktop/jupyteryong/26th-conference-Legent/expr/example/graph_chunk_entity_relation.graphml"

# 그래프 로딩
G = nx.read_graphml(graphml_file)

# 노드 라벨 설정 (노드 id를 그대로 표시하거나 description이 있으면 그걸 사용)
node_labels = {}
for node_id, data in G.nodes(data=True):
    label = data.get("description", node_id)  # description이 없으면 id로
    # 긴 라벨 줄바꿈 처리
    node_labels[node_id] = "\n".join([label[i:i+30] for i in range(0, len(label), 30)])

# 시각화 레이아웃
pos = nx.spring_layout(G, k=0.3, seed=42)  # k는 간격 조정, seed는 레이아웃 고정

# 그래프 그리기
plt.figure(figsize=(24, 18))  # 크기 조정

nx.draw_networkx_nodes(G, pos, node_size=800, node_color='skyblue', alpha=0.8)
nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.5)
nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)

# 옵션 설정
plt.title("Graph Visualization from GraphML", fontsize=20)
plt.axis("off")

# 👉 파일로 저장
plt.savefig("graph_visualization.png", dpi=300, bbox_inches='tight')
plt.close()