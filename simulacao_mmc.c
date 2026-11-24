#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct Info_ {
    unsigned long int numero_eventos;
    double soma_areas;
    double tempo_anterior;
} Info;

typedef struct ResultadoRodada_ {
    int rodada;
    unsigned int seed;
    double t_warmup;
    double ocupacao;
    double en;
    double ew;
    double erro_little;
    unsigned long int max_fila;
} ResultadoRodada;

typedef struct Estatistica_ {
    double media;
    double desvio_padrao;
    double ic_inferior;
    double ic_superior;
    double margem_abs;
    double margem_rel;
} Estatistica;

void iniciaInfo(Info *info) {
    info->numero_eventos = 0;
    info->soma_areas = 0.0;
    info->tempo_anterior = 0.0;
}

double aleatorio() {
    double u = rand() / ((double) RAND_MAX + 1.0);
    return 1.0 - u; // (0, 1]
}

double min_val(double n1, double n2) {
    return (n1 < n2) ? n1 : n2;
}

double obter_t_critico_95(int gl) {
    static const double tabela_t[31] = {
        0.0,
        12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201,  2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080,  2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042
    };
    if (gl < 1) return 0.0;
    if (gl <= 30) return tabela_t[gl];
    double z = 1.959964;
    return z + (pow(z, 3) + z) / (4.0 * gl);
}

void calcular_teorico_mmc(double lambda, double mu, int c,
                          double *rho_teo, double *en_teo, double *ew_teo, double *prob_espera_teo) {
    double a = lambda / mu;
    *rho_teo = lambda / (c * mu);

    double termo = 1.0;
    double soma = termo;
    for (int k = 1; k < c; k++) {
        termo *= a / k;
        soma += termo;
    }
    double termo_c = termo * (a / c);
    double parcela_c = termo_c / (1.0 - (*rho_teo));

    double p0 = 1.0 / (soma + parcela_c);
    *prob_espera_teo = parcela_c * p0;

    *en_teo = a + ((*rho_teo) * (*prob_espera_teo)) / (1.0 - (*rho_teo));
    *ew_teo = (*en_teo) / lambda;
}

