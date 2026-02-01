# 📐 Logarithma

> *Next-generation graph algorithms for computational optimization*

[![PyPI version](https://badge.fury.io/py/logarithma.svg)](https://badge.fury.io/py/logarithma)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Logarithma** is a high-performance Python library for graph algorithms. Our goal is to implement the groundbreaking **O(m + n log log n)** shortest path algorithm (Thorup's SSSP), breaking the classical Dijkstra's O(m + n log n) sorting barrier.

## ✨ Features

### Current (v0.1.0)
- ✅ **Dijkstra's Algorithm**: Classic shortest path implementation
- ✅ **Path Reconstruction**: Get both distances and paths
- ✅ **NetworkX Integration**: Seamless integration with NetworkX graphs

### Coming Soon (v0.2.0 - v0.5.0)
- 🔄 **A* Algorithm**: Heuristic-based pathfinding
- 🔄 **BFS/DFS**: Graph traversal algorithms
- 🔄 **Bellman-Ford**: Support for negative weights
- 🔄 **MST Algorithms**: Kruskal and Prim
- 🔄 **Visualization**: Interactive graph visualization
- 🔄 **Utils**: Graph generators, validators, converters
- 🎯 **Thorup SSSP**: O(m + n log log n) - Breaking the sorting barrier!

## 🚀 Installation

```bash
pip install logarithma
```

## 🎯 Quick Start

### Basic Dijkstra Usage

```python
import logarithma as lg
import networkx as nx

# Create a graph
G = nx.Graph()
G.add_edge('A', 'B', weight=4)
G.add_edge('A', 'C', weight=2)
G.add_edge('B', 'C', weight=1)
G.add_edge('B', 'D', weight=5)
G.add_edge('C', 'D', weight=8)

# Find shortest distances from A
distances = lg.dijkstra(G, 'A')
print(distances)
# Output: {'A': 0, 'C': 2, 'B': 3, 'D': 8}

# Get shortest path to a specific node
result = lg.dijkstra_with_path(G, 'A', 'D')
print(f"Distance to D: {result['distances']['D']}")
print(f"Path to D: {result['paths']['D']}")
# Output: Distance to D: 8
#         Path to D: ['A', 'C', 'B', 'D']
```

## 📚 Documentation

- **[Development Plan](DEVELOPMENT.md)**: Comprehensive roadmap and vision
- **[Algorithm Roadmap](docs/ALGORITHM_ROADMAP.md)**: Detailed algorithm specifications
- **[Project Structure](docs/PROJECT_STRUCTURE.md)**: Codebase organization
- **[Breaking Barrier Research](docs/breaking_barrier_research.md)**: 2025 paper analysis and implementation plan
- **[Paper Summary](docs/MAKALE_OZET.md)**: Guide to studying the 2025 paper

## 🗺️ Roadmap

### Phase 1: Core Algorithms (v0.2.0) - March 2026
- A* pathfinding algorithm
- BFS/DFS traversal
- Bellman-Ford for negative weights
- Utils module (generators, validators)
- Basic visualization

### Phase 2: Advanced Algorithms (v0.3.0-v0.4.0) - April-May 2026
- Minimum Spanning Tree (Kruskal, Prim)
- Network Flow algorithms
- All-pairs shortest path
- Graph properties (SCC, topological sort)

### Phase 3: Breaking the Sorting Barrier (v0.5.0) - June-July 2026 🎯
- **Breaking the Sorting Barrier** algorithm (Duan et al., 2025)
- Advanced data structures for directed graphs
- Surpassing Dijkstra's O(m + n log n) bound
- Implementation of cutting-edge 2025 research!

### Phase 4: Optimization (v0.6.0) - August 2026
- Cython optimizations
- Parallel processing
- Memory optimizations

### Phase 5: Applications (v0.7.0+) - September 2026
- Domain-specific modules (logistics, finance, social networks)
- Real-world examples
- Production-ready v1.0.0

## 🎓 Algorithm Complexity Comparison

| Algorithm | Time Complexity | Space | Use Case |
|-----------|----------------|-------|----------|
| Dijkstra | O(m + n log n) | O(n) | General SSSP, non-negative weights |
| A* | O(b^d)* | O(n) | Pathfinding with heuristics |
| Bellman-Ford | O(mn) | O(n) | Negative weights, cycle detection |
| **Breaking Barrier (2025)** | **[Makaleye göre]** | **O(n)** | **Directed graphs, breaks sorting barrier** |

*Practical performance is much better with good heuristics

## 💡 Use Cases

### Logistics & Transportation
- Route optimization
- Delivery planning
- Traffic network analysis

### Social Networks
- Influence analysis
- Community detection
- Recommendation systems

### Finance
- Arbitrage detection
- Risk analysis
- Portfolio optimization

### Telecommunications
- Network routing
- Bandwidth optimization
- Fault tolerance

## 🤝 Contributing

We welcome contributions! See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Contribution workflow

## 📊 Performance

Logarithma is designed for both correctness and performance:

- ✅ **Correctness**: Rigorous testing against known algorithms
- ⚡ **Speed**: Optimized implementations with Cython
- 📈 **Scalability**: Efficient for graphs with millions of nodes
- 💾 **Memory**: O(n) space complexity for most algorithms

## 🔬 Research

Logarithma is built on cutting-edge research:

- **Duan, R., Mao, J., Mao, X., Shu, X., Yin, L. (2025)**: "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths" - arXiv:2504.17033v2 🎯 **PRIMARY FOCUS**
- **Dijkstra, E. W. (1959)**: "A note on two problems in connexion with graphs"
- **Hart, P. E., et al. (1968)**: "A Formal Basis for the Heuristic Determination of Minimum Cost Paths"
- **Thorup, M. (2004)**: "Integer priority queues with decrease key in constant time" (Related work)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📧 Contact

- **Author**: Can AKYILDIRIM
- **Email**: akyildirimcan@gmail.com
- **GitHub**: [softdevcan/logarithma](https://github.com/softdevcan/logarithma)

## 🌟 Star History

If you find Logarithma useful, please consider giving it a star on GitHub!

---

**Status**: 🚀 Active Development  
**Current Version**: 0.1.0  
**Next Release**: 0.2.0 (March 2026)
