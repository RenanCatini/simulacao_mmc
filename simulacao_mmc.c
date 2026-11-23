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
    double margem_erro;
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
                                       double lambda, double mu, int c, double tempo_simulacao) {
    srand(seed);

    Info en, ew_chegadas, ew_saidas;
    iniciaInfo(&en);
    iniciaInfo(&ew_chegadas);
    iniciaInfo(&ew_saidas);

    double tempo_decorrido = 0.0;
    double chegada_cliente = (-1.0 / lambda) * log(aleatorio());

    unsigned long int fila = 0;
    unsigned long int max_fila = 0;
    int servidores_ocupados = 0;
    double soma_atendimentos = 0.0;

    double *saida_servidor = (double *) malloc(c * sizeof(double));
    if (!saida_servidor) {
        fprintf(stderr, "Erro de alocacao de memoria.\n");
        exit(1);
    }
    for (int i = 0; i < c; i++) {
        saida_servidor[i] = INFINITY;
    }

    while (tempo_decorrido < tempo_simulacao) {
        double menor_saida = INFINITY;
        int idx_saida = -1;
        for (int i = 0; i < c; i++) {
            if (saida_servidor[i] < menor_saida) {
                menor_saida = saida_servidor[i];
                idx_saida = i;
            }
        }

        tempo_decorrido = min_val(chegada_cliente, menor_saida);

        if (tempo_decorrido == chegada_cliente) {
            if (servidores_ocupados < c) {
                for (int i = 0; i < c; i++) {
                    if (isinf(saida_servidor[i])) {
                        double duracao_servico = (-1.0 / mu) * log(aleatorio());
                        saida_servidor[i] = tempo_decorrido + duracao_servico;
                        soma_atendimentos += duracao_servico;
                        servidores_ocupados++;
                        break;
                    }
                }
            }

            fila++;
            if (fila > max_fila) {
                max_fila = fila;
            }

            chegada_cliente = tempo_decorrido + (-1.0 / lambda) * log(aleatorio());

            en.soma_areas += en.numero_eventos * (tempo_decorrido - en.tempo_anterior);
            en.tempo_anterior = tempo_decorrido;
            en.numero_eventos++;

            ew_chegadas.soma_areas += ew_chegadas.numero_eventos * (tempo_decorrido - ew_chegadas.tempo_anterior);
            ew_chegadas.tempo_anterior = tempo_decorrido;
            ew_chegadas.numero_eventos++;

        } else {
            fila--;

            if (fila >= (unsigned long int) c) {
                double duracao_servico = (-1.0 / mu) * log(aleatorio());
                saida_servidor[idx_saida] = tempo_decorrido + duracao_servico;
                soma_atendimentos += duracao_servico;
            } else {
                saida_servidor[idx_saida] = INFINITY;
                servidores_ocupados--;
            }

            en.soma_areas += en.numero_eventos * (tempo_decorrido - en.tempo_anterior);
            en.tempo_anterior = tempo_decorrido;
            en.numero_eventos--;

            ew_saidas.soma_areas += ew_saidas.numero_eventos * (tempo_decorrido - ew_saidas.tempo_anterior);
            ew_saidas.tempo_anterior = tempo_decorrido;
            ew_saidas.numero_eventos++;
        }
    }

    ew_chegadas.soma_areas += ew_chegadas.numero_eventos * (tempo_decorrido - ew_chegadas.tempo_anterior);
    ew_saidas.soma_areas += ew_saidas.numero_eventos * (tempo_decorrido - ew_saidas.tempo_anterior);

    double lambda_efetivo = ew_chegadas.numero_eventos / tempo_decorrido;
    double en_final = en.soma_areas / tempo_decorrido;
    double ew_final = (ew_chegadas.soma_areas - ew_saidas.soma_areas) / ew_chegadas.numero_eventos;

    free(saida_servidor);

    ResultadoRodada res;
    res.rodada = rodada;
    res.seed = seed;
    res.ocupacao = soma_atendimentos / (c * tempo_decorrido);
    res.en = en_final;
    res.ew = ew_final;
    res.erro_little = en_final - (lambda_efetivo * ew_final);
    res.max_fila = max_fila;
    return res;
}