ResultadoRodada executar_simulacao_mmc(int rodada, unsigned int seed,
                                       double lambda, double mu, int c,
                                       double tempo_total, double passo_amostra,
                                       double *soma_serie_en, double *soma_serie_ew, int n_amostras) {
    srand(seed);

    Info en;
    iniciaInfo(&en);

    double tempo_decorrido = 0.0;
    double chegada_cliente = (-1.0 / lambda) * log(aleatorio());

    unsigned long int fila = 0;
    unsigned long int max_fila = 0;
    unsigned long int chegadas_estacionario = 0;
    int servidores_ocupados = 0;
    double soma_atendimentos = 0.0;

    int warmup_concluido = 0;
    double inicio_medicao = 0.0;
    double prox_amostra = passo_amostra;
    int idx_amostra = 0;
    double en_anterior = -1.0;

    double *saida_servidor = (double *) malloc(c * sizeof(double));
    if (!saida_servidor) {
        fprintf(stderr, "Erro de alocacao de memoria.\n");
        exit(1);
    }
    for (int i = 0; i < c; i++) saida_servidor[i] = INFINITY;

    while (1) {
        double menor_saida = INFINITY;
        int idx_saida = -1;
        for (int i = 0; i < c; i++) {
            if (saida_servidor[i] < menor_saida) {
                menor_saida = saida_servidor[i];
                idx_saida = i;
            }
        }

        double prox_evento = min_val(chegada_cliente, menor_saida);

        while (prox_amostra <= prox_evento && prox_amostra <= tempo_total) {
            double area_inst = en.soma_areas + en.numero_eventos * (prox_amostra - en.tempo_anterior);
            double jan = prox_amostra - inicio_medicao;
            double en_inst = (jan > 0.0) ? (area_inst / jan) : 0.0;
            double ew_inst = en_inst / lambda;

            if (idx_amostra < n_amostras) {
                soma_serie_en[idx_amostra] += en_inst;
                soma_serie_ew[idx_amostra] += ew_inst;
                idx_amostra++;
            }

            // Detecta estabilizacao: variacao relativa < 1% entre janelas de 1000s # Margem Descarte
            if (!warmup_concluido) {
                if ((en_anterior > 0.0 && en_inst > 0.0 && (fabs(en_inst - en_anterior) / en_inst) < 0.001) ||
                        prox_amostra >= tempo_total * 0.40) {
                    en.soma_areas = 0.0;
                    en.tempo_anterior = prox_amostra;

                    chegadas_estacionario = 0;
                    soma_atendimentos = 0.0;
                    for (int i = 0; i < c; i++) {
                        if (!isinf(saida_servidor[i]) && saida_servidor[i] > prox_amostra) {
                            double fim_efetivo = min_val(saida_servidor[i], tempo_total);
                            soma_atendimentos += (fim_efetivo - prox_amostra);
                        }
                    }

                    max_fila = fila;
                    warmup_concluido = 1;
                    inicio_medicao = prox_amostra;
                }
                en_anterior = en_inst;
            }

            prox_amostra += passo_amostra;
        }

        if (prox_evento > tempo_total) {
            en.soma_areas += en.numero_eventos * (tempo_total - en.tempo_anterior);
            en.tempo_anterior = tempo_total;
            tempo_decorrido = tempo_total;
            break;
        }

        tempo_decorrido = prox_evento;

        if (tempo_decorrido == chegada_cliente) {
            if (servidores_ocupados < c) {
                for (int i = 0; i < c; i++) {
                    if (isinf(saida_servidor[i])) {
                        double duracao_servico = (-1.0 / mu) * log(aleatorio());
                        saida_servidor[i] = tempo_decorrido + duracao_servico;
                        if (warmup_concluido) {
                            double fim_efetivo = min_val(saida_servidor[i], tempo_total);
                            soma_atendimentos += (fim_efetivo - tempo_decorrido);
                        }
                        servidores_ocupados++;
                        break;
                    }
                }
            }

            fila++;
            if (warmup_concluido) {
                chegadas_estacionario++;
                if (fila > max_fila) max_fila = fila;
            }

            chegada_cliente = tempo_decorrido + (-1.0 / lambda) * log(aleatorio());

            en.soma_areas += en.numero_eventos * (tempo_decorrido - en.tempo_anterior);
            en.tempo_anterior = tempo_decorrido;
            en.numero_eventos++;

        } else {
            fila--;

            if (fila >= (unsigned long int) c) {
                double duracao_servico = (-1.0 / mu) * log(aleatorio());
                saida_servidor[idx_saida] = tempo_decorrido + duracao_servico;
                if (warmup_concluido) {
                    double fim_efetivo = min_val(saida_servidor[idx_saida], tempo_total);
                    soma_atendimentos += (fim_efetivo - tempo_decorrido);
                }
            } else {
                saida_servidor[idx_saida] = INFINITY;
                servidores_ocupados--;
            }

            en.soma_areas += en.numero_eventos * (tempo_decorrido - en.tempo_anterior);
            en.tempo_anterior = tempo_decorrido;
            en.numero_eventos--;
        }
    }

    double tempo_estacionario = tempo_decorrido - inicio_medicao;
    double lambda_efetivo = chegadas_estacionario / tempo_estacionario;
    double en_final = en.soma_areas / tempo_estacionario;
    double ew_final = (lambda_efetivo > 0.0) ? (en_final / lambda_efetivo) : 0.0;

    free(saida_servidor);

    ResultadoRodada res;
    res.rodada = rodada;
    res.seed = seed;
    res.t_warmup = inicio_medicao;
    res.ocupacao = soma_atendimentos / (c * tempo_estacionario);
    res.en = en_final;
    res.ew = ew_final;
    res.erro_little = en_final - (lambda_efetivo * ew_final);
    res.max_fila = max_fila;
    return res;
}

Estatistica calcular_estatistica(const double *amostras, int R) {
    Estatistica est;
    double soma = 0.0;
    for (int i = 0; i < R; i++) soma += amostras[i];
    est.media = soma / R;

    if (R < 2) {
        est.desvio_padrao = 0.0;
        est.margem_abs = INFINITY;
        est.margem_rel = INFINITY;
        est.ic_inferior = est.media;
        est.ic_superior = est.media;
        return est;
    }

    double soma_quadrados = 0.0;
    for (int i = 0; i < R; i++) {
        double diff = amostras[i] - est.media;
        soma_quadrados += diff * diff;
    }
    est.desvio_padrao = sqrt(soma_quadrados / (R - 1));

    double t_crit = obter_t_critico_95(R - 1);
    est.margem_abs = t_crit * (est.desvio_padrao / sqrt((double) R));
    est.margem_rel = (est.media > 0.0) ? (est.margem_abs / est.media) : INFINITY;
    est.ic_inferior = est.media - est.margem_abs;
    est.ic_superior = est.media + est.margem_abs;
    return est;
}

