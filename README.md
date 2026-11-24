# Simulação de filas M/M/c

Este projeto implementa uma simulação de eventos discretos de filas M/M/c em C e gera gráficos comparativos em Python. O experimento avalia a ocupação, o número médio de clientes no sistema, o tempo médio no sistema e a probabilidade de espera em três perfis de atendimento e em quatro tamanhos de cluster.

As medidas analisadas são:

- $\rho$: taxa de ocupação do cluster;
- $E[N]$: número médio de requisições no sistema;
- $E[W]$: tempo médio de permanência no sistema;
- $P_{\mathrm{espera}}$: probabilidade de uma chegada encontrar todos os servidores ocupados.

## Estrutura do projeto

- [`simulacao_mmc.c`](simulacao_mmc.c): simulador principal, análise teórica, réplicas independentes e exportação dos dados.
- [`gerar_graficos.py`](gerar_graficos.py): geração das seis figuras na pasta `graficos/png/`.
- [`simulacao_v3.c`](simulacao_v3.c): versão anterior com um único servidor e entrada interativa.
- [`fluxograma.png`](fluxograma.png): representação visual do funcionamento do simulador.
- [`resultados_rodadas.csv`](resultados_rodadas.csv): resultados de todas as rodadas.
- [`resumo_experimento.csv`](resumo_experimento.csv): estatísticas agregadas e intervalos de confiança.
- [`serie_transiente.csv`](serie_transiente.csv): séries temporais médias usadas no estudo transiente.
- [`graficos/png/`](graficos/png): figuras geradas pelo Python.

Os arquivos CSV são ignorados pelo Git por serem produtos da execução. Eles são criados novamente ao executar `simulacao_mmc.c`.

## Configuração do experimento

O simulador atual executa 72 cenários: três perfis de serviço, quatro tamanhos de cluster e seis taxas de ocupação.

| Perfil | $\mu$ | Tempo médio de serviço $S=1/\mu$ |
|---|---:|---:|
| Rápido | 20 requisições/s | 50 ms |
| Mediano | 5 requisições/s | 200 ms |
| Lento | 2 requisições/s | 500 ms |

- Servidores: $c \in \{1, 2, 4, 8\}$;
- Ocupação: $\rho \in \{0{,}20;\ 0{,}40;\ 0{,}60;\ 0{,}80;\ 0{,}90;\ 0{,}99\}$;
- Taxa de chegada: $\lambda=\rho c\mu$;
- Tempo total de cada rodada: 100.000 unidades de tempo;
- Amostragem da série transiente: a cada 1.000 unidades de tempo;
- Margem relativa desejada: 5%;
- Confiança das réplicas: $95\%$ por t-Student;
- Mínimo de réplicas: 20;
- Máximo de réplicas: 300.

Cada cenário usa seeds consecutivas, iniciando em 1. O aquecimento é identificado em amostras temporais de 1.000 unidades: o processo considera estabilizado quando a variação relativa de $E[N](t)$ fica abaixo de 0,1% em duas amostras consecutivas, ou quando alcança 40% do tempo total.

A fila aguardando atendimento é implementada como FIFO. O tempo $E[W]$ é obtido pela diferença entre a entrada em serviço e a chegada de clientes que chegaram após o período de aquecimento, em vez de ser calculado pela aproximação $E[N]/\lambda$.

## Modelo teórico

Para o modelo M/M/c:

$$
a=\frac{\lambda}{\mu},
\qquad
\rho=\frac{\lambda}{c\mu}
$$

$$
C=\frac{\dfrac{a^c}{c!\,(1-\rho)}}{\displaystyle\sum_{k=0}^{c-1}\frac{a^k}{k!}+\frac{a^c}{c!\,(1-\rho)}}
$$

O código usa Erlang-C para calcular a probabilidade teórica de espera, o número médio no sistema e a latência teórica:

$$
P_{\mathrm{espera},\mathrm{teo}}=C
$$

$$
E[N]_{\mathrm{teo}}=a+\frac{\rho C}{1-\rho},
\qquad
E[W]_{\mathrm{teo}}=\frac{E[N]_{\mathrm{teo}}}{\lambda}
$$

No simulador, as chegadas seguem processo de Poisson e os tempos de serviço seguem distribuição exponencial.

O erro de Little de cada rodada compara $E[N]$ com $\lambda_{\mathrm{efetivo}}\times E[W]$. Esse valor é registrado em `resultados_rodadas.csv` e agregado no resumo.

## Compilação e execução

### Windows

No Prompt de Comando ou no PowerShell, dentro da pasta do projeto:

```powershell
gcc simulacao_mmc.c -o simulacao_mmc.exe -O2 -lm
.\simulacao_mmc.exe
python gerar_graficos.py
```

### Linux

```bash
gcc simulacao_mmc.c -o simulacao_mmc -O2 -lm
./simulacao_mmc
python3 gerar_graficos.py
```

É necessário ter Python com os pacotes `pandas`, `matplotlib` e `numpy`:

```powershell
pip install pandas matplotlib numpy
```

O executável para Windows é gerado localmente e não é versionado pelo `.gitignore`.

## Arquivos gerados

O simulador escreve:

- `resultados_rodadas.csv`: ocupação, probabilidade de espera, $E[N]$, $E[W]$, erro de Little, fila máxima e período de aquecimento de cada rodada;
- `resumo_experimento.csv`: médias, intervalos de confiança, margens relativas, erros teóricos, probabilidade de espera e cobertura de $E[N]$ e $E[W]$ por cenário;
- `serie_transiente.csv`: evolução média acumulada de $E[N]$ e $E[W]$.

O script Python gera:

1. `fig1_periodo_transiente.png`: convergência da série transiente;
2. `fig2_replicacoes_necessarias.png`: número de réplicas necessárias;
3. `fig3_cobertura_ic.png`: cobertura dos intervalos de confiança em $\rho=0{,}90$;
4. `fig4_latencia_perfis_painel.png`: latência simulada e teórica por perfil;
5. `fig5_invariancia_en.png`: invariância de $E[N]$ em relação ao perfil de serviço;
6. `fig6_probabilidade_espera.png`: probabilidade teórica e simulada de encontrar o sistema ocupado.

## Análise estatística

Ao final da execução, o programa imprime no terminal:

- o aquecimento médio de cada cenário;
- o número de réplicas usadas;
- os intervalos de confiança de 95% para $P_{\mathrm{espera}}$, $E[N]$ e $E[W]$;
- a cobertura dos valores teóricos pelos intervalos de $E[N]$ e $E[W]$.

Cada cenário começa com 20 réplicas. Novas réplicas são executadas até que as margens relativas de $E[N]$ e $E[W]$ sejam menores ou iguais a 5%, ou até atingir o limite de 300 réplicas.

Os gráficos devem ser interpretados junto aos intervalos de confiança e ao período de aquecimento calculado para cada cenário. Os valores numéricos finais dependem da execução atual e são apresentados pelo terminal e pelos CSVs gerados pelo simulador.
