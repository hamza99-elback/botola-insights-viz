import pandas as pd
import numpy as np
import json
import glob
from scipy.spatial import distance
import networkx as nx
import matplotlib.pyplot as plt
from mplsoccer import Pitch

# Step 1: Load all player data
def load_all_players(folder_path='./'):
    """
    Load all player JSON files and combine into one DataFrame
    """
    all_passes = []

    # Find all JSON files matching pattern (1.json, 2.json, etc.)
    json_files = sorted(glob.glob(f'{folder_path}/*.json'),
                       key=lambda x: int(x.split('/')[-1].split('.')[0]))

    for file_path in json_files:
        # Extract player number from filename
        player_id = file_path.split('/')[-1].split('.')[0]

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Extract only successful passes (outcome = true)
        successful_passes = [
            p for p in data.get('passes', [])
            if p.get('outcome') == True
        ]

        # Convert to DataFrame
        for pass_data in successful_passes:
            all_passes.append({
                'player_id': player_id,
                'start_x': pass_data['playerCoordinates']['x'],
                'start_y': pass_data['playerCoordinates']['y'],
                'end_x': pass_data['passEndCoordinates']['x'],
                'end_y': pass_data['passEndCoordinates']['y'],
                'is_long_ball': pass_data.get('isLongBall', False),
                'is_key_pass': pass_data.get('keypass', False)
            })

    return pd.DataFrame(all_passes)

# Step 2: Assign receivers based on proximity
def assign_receivers(df, max_distance=5):
    """
    For each pass, find which player was closest to the destination
    """
    df['receiver_id'] = None
    df['receiver_distance'] = None

    # Create a lookup of all player positions (where they make passes from)
    player_positions = df.groupby('player_id')[['start_x', 'start_y']].apply(
        lambda x: list(zip(x['start_x'], x['start_y']))
    ).to_dict()

    for idx, pass_row in df.iterrows():
        passer_id = pass_row['player_id']
        pass_end = (pass_row['end_x'], pass_row['end_y'])

        min_dist = float('inf')
        receiver = None

        # Check all other players' typical positions
        for other_player_id, positions in player_positions.items():
            if other_player_id == passer_id:
                continue

            # Check distance to all positions where this player makes passes
            for pos in positions:
                dist = distance.euclidean(pass_end, pos)

                if dist < min_dist:
                    min_dist = dist
                    receiver = other_player_id

        # Only assign if within reasonable distance
        if min_dist < max_distance:
            df.at[idx, 'receiver_id'] = receiver
            df.at[idx, 'receiver_distance'] = min_dist

    return df

# Step 3: Build pass network
def build_pass_network(df):
    """
    Create network graph from identified passes
    """
    # Filter passes with identified receivers
    valid_passes = df[df['receiver_id'].notna()].copy()

    # Aggregate pass statistics
    network_stats = valid_passes.groupby(['player_id', 'receiver_id']).agg({
        'start_x': 'size',      # Total passes (count rows)
        'is_key_pass': 'sum',   # Key passes
        'is_long_ball': 'sum'   # Long balls
    }).rename(columns={'start_x': 'total_passes'}).reset_index()

    # Create directed graph
    G = nx.DiGraph()

    for _, row in network_stats.iterrows():
        G.add_edge(
            row['player_id'],
            row['receiver_id'],
            weight=row['total_passes'],
            key_passes=row['is_key_pass'],
            long_balls=row['is_long_ball']
        )

    return G, valid_passes, network_stats