int main() {
    const char *nomes_perfis[] = {"Rapido", "Mediano", "Lento"};
    double valores_mu[]        = {20.0,     5.0,       2.0};

    int valores_c[]            = {1, 2, 4, 8};
    double valores_rho[]       = {0.20, 0.40, 0.60, 0.80, 0.90, 0.99};

    double tempo_total         = 100000.0;
    double passo_transiente    = 1000.0; 

    double margem_alvo         = 0.05;
    int R_min                  = 20;
    int R_max                  = 300;

    int num_perfis = sizeof(valores_mu) / sizeof(valores_mu[0]);
    int num_c      = sizeof(valores_c) / sizeof(valores_c[0]);
    int num_rho    = sizeof(valores_rho) / sizeof(valores_rho[0]);
    int n_amostras = (int) (tempo_total / passo_transiente);

    FILE *f_rodadas    = fopen("resultados_rodadas.csv", "w");
    FILE *f_resumo     = fopen("resumo_experimento.csv", "w");
    FILE *f_transiente = fopen("serie_transiente.csv", "w");

    if (!f_rodadas || !f_resumo || !f_transiente) {
        fprintf(stderr, "Erro ao criar arquivos CSV.\n");
        return 1;
    }

    fprintf(f_rodadas, "perfil,c,rho_alvo,rodada,seed,t_warmup_rodada,lambda,mu,ocupacao,en,ew,erro_little,max_fila\n");
    fprintf(f_transiente, "perfil,c,rho_alvo,tempo,en_acumulado,ew_acumulado\n");
    fprintf(f_resumo, "perfil,c,rho_alvo,lambda,mu,T_total,T_warmup,R_necessario,margem_alvo,"
                      "rho_teorico,rho_sim_media,rho_ic_inf,rho_ic_sup,erro_rel_rho,"
                      "en_teorico,en_sim_media,en_ic_inf,en_ic_sup,margem_ic_en,erro_rel_en,capturou_en,"
                      "ew_teorico,ew_sim_media,ew_ic_inf,ew_ic_sup,margem_ic_ew,erro_rel_ew,capturou_ew\n");

    double *vet_ocup   = (double *) malloc(R_max * sizeof(double));
    double *vet_en     = (double *) malloc(R_max * sizeof(double));
    double *vet_ew     = (double *) malloc(R_max * sizeof(double));
    double *vet_warmup = (double *) malloc(R_max * sizeof(double));
    double *soma_s_en  = (double *) malloc(n_amostras * sizeof(double));
    double *soma_s_ew  = (double *) malloc(n_amostras * sizeof(double));

    int total_cenarios = 0;
    int coberturas_en = 0;
    int coberturas_ew = 0;

    printf("=== CLUSTER M/M/c: AUTO-CORTE SIMPLES (<1%% em 1000s) + SEEDS COMUNS ===\n\n");

    for (int ip = 0; ip < num_perfis; ip++) {
        const char *perfil = nomes_perfis[ip];
        double mu          = valores_mu[ip];

        printf(">>> PERFIL: %s (mu = %.1f req/s | Latencia base S = %.0f ms) <<<\n",
               perfil, mu, (1.0 / mu) * 1000.0);

        for (int ic = 0; ic < num_c; ic++) {
            int c = valores_c[ic];

            for (int ir = 0; ir < num_rho; ir++) {
                double rho_alvo = valores_rho[ir];
                double lambda   = rho_alvo * c * mu;

                double rho_teo, en_teo, ew_teo, prob_espera_teo;
                calcular_teorico_mmc(lambda, mu, c, &rho_teo, &en_teo, &ew_teo, &prob_espera_teo);

                for (int k = 0; k < n_amostras; k++) {
                    soma_s_en[k] = 0.0;
                    soma_s_ew[k] = 0.0;
                }

                int r = 0;
                Estatistica est_ocup, est_en, est_ew, est_warmup;

                while (r < R_max) {
                    unsigned int seed_atual = (unsigned int) (r + 1);

                    ResultadoRodada res = executar_simulacao_mmc(
                        r + 1, seed_atual, lambda, mu, c,
                        tempo_total, passo_transiente, soma_s_en, soma_s_ew, n_amostras
                    );

                    vet_ocup[r]   = res.ocupacao;
                    vet_en[r]     = res.en;
                    vet_ew[r]     = res.ew;
                    vet_warmup[r] = res.t_warmup;
                    r++;

                    fprintf(f_rodadas, "%s,%d,%.2f,%d,%u,%.1f,%.6f,%.6f,%.6f,%.6f,%.6f,%.8f,%lu\n",
                            perfil, c, rho_alvo, res.rodada, res.seed, res.t_warmup, lambda, mu,
                            res.ocupacao, res.en, res.ew, res.erro_little, res.max_fila);

                    est_ocup   = calcular_estatistica(vet_ocup, r);
                    est_en     = calcular_estatistica(vet_en, r);
                    est_ew     = calcular_estatistica(vet_ew, r);
                    est_warmup = calcular_estatistica(vet_warmup, r);

                    if (r >= R_min &&
                        est_en.margem_rel <= margem_alvo &&
                        est_ew.margem_rel <= margem_alvo) {
                        break;
                    }
                }

                for (int k = 0; k < n_amostras; k++) {
                    fprintf(f_transiente, "%s,%d,%.2f,%.1f,%.6f,%.6f\n",
                            perfil, c, rho_alvo, (k + 1) * passo_transiente,
                            soma_s_en[k] / r, soma_s_ew[k] / r);
                }

                double erro_rel_ocup = fabs((est_ocup.media - rho_teo) / rho_teo) * 100.0;
                double erro_rel_en   = fabs((est_en.media - en_teo) / en_teo) * 100.0;
                double erro_rel_ew   = fabs((est_ew.media - ew_teo) / ew_teo) * 100.0;

                int cap_en = (en_teo >= est_en.ic_inferior && en_teo <= est_en.ic_superior) ? 1 : 0;
                int cap_ew = (ew_teo >= est_ew.ic_inferior && ew_teo <= est_ew.ic_superior) ? 1 : 0;

                total_cenarios++;
                coberturas_en += cap_en;
                coberturas_ew += cap_ew;

                fprintf(f_resumo, "%s,%d,%.2f,%.6f,%.6f,%.1f,%.1f,%d,%.4f,"
                                  "%.6f,%.6f,%.6f,%.6f,%.4f,"
                                  "%.6f,%.6f,%.6f,%.6f,%.4f,%.4f,%d,"
                                  "%.6f,%.6f,%.6f,%.6f,%.4f,%.4f,%d\n",
                        perfil, c, rho_alvo, lambda, mu, tempo_total, est_warmup.media, r, margem_alvo,
                        rho_teo, est_ocup.media, est_ocup.ic_inferior, est_ocup.ic_superior, erro_rel_ocup,
                        en_teo, est_en.media, est_en.ic_inferior, est_en.ic_superior,
                        est_en.margem_rel * 100.0, erro_rel_en, cap_en,
                        ew_teo, est_ew.media, est_ew.ic_inferior, est_ew.ic_superior,
                        est_ew.margem_rel * 100.0, erro_rel_ew, cap_ew);

                printf("[%s | c=%-2d | rho=%.2f] WarmupMed=%6.0fs | R=%-3d | "
                       "E[N]: Teo=%6.2f IC=[%6.2f,%6.2f] (%s) | "
                       "E[W]: Teo=%6.3fs IC=[%6.3f,%6.3f] (%s)\n",
                       perfil, c, rho_alvo, est_warmup.media, r,
                       en_teo, est_en.ic_inferior, est_en.ic_superior, cap_en ? "OK" : "FORA",
                       ew_teo, est_ew.ic_inferior, est_ew.ic_superior, cap_ew ? "OK" : "FORA");
            }
        }
        printf("---------------------------------------------------------------------------------------------------------------------\n");
    }

    fclose(f_rodadas);
    fclose(f_resumo);
    fclose(f_transiente);

    free(vet_ocup);
    free(vet_en);
    free(vet_ew);
    free(vet_warmup);
    free(soma_s_en);
    free(soma_s_ew);

    printf("\n=== AUDITORIA DE COBERTURA DO INTERVALO DE CONFIANCA (95%%) ===\n");
    printf("Cobertura E[N]: %d / %d cenarios (%.1f%%)\n",
           coberturas_en, total_cenarios, (100.0 * coberturas_en) / total_cenarios);
    printf("Cobertura E[W]: %d / %d cenarios (%.1f%%)\n",
           coberturas_ew, total_cenarios, (100.0 * coberturas_ew) / total_cenarios);
    return 0;
}