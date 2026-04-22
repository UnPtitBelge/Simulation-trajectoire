import numpy as np

def plots():
    import pandas as pd
    import matplotlib.pyplot as plt
    
    dfC = pd.read_csv("resultsConique.csv")
    dfL = pd.read_csv("resultsLaplace.csv")
    dfLR = pd.read_csv("resultsLaplace R_C.csv")
    dfT = pd.read_csv("tracking_data.csv", delimiter=";")
    dfT["y"] = dfT["y"].max() - dfT["y"]

    
    fig, axes = plt.subplots(1, 4, figsize=(14, 6))

    # -------------------------
    # Graphe 1 : trajectoire simulée normalisée
    # -------------------------
    axes[0].plot(dfT["x"], dfT["y"])
    axes[0].set_xlabel("x normalisé")
    axes[0].set_ylabel("y normalisé")
    axes[0].set_title("Trajectoire simulée normalisée")
    axes[0].grid(True)
    axes[0].axis("equal")
    
    # -------------------------
    # Graphe 2 : trajectoire réelle interpolée et normalisée
    # -------------------------
    axes[1].plot(dfC["r_x"], dfC["r_y"])
    axes[1].set_xlabel("x normalisé")
    axes[1].set_ylabel("y normalisé")
    axes[1].set_title("Trajectoire réelle interpolée et normalisée")
    axes[1].grid(True)
    axes[1].axis("equal")
    
    # -------------------------
    # Graphe 3 : trajectoire réelle interpolée et normalisée
    # -------------------------
    axes[2].plot(dfL["r_x"], dfL["r_y"])
    axes[2].set_xlabel("x normalisé")
    axes[2].set_ylabel("y normalisé")
    axes[2].set_title("Trajectoire réelle interpolée et normalisée")
    axes[2].grid(True)
    axes[2].axis("equal")
    
    # -------------------------
    # Graphe 2 : trajectoire réelle interpolée et normalisée
    # -------------------------
    axes[3].plot(dfLR["r_x"], dfLR["r_y"])
    axes[3].set_xlabel("x normalisé")
    axes[3].set_ylabel("y normalisé")
    axes[3].set_title("Trajectoire réelle interpolée et normalisée")
    axes[3].grid(True)
    axes[3].axis("equal")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plots()
