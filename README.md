# Mininet-GUI: Uma Abordagem Visual e Interativa para Experimentação em Redes SDN

![mininet-gui logo](https://github.com/user-attachments/assets/c3c35610-1d7b-4458-a08e-2f9608816501)

O Mininet é um emulador amplamente utilizado para a prototipação e experimentação de Redes Definidas por Software (SDN). No entanto, sua interface gráfica principal, o MiniEdit, oferece suporte limitado e baixa interatividade, dificultando sua adoção e restringindo experimentações avançadas. Embora diversas ferramentas tenham sido propostas, nenhuma se consolidou como alternativa definitiva devido à falta de integração de funcionalidades essenciais. 
Neste trabalho, apresentamos o Mininet-GUI, uma ferramenta integrada que opera através de uma interface web para viabilizar a criação, edição e execução de topologias no Mininet em tempo real. O Mininet-GUI possibilita a manipulação dinâmica de hosts, switches, controladores e links, além da execução de comandos diretamente na interface. Diferentemente das abordagens existentes, o Mininet-GUI oferece edição interativa da topologia, acesso simplificado aos terminais via WebShell e suporte à exportação/importação de topologias nos formatos JSON e Python.  
O Mininet-GUI visa tornar a experimentação com SDN mais acessível e eficiente, atendendo tanto a iniciantes quanto a pesquisadores avançados. Este trabalho descreve sua arquitetura, funcionalidades e aplicabilidade por meio de casos de uso recorrentes.

![mininet-gui screenshot](https://github.com/user-attachments/assets/1d5bfc10-859e-4385-96ac-f8f366e14b5a)

# Estrutura do readme.md

O arquivo README.md divide-se nas seguintes seções: Selos Considerados, Informações Básicas, Dependências, Preocupações com segurança, Instalação, Teste mínimo, Experimentos e LICENSE.
O repositório contém dois subdiretórios principais: mininet-gui-frontend, com o código da aplicação frontend, e mininet-gui-backend, com o código do backend.
Além disso, há dois scripts setup.sh e run.sh, para facilitar a instalação e execução.
Foram incluídos também dois arquivos: `example_network_export.json` e `example_network_export.py`, que são arquivos exemplos exportados de uma topologia criada no Mininet-GUI.


# Selos Considerados

Os selos considerados são: Disponíveis, Funcionais, Sustentáveis e Reprodutíveis.


# Informações básicas

Vídeo da demonstração: <https://youtu.be/YSsqHKsJlxY>

Repositório oficial: <https://github.com/latarc/mininet-gui>

Para a demonstração, foi utilizado um laptop com as seguintes configurações:

Processador:	Intel(R) Core(TM) i5-10300H CPU @ 2.50GHz   2.50 GHz
RAM instalada:	8,00 GB
Sistema Operacional:	Windows 11 Home Single Language
Tipo de sistema:	Sistema operacional de 64 bits, processador baseado em x64
Espaço disponível em disco: Pelo menos 80GB livres


# Dependências

A execução do Mininet-GUI requer o Oracle VirtualBox (versão 7.1.6 r167084).
Memória RAM: Mínimo de 8GB para a máquina virtual.


# Preocupações com segurança

A instalação nativa do Mininet é invasiva, e pode alterar ou remover arquivos importantes do sistema de arquivos. 
Por isso, recomenda-se a utilização da VM do Mininet-GUI que disponibilizamos no repositório.


# Instalação

## Máquina Virtual (recomendado)

Pré-requisitos: Oracle VirtualBox (<https://www.virtualbox.org/wiki/Downloads>)

Passo 1: Baixe o arquivo ova neste link: <https://drive.google.com/file/d/1HBqlTwEWnmkPjRFJVQhEn34itKNyzhg3/view?usp=sharing>

Passo 2: Abra o arquivo `Mininet-GUI-Desktop-VM-SBRC-2025.ova` no VirtualBox, para importar a máquina virtual

Passo 3: Execute a máquina virtual (user `mininet`, senha `mininet`)


## Instalação manual

Atenção: os comandos abaixo irão modificar o kernel e outras configurações do seu sistema operacional, portanto use com cautela.
Utilize os comandos abaixo para instalar manualmente (testado no ubuntu 20.04):

```bash
git clone https://github.com/mininet/mininet
cd mininet
./util/install.sh -nfv
cd ..
git clone https://github.com/latarc/mininet-gui
cd mininet-gui
./setup.sh
```

Opcionalmente, para instalar o Ryu:
```bash
pip3 install ryu eventlet==0.30.0 dnspython==1.16.0
```

# Teste mínimo

Passo 1: Execute a VM dentro do VirtualBox e faça login (usuário: `mininet`, senha: `mininet`)

Passo 2: Abra o terminal (Ctrl+Alt+T) e rode o seguinte comando: `mininet_gui` (ou alternativamente `/home/mininet/mininet-gui/run.sh`)

Passo 3: A execução do comando do Passo 2 mostrará em sua saída do terminal uma URL (Exemplo: `http://10.0.2.15:5173`). Acesse essa URL em um navegador dentro da VM.

Passo 4: Para criar um controlador, arraste o ícone rotulado "Controller", localizado na aba lateral esquerda, para o centro da tela. Em seguida, se abrirá uma caixa de diálogo, perguntando o tipo do controller. Nessa etapa, selecione a opção "Default" e em seguida pressione o botão "Submit" para criar o controller.

Passo 5: Clique no botão "Generate Topology" localizado na aba lateral esquerda. No modal, selecione o "Topology Type" Single, o "Controller" c1, e no campo "Hosts" insira o número 2. Em seguida, pressione o botão "Submit".

Passo 6: Execute um teste de pingall clicando no botão "Run Pingall Test" na aba lateral esquerda e aguarde os resultados aparecerem.

Passo 7 (opcional): Teste com iperf - selecione no webshell o terminal do node h1 e digite o comando `iperf -s`. Depois, abra o terminal do node h2 e digite o comando `iperf -c 10.0.0.1`. Aguarde 1 minuto para o teste completar-se.

Passo 8 (opcional): Multiplos controladores - arraste um novo "Controller" da barra lateral para o centro da tela, mas dessa vez mude o type para "Remote" e preencha o IP 127.0.0.1 e a porta 6633. Em seguida, gere uma topologia (com o "Generate Topology") do tipo Single e com 2 hosts, e também selecione o novo controlador criado (c2). Adicionalmente, clique no botão "Create Link" e conecte os switches das duas topologias, s1 e s2, clicando e arrastando de um para o outro (o sucesso dessa ação é indicado por uma linha verde conectando os dois nós). A seguir, selecione no webshell o terminal do novo controlador c2 e execute o comando: `ryu-manager --ofp-tcp-listen-port 6633 ryu.app.simple_switch_13` para iniciar o controlador SDN Ryu. Optamos por utilizar o Ryu nesse exemplo, pois ele é leve e não ocupa tanto espaço na VM quanto outros (ONOS, OpenDaylight, Floodlight). Para testar a conexão, execute um teste com o botão de Pingall.

Passo 9: Finalmente, clique nos botões "Export Topology (JSON)" e "Export Mininet Script" para obter respectivamente o arquivo JSON com a configuração da topologia atual e o script do mininet para executar a topologia fora do Mininet-GUI, diretamente no Python.


# Experimentos

A execução da VM requer no mínimo 2GB de RAM e um core de CPU reservado à VM.

## Reivindicação "Geração automatizada de topologias, incluindo diversos modelos amplamente utilizados"

Após inicializar o mininet_gui e acessar a interface web do frontend, clique no botão "Generate Topology". Selecione o tipo de topologia (Single, Linear ou Tree), 
e o número de dispositivos, então clique em OK.

## Reivindicação "Terminal integrado dos nós via WebShell"

Após inicializar o mininet_gui e acessar a interface web do frontend, crie ao menos um nó (seja pelo Gerador de Topologias ou clicando e arrastando) e na aba inferior titulada "Webshell"
selecione a aba com o nome desse nó, clicando nela.
Em seguida, utilize o terminal bash para executar comandos diretamente no namespace daquele nó.

# LICENSE

BSD 3-Clause License

Copyright (c) 2025, LaTARC Research Lab

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
