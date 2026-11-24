import os
import math
import string
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ==============================================================================
# CONFIGURACAO EDITORIAL (PADRAO ARTIGO CIENTIFICO - SBC / IEEE)
# ==============================================================================
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

os.makedirs("graficos/png", exist_ok=True)

df_resumo = pd.read_csv("resumo_experimento.csv")
df_trans  = pd.read_csv("serie_transiente.csv")

perfis_ordem = ["Rapido", "Mediano", "Lento"]
rotulos_perfis = {
    "Rapido":  r"Rápido ($\mu = 20\,\mathrm{req/s}$, $S = 50\,\mathrm{ms}$)",
    "Mediano": r"Mediano ($\mu = 5\,\mathrm{req/s}$, $S = 200\,\mathrm{ms}$)",
    "Lento":   r"Lento ($\mu = 2\,\mathrm{req/s}$, $S = 500\,\mathrm{ms}$)",
}

cs = sorted(df_resumo["c"].unique())
paleta_c = ["#1B4F72", "#D35400", "#117864", "#7D3C98", "#B03A2E", "#2874A6"]
marcadores_c = ["o", "s", "^", "D", "v", "P"]
cores_c = {c: paleta_c[i % len(paleta_c)] for i, c in enumerate(cs)}
marc_c = {c: marcadores_c[i % len(marcadores_c)] for i, c in enumerate(cs)}

cores_perfil = {"Rapido": "#117864", "Mediano": "#1B4F72", "Lento": "#B03A2E"}
marc_perfil = {"Rapido": "^", "Mediano": "o", "Lento": "s"}
letras = list(string.ascii_lowercase)


def formatar_num_br(val, pos=None):
    if np.isclose(val, round(val)):
        return f"{int(round(val))}"
    return f"{val:g}".replace(".", ",")


def estilizar_eixo(ax, grid_axis="both", eixo_y_log=False):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", which="both", labelleft=True)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(formatar_num_br))
    if eixo_y_log:
        ax.yaxis.set_minor_formatter(ticker.NullFormatter())
    ax.grid(True, axis=grid_axis, which="major", linestyle="--", linewidth=0.5, alpha=0.4)
    ax.grid(True, axis=grid_axis, which="minor", linestyle=":", linewidth=0.4, alpha=0.25)


def salvar_png(nome_base):
    plt.savefig(f"graficos/png/{nome_base}.png")
    plt.close()


# ==============================================================================
# FIGURA 1: Periodo Transiente e Corte Individual para TODOS os Clusters (c)
# ==============================================================================
n_c = len(cs)
fig, axes = plt.subplots(n_c, 3, figsize=(13.2, 2.7 * n_c), sharex=True, squeeze=False)

for row_idx, c_val in enumerate(cs):
    for col_idx, perfil in enumerate(perfis_ordem):
        ax = axes[row_idx][col_idx]
        sub_t = df_trans[(df_trans["perfil"] == perfil) & (df_trans["c"] == c_val)]

        for rho_sel, cor_r in [(0.80, "#117864"), (0.90, "#1B4F72"), (0.99, "#B03A2E")]:
            serie = sub_t[np.isclose(sub_t["rho_alvo"], rho_sel)].sort_values("tempo")
            linha_res = df_resumo[(df_resumo["perfil"] == perfil) &
                                  (df_resumo["c"] == c_val) &
                                  (np.isclose(df_resumo["rho_alvo"], rho_sel))].iloc[0]

            teo = linha_res["en_teorico"]
            tw_ind = linha_res["T_warmup"]

            rho_fmt = f"{rho_sel:.2f}".replace(".", ",")
            ax.plot(serie["tempo"], serie["en_acumulado"], linewidth=1.3, color=cor_r,
                    label=rf"$\rho = {rho_fmt}$ ($T_w = {tw_ind:.0f}\,\mathrm{{s}}$)")
            ax.axhline(y=teo, color=cor_r, linestyle=":", linewidth=0.9, alpha=0.7)
            ax.axvline(x=tw_ind, color=cor_r, linestyle="--", linewidth=1.0, alpha=0.85)

        if row_idx == 0:
            ax.set_title(f"{rotulos_perfis[perfil]}", pad=8, fontsize=10.0)
        if row_idx == n_c - 1:
            ax.set_xlabel("Tempo de Simulação (s)")
        ax.set_ylabel(rf"$E[N](t)$ (M/M/{c_val})")

        estilizar_eixo(ax)
        ax.legend(loc="lower right", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=7.0)

