import os
import math
import string
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==============================================================================
# CONFIGURACAO EDITORIAL (PADRAO ARTIGO CIENTIFICO - SBC / IEEE)
# ==============================================================================
INCLUIR_TITULOS = False  # Em LaTeX, use \caption{}

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

os.makedirs("graficos/", exist_ok=True)

df_resumo = pd.read_csv("resumo_experimento.csv")
df_rodadas = pd.read_csv("resultados_rodadas.csv")

perfis_ordem = ["Rapido", "Mediano", "Lento"]
rotulos_perfis = {
    "Rapido":  r"Rápido ($\mu = 0{,}50\,\mathrm{s}^{-1}$, $S = 2\,\mathrm{s}$)",
    "Mediano": r"Mediano ($\mu = 0{,}125\,\mathrm{s}^{-1}$, $S = 8\,\mathrm{s}$)",
    "Lento":   r"Lento ($\mu = 0{,}05\,\mathrm{s}^{-1}$, $S = 20\,\mathrm{s}$)",
}

cs = sorted(df_resumo["c"].unique())
rhos = sorted(df_resumo["rho_alvo"].unique())

paleta_c = ["#1B4F72", "#D35400", "#117864", "#7D3C98", "#B03A2E", "#2874A6", "#B7950B", "#1F618D"]
marcadores_c = ["o", "s", "^", "D", "v", "P", "X", "*"]
cores_c = {c: paleta_c[i % len(paleta_c)] for i, c in enumerate(cs)}
marc_c = {c: marcadores_c[i % len(marcadores_c)] for i, c in enumerate(cs)}

cores_perfil = {"Rapido": "#117864", "Mediano": "#1B4F72", "Lento": "#B03A2E"}
marc_perfil = {"Rapido": "^", "Mediano": "o", "Lento": "s"}


def estilizar_eixo(ax, grid_axis="both"):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis=grid_axis, which="major", linestyle="--", linewidth=0.5, alpha=0.4)
    ax.grid(True, axis=grid_axis, which="minor", linestyle=":", linewidth=0.4, alpha=0.25)


def salvar_png(nome_base):
    plt.savefig(f"graficos/{nome_base}.png")
    plt.close()


# ==============================================================================
# FIGURA 1: Tempo Medio E[W] nos 3 Perfis (Paineis compartilhando Eixo Y)
# ==============================================================================
fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.1), sharey=True)
letras = list(string.ascii_lowercase)

for idx, perfil in enumerate(perfis_ordem):
    ax = axes[idx]
    sub_p = df_resumo[df_resumo["perfil"] == perfil]
    mu_val = sub_p["mu"].iloc[0]
    s_val = 1.0 / mu_val

    for c in cs:
        grupo = sub_p[sub_p["c"] == c].sort_values("rho_alvo")
        ax.plot(grupo["rho_alvo"], grupo["ew_teorico"], linestyle="--", linewidth=1.1,
                color=cores_c[c], alpha=0.65)
        ax.fill_between(grupo["rho_alvo"], grupo["ew_ic_inf"], grupo["ew_ic_sup"],
                        color=cores_c[c], alpha=0.14, linewidth=0)
        ax.plot(grupo["rho_alvo"], grupo["ew_sim_media"], marker=marc_c[c], linestyle="-",
                linewidth=1.5, markersize=5.0, color=cores_c[c],
                markeredgecolor="white", markeredgewidth=0.5, label=f"M/M/{c}")

    ax.axhline(y=s_val, color="#333333", linestyle=":", linewidth=1.3,
               label=rf"Base $S = {s_val:.0f}\,\mathrm{{s}}$")

    ax.set_title(f"({letras[idx]}) {rotulos_perfis[perfil]}", pad=8, fontsize=10)
    ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
    if idx == 0:
        ax.set_ylabel(r"Tempo Médio no Sistema $E[W]$ (s) — log")

    ax.set_yscale("log")
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
    ax.set_xticklabels(["0,2", "0,4", "0,6", "0,8", "0,9", "0,99"])
    estilizar_eixo(ax)
    ax.legend(loc="upper left", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=8)

plt.tight_layout(w_pad=1.1)
salvar_png("fig1_ew_perfis_painel")

# ==============================================================================
# FIGURA 2: Invariancia de E[N] para TODOS os valores de c
# ==============================================================================
n_c = len(cs)
ncols_c = min(3, n_c)
nrows_c = math.ceil(n_c / ncols_c)

fig, axes = plt.subplots(nrows_c, ncols_c, figsize=(4.0 * ncols_c, 3.4 * nrows_c),
                         sharey=True, squeeze=False)

for idx, c_val in enumerate(cs):
    row, col = divmod(idx, ncols_c)
    ax = axes[row][col]
    sub_c = df_resumo[df_resumo["c"] == c_val]

    teo_ref = sub_c[sub_c["perfil"] == "Mediano"].sort_values("rho_alvo")
    ax.plot(teo_ref["rho_alvo"], teo_ref["en_teorico"], linestyle="-", linewidth=1.8,
            color="#222222", label="Teórico (Erlang-C)", zorder=2)

    for perfil in perfis_ordem:
        grupo = sub_c[sub_c["perfil"] == perfil].sort_values("rho_alvo")
        ax.plot(grupo["rho_alvo"], grupo["en_sim_media"], marker=marc_perfil[perfil],
                linestyle="none", markersize=5.8, color=cores_perfil[perfil],
                markeredgecolor="white", markeredgewidth=0.5,
                label=f"Simulado — {perfil}", zorder=3)

    ax.set_title(f"({letras[idx]}) Arquitetura M/M/{c_val}", pad=7)
    if row == nrows_c - 1:
        ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
    if col == 0:
        ax.set_ylabel(r"Número Médio no Sistema $E[N]$ (log)")

    ax.set_yscale("log")
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
    ax.set_xticklabels(["0,2", "0,4", "0,6", "0,8", "0,9", "0,99"])
    estilizar_eixo(ax)
    if idx == 0:
        ax.legend(loc="upper left", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=8)

