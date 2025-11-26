import osmnx as ox
import pandas as pd

# Example: get driving network for a city
G = ox.graph_from_place(
    "Somerville, Massachusetts, USA", retain_all=True, network_type="bike"
)

# Convert to GeoDataFrames (nodes + edges)
nodes, edges = ox.graph_to_gdfs(G)