plt.tight_layout(w_pad=1.3, h_pad=0.9)
salvar_png("fig1_periodo_transiente")


# ==============================================================================
# FIGURA 2: Replicacoes Necessarias (R) para Margem <= 5% (t-Student 95%)
# ==============================================================================
fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.8), sharey=False)

for idx, perfil in enumerate(perfis_ordem):
    ax = axes[idx]
    sub_p = df_resumo[df_resumo["perfil"] == perfil]

    for c in cs:
        grupo = sub_p[sub_p["c"] == c].sort_values("rho_alvo")
        ax.plot(grupo["rho_alvo"], grupo["R_necessario"], marker=marc_c[c], linestyle="-",
                linewidth=1.5, markersize=5.2, color=cores_c[c], label=f"M/M/{c}")

    max_r = sub_p["R_necessario"].max()
    ax.set_ylim(3, max_r * 1.12)

    ax.set_title(f"({letras[idx]}) {rotulos_perfis[perfil]}", pad=8, fontsize=9.8)
    ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
    ax.set_ylabel(r"Replicações Necessárias ($R$)")
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
    ax.set_xticklabels(["0,2", "0,4", "0,6", "0,8", "0,9", "0,99"])
    estilizar_eixo(ax)
    if idx == 0:
        ax.legend(loc="upper left", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=8)

plt.tight_layout(w_pad=1.4)
salvar_png("fig2_replicacoes_necessarias")


# ==============================================================================
# FIGURA 3: Cobertura do Intervalo de Confianca (95%) vs. Valor Teorico (E[W])
# ==============================================================================
fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.0), sharey=False)

for idx, perfil in enumerate(perfis_ordem):
    ax = axes[idx]
    sub_p = df_resumo[(df_resumo["perfil"] == perfil) & (np.isclose(df_resumo["rho_alvo"], 0.90))].sort_values("c")

    x_pos = np.arange(len(sub_p))
    y_med = sub_p["ew_sim_media"].values * 1000.0
    y_inf = (sub_p["ew_sim_media"].values - sub_p["ew_ic_inf"].values) * 1000.0
    y_sup = (sub_p["ew_ic_sup"].values - sub_p["ew_sim_media"].values) * 1000.0
    y_teo = sub_p["ew_teorico"].values * 1000.0
    caps  = sub_p["capturou_ew"].values

    ax.errorbar(x_pos, y_med, yerr=[y_inf, y_sup], fmt="none", ecolor="#1B4F72",
                elinewidth=1.8, capsize=4.5, label="IC 95% (t-Student)", zorder=2)

    rot_ok_usado = False
    rot_fora_usado = False
    for i in range(len(x_pos)):
        if caps[i] == 1:
            cor_pt = "#117864"
            rot_pt = "Teórico (Capturado)" if not rot_ok_usado else ""
            rot_ok_usado = True
        else:
            cor_pt = "#B03A2E"
            rot_pt = "Teórico (Fora do IC)" if not rot_fora_usado else ""
            rot_fora_usado = True

        ax.scatter(x_pos[i], y_teo[i], color=cor_pt, s=48, zorder=3,
                   marker="D", edgecolor="white", linewidth=0.6, label=rot_pt)

    ax.set_title(f"({letras[idx]}) {rotulos_perfis[perfil]}", pad=8, fontsize=9.8)
    ax.set_xlabel(r"Instâncias Paralelas ($c$) — $\rho = 0{,}90$")
    ax.set_ylabel(r"Latência Média $E[W]$ (ms)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(c) for c in sub_p["c"]])
    estilizar_eixo(ax)
    if idx == 0:
        ax.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=8)

plt.tight_layout(w_pad=1.4)
salvar_png("fig3_cobertura_ic")


# ==============================================================================
# FIGURA 4: Latencia Media E[W] nos 3 Perfis (Com valores no eixo Y de todos)
# ==============================================================================
fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.1), sharey=True)