# Step 4: Visualize pass network with OPTA pitch - STRAIGHT LINES
def visualize_pass_network(G, pass_data, min_passes=1):
    """
    Visualize pass network with nodes positioned by average player location
    """
    # Calculate average position for each player
    player_avg_pos = pass_data.groupby('player_id').agg({
        'start_x': 'mean',
        'start_y': 'mean'
    })

    # Create position dict (no need to invert Y for Opta coordinates)
    pos = {
        player: (player_avg_pos.loc[player, 'start_x'],
                 player_avg_pos.loc[player, 'start_y'])
        for player in G.nodes()
    }

    # Filter edges by minimum passes
    edges_to_draw = [(u, v) for u, v, d in G.edges(data=True)
                     if d['weight'] >= min_passes]

    # Setup plot with mplsoccer
    fig, ax = plt.subplots(figsize=(16, 11))

    # Draw Opta pitch
    pitch = Pitch(pitch_type='opta', pitch_color='white', line_color='black', linewidth=2)
    pitch.draw(ax=ax)

    # Draw nodes (players)
    node_sizes = [G.degree(node) * 150 for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color='#e8fffb', edgecolors='red',
                          node_size=node_sizes, alpha=0.8, ax=ax)

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=20, font_weight='bold', ax=ax)

    # Draw edges (passes) - STRAIGHT LINES
    edge_weights = [G[u][v]['weight'] for u, v in edges_to_draw]
    nx.draw_networkx_edges(G, pos, edgelist=edges_to_draw,
                          width=[w * 1 for w in edge_weights],
                          alpha=0.6, arrows=False, arrowsize=15,
                          edge_color='#e82f30', ax=ax,
                          connectionstyle='arc3,rad=0')  # rad=0 makes them straight

    # ax.set_title('Pass Network - Successful Passes Only',
    #              fontsize=20, fontweight='bold', color='white', pad=20)

    plt.tight_layout()
    return fig

# Step 5: Generate network statistics
def print_network_stats(G, network_stats):
    """
    Print comprehensive network statistics
    """
    print("="*60)
    print("PASS NETWORK STATISTICS")
    print("="*60)
    print(f"\nTotal players: {G.number_of_nodes()}")
    print(f"Total pass connections: {G.number_of_edges()}")
    print(f"Network density: {nx.density(G):.3f}")

    print("\n" + "-"*60)
    print("TOP PASS COMBINATIONS (Passer → Receiver)")
    print("-"*60)
    top_combinations = network_stats.nlargest(10, 'total_passes')
    for _, row in top_combinations.iterrows():
        print(f"Player {row['player_id']} → Player {row['receiver_id']}: "
              f"{int(row['total_passes'])} passes "
              f"({int(row['is_key_pass'])} key passes)")

    print("\n" + "-"*60)
    print("MOST ACTIVE PASSERS")
    print("-"*60)
    out_degree = dict(G.out_degree(weight='weight'))
    top_passers = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:5]
    for player, passes in top_passers:
        print(f"Player {player}: {int(passes)} passes made")

    print("\n" + "-"*60)
    print("MOST ACTIVE RECEIVERS")
    print("-"*60)
    in_degree = dict(G.in_degree(weight='weight'))
    top_receivers = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]
    for player, passes in top_receivers:
        print(f"Player {player}: {int(passes)} passes received")

# MAIN EXECUTION
# ==============

# Load all player data
print("Loading player data...")
df_all_passes = load_all_players('./')  # Adjust path if needed
print(f"Loaded {len(df_all_passes)} successful passes from {df_all_passes['player_id'].nunique()} players")

# Assign receivers
print("\nAssigning receivers...")
df_all_passes = assign_receivers(df_all_passes, max_distance=5)

# Build network
print("Building pass network...")
G, valid_passes, network_stats = build_pass_network(df_all_passes)

# Print statistics
print_network_stats(G, network_stats)

# Visualize
print("\nGenerating visualization...")
fig = visualize_pass_network(G, valid_passes, min_passes=2)
plt.savefig('pass_network.png', dpi=300, bbox_inches='tight', facecolor='#0e1117')
plt.show()

# Export to CSV
print("\nExporting network data...")
network_stats.to_csv('pass_network_data.csv', index=False)
print("✓ Saved to 'pass_network_data.csv'")

# Export as adjacency matrix
adjacency_matrix = nx.to_pandas_adjacency(G, weight='weight')
adjacency_matrix.to_csv('pass_adjacency_matrix.csv')
print("✓ Saved adjacency matrix to 'pass_adjacency_matrix.csv'")

print("\n" + "="*60)
print(f"Successfully linked {len(valid_passes)} passes out of {len(df_all_passes)} total")
print(f"Success rate: {len(valid_passes)/len(df_all_passes)*100:.1f}%")
print("="*60)