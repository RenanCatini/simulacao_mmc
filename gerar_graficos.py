import os
import math
import string
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==============================================================================
# CONFIGURACAO EDITORIAL (PADRAO ARTIGO CIENTIFICO - SBC / IEEE)
# ==============================================================================
INCLUIR_TITULOS = False  # Em LaTeX, use \caption{} em vez de titulo no grafico
MAX_C = 16

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman", "Computer Modern Roman"],
    "mathtext.fontset": "stix",
    "font.size": 10.5,
    "axes.titlesize": 11,
    "axes.labelsize": 10.5,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 8.5,
    "axes.linewidth": 0.8,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

os.makedirs("graficos/pdf", exist_ok=True)
os.makedirs("graficos/png", exist_ok=True)

df_resumo = pd.read_csv("resumo_experimento.csv")
df_rodadas = pd.read_csv("resultados_rodadas.csv")

cs = sorted(df_resumo["c"].unique())[:MAX_C]
rhos = sorted(df_resumo["rho_alvo"].unique())
df_resumo = df_resumo[df_resumo["c"].isin(cs)]
df_rodadas = df_rodadas[df_rodadas["c"].isin(cs)]

# Paleta sobria com suporte para ate 16 valores distintos de c
paleta_base = [
    "#1B4F72", "#D35400", "#117864", "#7D3C98",
    "#B03A2E", "#2874A6", "#B7950B", "#1F618D",
    "#A04000", "#148F77", "#6C3483", "#922B21",
    "#2E86C1", "#CA6F1E", "#1E8449", "#515A5A"
]
marcadores_base = ["o", "s", "^", "D", "v", "P", "X", "*", "<", ">", "p", "h", "d", "H", "8", "1"]

cores = {c: paleta_base[i % len(paleta_base)] for i, c in enumerate(cs)}
marcadores = {c: marcadores_base[i % len(marcadores_base)] for i, c in enumerate(cs)}


def estilizar_eixo(ax, grid_axis="both"):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis=grid_axis, which="major", linestyle="--", linewidth=0.5, alpha=0.4)
    ax.grid(True, axis=grid_axis, which="minor", linestyle=":", linewidth=0.4, alpha=0.25)


def salvar_figura(nome_base):
    plt.savefig(f"graficos/pdf/{nome_base}.pdf")
    plt.savefig(f"graficos/png/{nome_base}.png")
    plt.close()


# ==============================================================================
# FIGURA 1: Validacao E[N] em grade adaptativa (ate 4 colunas x 4 linhas)
# ==============================================================================
n_c = len(cs)
ncols = min(4, n_c)
nrows = math.ceil(n_c / ncols)
letras = [f"({l})" for l in string.ascii_lowercase[:n_c]]

fig, axes = plt.subplots(
    nrows, ncols,
    figsize=(3.4 * ncols, 3.1 * nrows),
    sharey=True,
    squeeze=False
)

for idx, c in enumerate(cs):
    row, col = divmod(idx, ncols)
    ax = axes[row][col]
    grupo = df_resumo[df_resumo["c"] == c].sort_values("rho_alvo")
    cor = cores[c]
    marc = marcadores[c]

    ax.plot(grupo["rho_alvo"], grupo["en_teorico"], linestyle="-", linewidth=1.5,
            color="#2C3E50", label="Teórico (Erlang-C)", zorder=2)

    ax.fill_between(grupo["rho_alvo"], grupo["en_ic_inf"], grupo["en_ic_sup"],
                    color=cor, alpha=0.20, linewidth=0, label="IC 95%")

    ax.plot(grupo["rho_alvo"], grupo["en_sim_media"], marker=marc, linestyle="none",
            markersize=5.2, color=cor, markeredgecolor="white", markeredgewidth=0.5,
            label="Média Simulada", zorder=3)

    ax.set_title(f"{letras[idx]} M/M/{c}", pad=6)
    if row == nrows - 1:
        ax.set_xlabel(r"Ocupação ($\rho$)")
    if col == 0:
        ax.set_ylabel(r"$E[N]$ (log)")

    ax.set_yscale("log")
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.99])
    ax.set_xticklabels(["0,2", "0,4", "0,6", "0,8", "0,99"])
    estilizar_eixo(ax)

    if idx == 0:
        ax.legend(loc="upper left", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=7.8)

# Oculta subplots sobrando na ultima linha
for idx_vazio in range(n_c, nrows * ncols):
    row, col = divmod(idx_vazio, ncols)
    axes[row][col].set_visible(False)

if INCLUIR_TITULOS:
    fig.suptitle(r"Validação de $E[N]$: Modelo Analítico vs. Simulação", y=1.02)

plt.tight_layout(w_pad=1.0, h_pad=1.2)
salvar_figura("fig1_validacao_en")

# ==============================================================================
# FIGURA 2: Impacto do Paralelismo no Tempo Medio E[W]
# ==============================================================================
fig, ax = plt.subplots(figsize=(8.0, 4.6))

for c in cs:
    grupo = df_resumo[df_resumo["c"] == c].sort_values("rho_alvo")
    cor = cores[c]
    marc = marcadores[c]

    ax.plot(grupo["rho_alvo"], grupo["ew_teorico"], linestyle="--", linewidth=1.1,
            color=cor, alpha=0.65)

    ax.fill_between(grupo["rho_alvo"], grupo["ew_ic_inf"], grupo["ew_ic_sup"],
                    color=cor, alpha=0.12, linewidth=0)

    ax.plot(grupo["rho_alvo"], grupo["ew_sim_media"], marker=marc, linestyle="-",
            linewidth=1.5, markersize=5.2, color=cor, markeredgecolor="white",
            markeredgewidth=0.5, label=f"M/M/{c}")