for idx, perfil in enumerate(perfis_ordem):
    ax = axes[idx]
    sub_p = df_resumo[df_resumo["perfil"] == perfil]
    s_ms = (1.0 / sub_p["mu"].iloc[0]) * 1000.0

    for c in cs:
        grupo = sub_p[sub_p["c"] == c].sort_values("rho_alvo")
        ax.plot(grupo["rho_alvo"], grupo["ew_teorico"] * 1000.0, linestyle="--", linewidth=1.1,
                color=cores_c[c], alpha=0.65)
        ax.fill_between(grupo["rho_alvo"], grupo["ew_ic_inf"] * 1000.0, grupo["ew_ic_sup"] * 1000.0,
                        color=cores_c[c], alpha=0.14, linewidth=0)
        ax.plot(grupo["rho_alvo"], grupo["ew_sim_media"] * 1000.0, marker=marc_c[c], linestyle="-",
                linewidth=1.5, markersize=5.0, color=cores_c[c],
                markeredgecolor="white", markeredgewidth=0.5, label=f"M/M/{c}")

    ax.axhline(y=s_ms, color="#333333", linestyle=":", linewidth=1.3,
               label=rf"Base $S = {s_ms:.0f}\,\mathrm{{ms}}$")

    ax.set_title(f"({letras[idx]}) {rotulos_perfis[perfil]}", pad=8, fontsize=9.8)
    ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
    ax.set_ylabel(r"Latência Média $E[W]$ (ms) — log")

    ax.set_yscale("log")
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
    ax.set_xticklabels(["0,2", "0,4", "0,6", "0,8", "0,9", "0,99"])
    estilizar_eixo(ax, eixo_y_log=True)
    ax.legend(loc="upper left", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=8)

plt.tight_layout(w_pad=1.4)
salvar_png("fig4_latencia_perfis_painel")


# ==============================================================================
# FIGURA 5: Invariancia de E[N] para TODOS os valores de c (Na mesma fila)
# ==============================================================================
n_c = len(cs)
fig, axes = plt.subplots(1, n_c, figsize=(3.6 * n_c, 3.6), sharey=True, squeeze=False)

for idx, c_val in enumerate(cs):
    ax = axes[0][idx]
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

    ax.set_title(f"({letras[idx]}) Cluster M/M/{c_val}", pad=7, fontsize=10.0)
    ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
    ax.set_ylabel(r"Requisições no Cluster $E[N]$ (log)")

    ax.set_yscale("log")
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
    ax.set_xticklabels(["0,2", "0,4", "0,6", "0,8", "0,9", "0,99"])
    estilizar_eixo(ax, eixo_y_log=True)
    if idx == 0:
        ax.legend(loc="upper left", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=7.5)

# ==============================================================================
# FIGURA 6: Validacao de Erlang-C — Probabilidade de Espera P_espera
# ==============================================================================
fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.0), sharey=True)

for idx, perfil in enumerate(perfis_ordem):
    ax = axes[idx]
    sub_p = df_resumo[df_resumo["perfil"] == perfil]

    for c in cs:
        grupo = sub_p[sub_p["c"] == c].sort_values("rho_alvo")
        ax.plot(grupo["rho_alvo"], grupo["prob_espera_teo"], linestyle="--", linewidth=1.1,
                color=cores_c[c], alpha=0.65)
        ax.fill_between(grupo["rho_alvo"], grupo["prob_espera_ic_inf"], grupo["prob_espera_ic_sup"],
                        color=cores_c[c], alpha=0.14, linewidth=0)
        ax.plot(grupo["rho_alvo"], grupo["prob_espera_sim"], marker=marc_c[c], linestyle="-",
                linewidth=1.5, markersize=5.0, color=cores_c[c],
                markeredgecolor="white", markeredgewidth=0.5, label=f"M/M/{c}")

    ax.set_title(f"({letras[idx]}) {rotulos_perfis[perfil]}", pad=8, fontsize=9.8)
    ax.set_xlabel(r"Taxa de Ocupação ($\rho$)")
    ax.set_ylabel(r"Probabilidade de Espera ($P_{\mathrm{espera}}$)")
    ax.set_ylim(-0.02, 1.05)
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
    ax.set_xticklabels(["0,2", "0,4", "0,6", "0,8", "0,9", "0,99"])
    estilizar_eixo(ax)
    if idx == 0:
        ax.legend(loc="upper left", frameon=True, framealpha=0.92, edgecolor="#CCCCCC", fontsize=8)

plt.tight_layout(w_pad=1.4)
salvar_png("fig6_probabilidade_espera")


plt.tight_layout(w_pad=1.3)
salvar_png("fig5_invariancia_en")

print("Todas as 5 figuras geradas com sucesso em 'graficos/png/'!")