for idx_vazio in range(n_c, nrows_c * ncols_c):
    row, col = divmod(idx_vazio, ncols_c)
    axes[row][col].set_visible(False)

plt.tight_layout(w_pad=1.2, h_pad=1.3)
salvar_png("fig2_invariancia_en")

# ==============================================================================
# FIGURA 3: Trade-off Arquitetural (c vs. mu) para TODOS os niveis de rho
# ==============================================================================
n_rho = len(rhos)
ncols_r = min(3, n_rho)
nrows_r = math.ceil(n_rho / ncols_r)

fig, axes = plt.subplots(nrows_r, ncols_r, figsize=(4.2 * ncols_r, 3.5 * nrows_r),
                         sharey=False, squeeze=False)

for idx, rho_sel in enumerate(rhos):
    row, col = divmod(idx, ncols_r)
    ax = axes[row][col]
    sub_r = df_resumo[np.isclose(df_resumo["rho_alvo"], rho_sel)]

    for perfil in perfis_ordem:
        grupo = sub_r[sub_r["perfil"] == perfil].sort_values("c")
        yerr_inf = grupo["ew_sim_media"] - grupo["ew_ic_inf"]
        yerr_sup = grupo["ew_ic_sup"] - grupo["ew_sim_media"]

        ax.errorbar(grupo["c"], grupo["ew_sim_media"], yerr=[yerr_inf, yerr_sup],
                    fmt=f"-{marc_perfil[perfil]}", linewidth=1.6, markersize=5.5,
                    color=cores_perfil[perfil], capsize=3.0,
                    label=rotulos_perfis[perfil])

    rho_fmt = f"{rho_sel:.2f}".replace(".", ",")
    ax.set_title(rf"({letras[idx]}) Ocupação $\rho = {rho_fmt}$", pad=7)
    if row == nrows_r - 1:
        ax.set_xlabel(r"Número de Servidores ($c$)")
    if col == 0:
        ax.set_ylabel(r"Tempo Médio $E[W]$ (s)")

    ax.set_xscale("log", base=2)
    ax.set_xticks(cs)
    ax.set_xticklabels([str(c) for c in cs])
    estilizar_eixo(ax)
    if idx == 0:
        ax.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=7.5)

for idx_vazio in range(n_rho, nrows_r * ncols_r):
    row, col = divmod(idx_vazio, ncols_r)
    axes[row][col].set_visible(False)

plt.tight_layout(w_pad=1.3, h_pad=1.3)
salvar_png("fig3_tradeoff_c_vs_mu")

# ==============================================================================
# FIGURA 4: Erro Relativo (%) por Perfil apenas para rho in {0.80, 0.90, 0.99}
# ==============================================================================
rhos_fig4 = [0.80, 0.90, 0.99]
fig, axes = plt.subplots(1, len(rhos_fig4), figsize=(12.2, 3.8), sharey=True)

x = np.arange(len(cs))
largura = 0.26

for idx, rho_sel in enumerate(rhos_fig4):
    ax = axes[idx]
    sub_r = df_resumo[np.isclose(df_resumo["rho_alvo"], rho_sel)]

    for ip, perfil in enumerate(perfis_ordem):
        grupo = sub_r[sub_r["perfil"] == perfil].sort_values("c")
        barras = ax.bar(x + (ip - 1) * largura, grupo["erro_rel_en"], width=largura,
                        color=cores_perfil[perfil], edgecolor="#222222", linewidth=0.45,
                        alpha=0.88, label=perfil)

        for barra in barras:
            h = barra.get_height()
            if h >= 1.0:
                ax.annotate(f"{h:.1f}%".replace(".", ","),
                            xy=(barra.get_x() + barra.get_width() / 2, h),
                            xytext=(0, 2.5), textcoords="offset points",
                            ha="center", va="bottom", fontsize=7.0, rotation=90)

    rho_fmt = f"{rho_sel:.2f}".replace(".", ",")
    ax.set_title(rf"({letras[idx]}) Ocupação $\rho = {rho_fmt}$", pad=8)
    ax.set_xlabel(r"Número de Servidores ($c$)")
    if idx == 0:
        ax.set_ylabel(r"Erro Relativo em $E[N]$ (%)")

    ax.set_xticks(x)
    ax.set_xticklabels([str(c) for c in cs])
    ax.set_ylim(0, df_resumo[df_resumo["rho_alvo"].isin(rhos_fig4)]["erro_rel_en"].max() * 1.25)
    estilizar_eixo(ax, grid_axis="y")
    if idx == 0:
        ax.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=8.5)

plt.tight_layout(w_pad=1.1)
salvar_png("fig4_erro_relativo_perfis")

print("Todos os graficos completos gerados com sucesso em 'graficos/png/'!")