tempo_atendimento = 1.0 / df_resumo["mu"].iloc[0]
ax.axhline(y=tempo_atendimento, color="#555555", linestyle=":", linewidth=1.3,
           label=rf"$1/\mu = {tempo_atendimento:.0f}\,\mathrm{{s}}$")

if INCLUIR_TITULOS:
    ax.set_title(r"Tempo Médio no Sistema $E[W]$ por Número de Servidores ($c$)", pad=10)

ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
ax.set_ylabel(r"Tempo Médio no Sistema $E[W]$ (s) — escala log")
ax.set_yscale("log")
ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
ax.set_xticklabels(["0,20", "0,40", "0,60", "0,80", "0,90", "0,99"])
estilizar_eixo(ax)

ncol_leg = 2 if n_c > 6 else 1
ax.legend(loc="upper left", ncol=ncol_leg, frameon=True, framealpha=0.92,
          edgecolor="#CCCCCC", title="Simulado (±IC 95%) | Tracejado: Teórico", title_fontsize=8)

plt.tight_layout()
salvar_figura("fig2_comparacao_ew")

# ==============================================================================
# FIGURA 3: Erro Relativo Percentual (%) de E[N] por Cenario
# ==============================================================================
fig, ax = plt.subplots(figsize=(max(7.5, 0.6 * n_c + 6.0), 4.2))

x = np.arange(len(rhos))
largura = 0.82 / n_c

for idx, c in enumerate(cs):
    sub = df_resumo[df_resumo["c"] == c].sort_values("rho_alvo")
    deslocamento = (idx - (n_c - 1) / 2.0) * largura
    barras = ax.bar(x + deslocamento, sub["erro_rel_en"], width=largura,
                    color=cores[c], edgecolor="#222222", linewidth=0.4,
                    alpha=0.88, label=f"M/M/{c}")

    if n_c <= 6:
        for barra in barras:
            altura = barra.get_height()
            ax.annotate(f"{altura:.1f}%".replace(".", ","),
                        xy=(barra.get_x() + barra.get_width() / 2, altura),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.5, color="#222222")

if INCLUIR_TITULOS:
    ax.set_title(r"Erro Relativo Percentual de $E[N]$ (Simulado vs. Teórico)", pad=10)

ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
ax.set_ylabel("Erro Relativo (%)")
ax.set_xticks(x)
ax.set_xticklabels([f"{r:.2f}".replace(".", ",") for r in rhos])
ax.set_ylim(0, df_resumo["erro_rel_en"].max() * 1.20)
estilizar_eixo(ax, grid_axis="y")
ax.legend(loc="upper left", ncol=2 if n_c > 6 else 1, frameon=True,
          framealpha=0.92, edgecolor="#CCCCCC")

plt.tight_layout()
salvar_figura("fig3_erro_relativo")

# ==============================================================================
# FIGURA 4: Dispersao entre as Seeds (Boxplot para rho = 0.80 e rho = 0.90)
# ==============================================================================
largura_box_fig = max(9.2, 0.75 * n_c + 7.5)
fig, axes = plt.subplots(1, 2, figsize=(largura_box_fig, 4.1), sharey=False)
letras_box = ["(a)", "(b)"]

for idx, rho_sel in enumerate([0.80, 0.90]):
    ax = axes[idx]
    sub_rod = df_rodadas[np.isclose(df_rodadas["rho_alvo"], rho_sel)]
    dados_box = [sub_rod[sub_rod["c"] == c]["ew"].values for c in cs]

    bp = ax.boxplot(
        dados_box,
        tick_labels=[f"{c}" for c in cs],
        patch_artist=True,
        widths=0.52,
        medianprops=dict(color="#111111", linewidth=1.4),
        whiskerprops=dict(color="#444444", linewidth=0.9),
        capprops=dict(color="#444444", linewidth=0.9),
        flierprops=dict(marker="o", markersize=3.0, markerfacecolor="#666666",
                        markeredgecolor="none", alpha=0.6)
    )
    for patch, c in zip(bp["boxes"], cs):
        patch.set_facecolor(cores[c])
        patch.set_edgecolor("#222222")
        patch.set_linewidth(0.7)
        patch.set_alpha(0.75)

    for i, c in enumerate(cs):
        teo = df_resumo[(df_resumo["c"] == c) & (np.isclose(df_resumo["rho_alvo"], rho_sel))]["ew_teorico"].values[0]
        ax.hlines(teo, i + 0.65, i + 1.35, colors="#922B21", linestyles="--", linewidth=1.5,
                  label="Teórico (Erlang-C)" if i == 0 else "", zorder=4)

    rho_fmt = f"{rho_sel:.2f}".replace(".", ",")
    ax.set_title(rf"{letras_box[idx]} Dispersão nas Replicações ($\rho = {rho_fmt}$)", pad=8)
    ax.set_xlabel(r"Número de Servidores ($c$)")
    ax.set_ylabel(r"$E[W]$ por Rodada (s)")
    estilizar_eixo(ax, grid_axis="y")
    if idx == 0:
        ax.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#CCCCCC")

plt.tight_layout(w_pad=1.8)
salvar_figura("fig4_boxplot_seeds")

print(f"Figuras exportadas para {n_c} valores de c em graficos/pdf e graficos/png com sucesso!")