Estatistica calcular_estatistica(const double *amostras, int R) {
    Estatistica est;
    double soma = 0.0;
    for (int i = 0; i < R; i++) {
        soma += amostras[i];
    }
    est.media = soma / R;

    if (R < 2) {
        est.desvio_padrao = 0.0;
        est.margem_erro = 0.0;
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
    est.margem_erro = t_crit * (est.desvio_padrao / sqrt((double) R));
    est.ic_inferior = est.media - est.margem_erro;
    est.ic_superior = est.media + est.margem_erro;
    return est;
}

int main() {
    // =========================================================================
    // CONFIGURACAO DA BATERIA DE EXPERIMENTOS (3 PERFIS DE VELOCIDADE)
    // =========================================================================
    const char *nomes_perfis[] = {"Rapido", "Mediano", "Lento"};
    double valores_mu[]        = {0.50,     0.125,     0.05};     // S = 2s, 8s e 20s

    int valores_c[]            = {1, 2, 4, 8, 16, 32};                 // Arquiteturas M/M/c
    double valores_rho[]       = {0.20, 0.40, 0.60, 0.80, 0.90, 0.99};
    double tempo_simulacao     = 500000.0;                         // Tempo fixo (T)
    int R                      = 30;                               // Replicacoes por cenario
    unsigned int seed_base     = 42;
    // =========================================================================

    int num_perfis = sizeof(valores_mu) / sizeof(valores_mu[0]);
    int num_c      = sizeof(valores_c) / sizeof(valores_c[0]);
    int num_rho    = sizeof(valores_rho) / sizeof(valores_rho[0]);

    FILE *f_rodadas = fopen("resultados_rodadas.csv", "w");
    FILE *f_resumo  = fopen("resumo_experimento.csv", "w");

    if (!f_rodadas || !f_resumo) {
        fprintf(stderr, "Erro ao criar arquivos CSV.\n");
        return 1;
    }

    fprintf(f_rodadas, "perfil,c,rho_alvo,rodada,seed,lambda,mu,ocupacao,en,ew,erro_little,max_fila\n");
    fprintf(f_resumo, "perfil,c,rho_alvo,lambda,mu,T,R,prob_espera_teo,"
                      "rho_teorico,rho_sim_media,rho_ic_inf,rho_ic_sup,erro_rel_rho,"
                      "en_teorico,en_sim_media,en_ic_inf,en_ic_sup,erro_rel_en,"
                      "ew_teorico,ew_sim_media,ew_ic_inf,ew_ic_sup,erro_rel_ew,"
                      "max_fila_media,max_fila_ic_inf,max_fila_ic_sup\n");

    ResultadoRodada *rodadas = (ResultadoRodada *) malloc(R * sizeof(ResultadoRodada));
    double *vet_ocup = (double *) malloc(R * sizeof(double));
    double *vet_en   = (double *) malloc(R * sizeof(double));
    double *vet_ew   = (double *) malloc(R * sizeof(double));
    double *vet_max  = (double *) malloc(R * sizeof(double));

    printf("=== BATERIA M/M/c: 3 PERFIS DE VELOCIDADE (%d cenarios x %d rodadas) ===\n\n",
           num_perfis * num_c * num_rho, R);

    for (int ip = 0; ip < num_perfis; ip++) {
        const char *perfil = nomes_perfis[ip];
        double mu          = valores_mu[ip];

        printf(">>> PERFIL: %s (mu = %.3f | Tempo medio atendimento S = %.1fs) <<<\n",
               perfil, mu, 1.0 / mu);

        for (int ic = 0; ic < num_c; ic++) {
            int c = valores_c[ic];

            for (int ir = 0; ir < num_rho; ir++) {
                double rho_alvo = valores_rho[ir];
                double lambda   = rho_alvo * c * mu;

                double rho_teo, en_teo, ew_teo, prob_espera_teo;
                calcular_teorico_mmc(lambda, mu, c, &rho_teo, &en_teo, &ew_teo, &prob_espera_teo);

                for (int r = 0; r < R; r++) {
                    unsigned int seed_atual = seed_base + r;
                    rodadas[r] = executar_simulacao_mmc(r + 1, seed_atual, lambda, mu, c, tempo_simulacao);

                    vet_ocup[r] = rodadas[r].ocupacao;
                    vet_en[r]   = rodadas[r].en;
                    vet_ew[r]   = rodadas[r].ew;
                    vet_max[r]  = (double) rodadas[r].max_fila;

                    fprintf(f_rodadas, "%s,%d,%.2f,%d,%u,%.6f,%.6f,%.6f,%.6f,%.6f,%.8f,%lu\n",
                            perfil, c, rho_alvo, rodadas[r].rodada, rodadas[r].seed, lambda, mu,
                            rodadas[r].ocupacao, rodadas[r].en, rodadas[r].ew,
                            rodadas[r].erro_little, rodadas[r].max_fila);
                }

                Estatistica est_ocup = calcular_estatistica(vet_ocup, R);
                Estatistica est_en   = calcular_estatistica(vet_en, R);
                Estatistica est_ew   = calcular_estatistica(vet_ew, R);
                Estatistica est_max  = calcular_estatistica(vet_max, R);

                double erro_rel_ocup = fabs((est_ocup.media - rho_teo) / rho_teo) * 100.0;
                double erro_rel_en   = fabs((est_en.media - en_teo) / en_teo) * 100.0;
                double erro_rel_ew   = fabs((est_ew.media - ew_teo) / ew_teo) * 100.0;

                fprintf(f_resumo, "%s,%d,%.2f,%.6f,%.6f,%.1f,%d,%.6f,"
                                  "%.6f,%.6f,%.6f,%.6f,%.4f,"
                                  "%.6f,%.6f,%.6f,%.6f,%.4f,"
                                  "%.6f,%.6f,%.6f,%.6f,%.4f,"
                                  "%.4f,%.4f,%.4f\n",
                        perfil, c, rho_alvo, lambda, mu, tempo_simulacao, R, prob_espera_teo,
                        rho_teo, est_ocup.media, est_ocup.ic_inferior, est_ocup.ic_superior, erro_rel_ocup,
                        en_teo, est_en.media, est_en.ic_inferior, est_en.ic_superior, erro_rel_en,
                        ew_teo, est_ew.media, est_ew.ic_inferior, est_ew.ic_superior, erro_rel_ew,
                        est_max.media, est_max.ic_inferior, est_max.ic_superior);

                printf("[%s | c=%-2d | rho=%.2f] E[N]: Teo=%6.2f vs Sim=%6.2f (Err=%5.2f%%) | "
                       "E[W]: Teo=%7.2f vs Sim=%7.2f (Err=%5.2f%%)\n",
                       perfil, c, rho_alvo, en_teo, est_en.media, erro_rel_en, ew_teo, est_ew.media, erro_rel_ew);
            }
        }
        printf("----------------------------------------------------------------------------------------------------\n");
    }

    fclose(f_rodadas);
    fclose(f_resumo);

    free(rodadas);
    free(vet_ocup);
    free(vet_en);
    free(vet_ew);
    free(vet_max);

    printf("\nConcluido! Dados salvos em 'resumo_experimento.csv' e 'resultados_rodadas.csv'.\n");
    return 0;
}