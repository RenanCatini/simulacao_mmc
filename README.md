# Simulação de filas M/M/c

Projeto de simulação de eventos discretos para filas M/M/c, desenvolvido em C, com processamento dos resultados e geração de gráficos em Python. O experimento compara medidas simuladas com os valores teóricos de Erlang-C para diferentes números de servidores, taxas de ocupação e perfis de atendimento.

As medidas analisadas são:

- $\rho$: taxa de ocupação do cluster;
- $E[N]$: número médio de requisições no sistema;
- $E[W]$: tempo médio de permanência no sistema.

## Estrutura do projeto

- [`simulacao_mmc.c`](simulacao_mmc.c): simulador principal, análise teórica, réplicas independentes e exportação dos dados.
- [`gerar_graficos.py`](gerar_graficos.py): geração das cinco figuras na pasta `graficos/png/`.
- [`simulacao_v3.c`](simulacao_v3.c): versão anterior com um único servidor e entrada interativa.
- [`simulacao_mmc.exe`](simulacao_mmc.exe): executável já compilado para Windows.
- [`resultados_rodadas.csv`](resultados_rodadas.csv): resultados de todas as rodadas.
- [`resumo_experimento.csv`](resumo_experimento.csv): estatísticas agregadas e intervalos de confiança.
- [`serie_transiente.csv`](serie_transiente.csv): séries temporais médias usadas no estudo transiente.
- [`saida.txt`](saida.txt): captura de uma execução do experimento.
- [`graficos/png/`](graficos/png): figuras geradas pelo Python.

## Configuração do experimento

O programa atual executa 72 cenários: três perfis de serviço, quatro tamanhos de cluster e seis taxas de ocupação.

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

Cada cenário usa seeds comuns e consecutivas, com a primeira semente iniciando em 1. O aquecimento é identificado em amostras temporais de 1.000 unidades: o processo considera estabilizado quando a variação relativa de $E[N](t)$ fica abaixo de 1% em uma comparação consecutiva, ou quando alcança 40% do tempo total.

## Método de comparação

Para o modelo teórico M/M/c:

$$
a=\frac{\lambda}{\mu},
\qquad
\rho=\frac{\lambda}{c\mu}
$$

$$
C=\frac{\dfrac{a^c}{c!\,(1-\rho)}}{\displaystyle\sum_{k=0}^{c-1}\frac{a^k}{k!}+\frac{a^c}{c!\,(1-\rho)}}
$$

A implementação usa Erlang-C para calcular a probabilidade de espera, o número médio no sistema e a latência teórica:

$$
E[N]_{\text{teo}}=a+\frac{\rho C}{1-\rho}
\qquad
E[W]_{\text{teo}}=\frac{E[N]_{\text{teo}}}{\lambda}
$$

No simulador, as chegadas seguem processo de Poisson e os tempos de serviço seguem distribuição exponencial.

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

## Arquivos gerados

O simulador escreve:

- `resultados_rodadas.csv`: ocupação, $E[N]$, $E[W]$, erro de Little, fila máxima e período de aquecimento de cada rodada;
- `resumo_experimento.csv`: média, intervalo de confiança, margem relativa, erro teórico e cobertura de $E[N]$ e $E[W]$ por cenário;
- `serie_transiente.csv`: evolução média acumulada de $E[N]$ e $E[W]$.

O script Python gera:

1. `fig1_periodo_transiente.png`: convergência da série transiente;
2. `fig2_replicacoes_necessarias.png`: número de réplicas necessárias;
3. `fig3_cobertura_ic.png`: cobertura dos intervalos de confiança em $\rho=0{,}90$;
4. `fig4_latencia_perfis_painel.png`: latência simulada e teórica por perfil;
5. `fig5_invariancia_en.png`: invariância de $E[N]$ em relação ao perfil de serviço.

## Resultados observados

Da execução registrada em `saida.txt`:

- cobertura do intervalo de 95% para $E[N]$: 69 de 72 cenários (95,8%);
- cobertura do intervalo de 95% para $E[W]$: 62 de 72 cenários (86,1%);
- em $\rho=0{,}99$, o número necessário de réplicas cresce com a correlação temporal e pode alcançar o limite de 300;
- os resultados simulados acompanham a teoria de Erlang-C, especialmente para cargas moderadas;
- a latência cresce fortemente próximo de $\rho=1$, enquanto $E[N]$ permanece independente do perfil $\mu$ para uma mesma combinação $(c,\rho)$.

Os gráficos devem ser interpretados considerando o aquecimento, o número de réplicas de cada cenário e a precisão estatística registrada nos intervalos de confiança.
