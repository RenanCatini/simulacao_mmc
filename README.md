# Simulação de Filas M/M/c e Análise de Desempenho

Este projeto apresenta um simulador de eventos discretos em C para sistemas de filas M/M/c e um script em Python para visualização de dados. O objetivo é analisar o comportamento do tempo médio de espera no sistema ($E[W]$), do número médio de clientes ($E[N]$) e do erro relativo de simulação sob diferentes configurações de servidores ($c$), taxas de ocupação ($\rho$) e velocidades de atendimento ($\mu$).

---

## Estrutura de Arquivos

* `simulacao_mmc.c`: Código-fonte em C com o motor da simulação.
* `gerar_graficos.py`: Script Python para gerar os gráficos na pasta `graficos/png/`.

---

## Como Compilar e Executar

### No Linux

1. Abra o terminal na pasta do projeto e compile o código em C:
   ```bash
   gcc simulacao_mmc.c -o simulacao_mmc -O2 -lm
   ```

2. Execute o simulador para gerar os arquivos de dados CSV:
   ```bash
   ./simulacao_mmc
   ```

3. Instale as dependências em Python (se necessário) e gere as figuras:
   ```bash
   pip install pandas matplotlib numpy
   python3 gerar_graficos.py
   ```

### No Windows

1. Abra o Prompt de Comando (CMD) ou PowerShell na pasta do projeto (certifique-se de ter o GCC/MinGW no PATH):
   ```cmd
   gcc simulacao_mmc.c -o simulacao_mmc.exe -O2 -lm
   ```

2. Execute a simulação:
   ```cmd
   simulacao_mmc.exe
   ```

3. Instale as bibliotecas necessárias e execute o script dos gráficos:
   ```cmd
   pip install pandas matplotlib numpy
   python gerar_graficos.py
   ```

---

## Parâmetros do Experimento

As simulações consideram as seguintes variações:

* **Perfis de Atendimento ($\mu$):**
  * **Rápido:** $\mu = 0{,}50\,\mathrm{s}^{-1}$ (tempo médio de atendimento $S = 2\,\mathrm{s}$)
  * **Mediano:** $\mu = 0{,}125\,\mathrm{s}^{-1}$ (tempo médio de atendimento $S = 8\,\mathrm{s}$)
  * **Lento:** $\mu = 0{,}05\,\mathrm{s}^{-1}$ (tempo médio de atendimento $S = 20\,\mathrm{s}$)
* **Número de Servidores ($c$):** $1, 2, 4, 8, 16$ e $32$.
* **Taxa de Ocupação ($\rho$):** $0{,}20$, $0{,}40$, $0{,}60$, $0{,}80$, $0{,}90$ e $0{,}99$.
* **Duração da Simulação ($T$):** Fixo em $500.000\,\mathrm{s}$ por rodada, com $30$ repetições independentes (*seeds*).

---

## Análise Direta dos Gráficos

### Figura 1: Tempo Médio no Sistema ($E[W]$) por Perfil
* **Escala temporal:** À medida que o atendimento se torna mais lento (do perfil Rápido ao Lento), toda a curva do tempo de permanência é deslocada para cima. Isso ocorre porque o piso mínimo de tempo no sistema é determinado pelo próprio tempo de serviço ($S = 2\,\mathrm{s}$, $8\,\mathrm{s}$ e $20\,\mathrm{s}$).
* **Comportamento assintótico:** Independente da velocidade, o tempo médio no sistema aumenta acentuadamente quando a taxa de ocupação ultrapassa $\rho = 0{,}80$, seguindo com precisão a curva teórica de Erlang-C.

### Figura 2: Número Médio de Clientes ($E[N]$) e Invariância
* **Independência da velocidade ($\mu$):** Nos seis painéis ($c = 1$ a $c = 32$), os resultados simulados dos três perfis sobrepõem-se exatamente sobre a linha teórica. Isso confirma que a quantidade total de clientes dentro do sistema depende unicamente da taxa de carga ($\rho$) e da quantidade de servidores ($c$).
* **Capacidade em carga baixa:** Em $\rho = 0{,}20$, a quantidade média de clientes cresce de $0{,}25$ em $c = 1$ para $6{,}4$ em $c = 32$, pois mais servidores ativos sustentam o mesmo fluxo total sem formar filas significativas.

### Figura 3: Trade-off entre Servidores ($c$) e Velocidade ($\mu$)
* **Saturação de paralelismo em baixa carga:** Para ocupações até $\rho = 0{,}60$, adicionar mais de $4$ ou $8$ servidores praticamente não reduz o tempo de resposta, pois o valor estabiliza no tempo próprio de atendimento.
* **Equivalência em alta carga:** Em $\rho = 0{,}90$, uma infraestrutura com $32$ servidores lentos obtém um tempo médio de resposta de aproximadamente $23\,\mathrm{s}$, valor próximo ao de $4$ servidores medianos ($24\,\mathrm{s}$) ou de $1$ único servidor rápido ($20\,\mathrm{s}$).

### Figura 4: Erro Relativo em Regimes Críticos ($\rho \in \{0{,}80; 0{,}90; 0{,}99\}$)
* **Alta precisão até $\rho = 0{,}90$:** O erro relativo entre a simulação e a teoria permanece abaixo de $2\%$ em todas as configurações para $\rho = 0{,}80$ e $\rho = 0{,}90$.
* **Efeito transiente em $\rho = 0{,}99$:** No regime de extrema ocupação ($\rho = 0{,}99$), o erro cresce significativamente no perfil Lento (chegando a $30{,}7\%$ para $c = 1$). Como o tempo total de simulação é fixado em $500.000\,\mathrm{s}$, o servidor lento processa dez vezes menos eventos que o rápido, tornando a média mais sensível ao período inicial de aquecimento (onde o sistema inicia vazio).
