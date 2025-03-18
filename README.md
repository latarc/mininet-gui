# Mininet-GUI: Uma Abordagem Visual e Interativa para Experimentação em Redes SDN

O Mininet é um emulador amplamente utilizado para a prototipação e experimentação de Redes Definidas por Software (SDN). No entanto, sua interface gráfica principal, o MiniEdit, oferece suporte limitado e baixa interatividade, dificultando sua adoção e restringindo experimentações avançadas. Embora diversas ferramentas tenham sido propostas, nenhuma se consolidou como alternativa definitiva devido à falta de integração de funcionalidades essenciais. 
Neste trabalho, apresentamos o Mininet-GUI, uma ferramenta integrada que opera através de uma interface web para viabilizar a criação, edição e execução de topologias no Mininet em tempo real. O Mininet-GUI possibilita a manipulação dinâmica de hosts, switches, controladores e links, além da execução de comandos diretamente na interface. Diferentemente das abordagens existentes, o Mininet-GUI oferece edição interativa da topologia, acesso simplificado aos terminais via WebShell e suporte à exportação/importação de topologias nos formatos JSON e Python.  
O Mininet-GUI visa tornar a experimentação com SDN mais acessível e eficiente, atendendo tanto a iniciantes quanto a pesquisadores avançados. Este trabalho descreve sua arquitetura, funcionalidades e aplicabilidade por meio de casos de uso recorrentes.

# Estrutura do readme.md

O arquivo README.md divide-se nas seguintes seções: Selos Considerados, Informações Básicas, Dependências, Preocupações com segurança, Instalação, Teste mínimo, Experimentos e LICENSE.
O repositório contém dois subdiretórios principais: mininet-gui-frontend, com o código da aplicação frontend, e mininet-gui-backend, com o código do backend.
Além disso, há dois scripts setup.sh e run.sh, para facilitar a instalação e execução.


# Selos Considerados

Os selos considerados são: Disponíveis, Funcionais, Sustentáveis e Reprodutíveis.


# Informações básicas

Vídeo da demonstração: <https://www.youtube.com/watch?v=NR50fQHFmy0>

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

Pré-requisitos: Oracle VirtualBox (<https://www.virtualbox.org/wiki/Downloads>)

Passo 1: Baixe o arquivo zip neste link: <https://github.com/latarc/mininet-gui/releases/download/v0.0.1/Mininet-GUI-VM-SBRC-2025.zip>

Passo 2: Descompacte o arquivo zip, que contém um arquivo chamado "Mininet-GUI-VM-SBRC-2025.ova"

Passo 3: Abra o arquivo `Mininet-GUI-VM-SBRC-2025.ova` no VirtualBox, para importar a máquina virtual


# Teste mínimo

Passo 1: Execute a VM dentro do VirtualBox e faça login (usuário: `mininet`, senha: `mininet`)

Passo 2: Rode o seguinte comando: `mininet_gui` (ou alternativamente `/home/mininet/mininet-gui/run.sh`)

Passo 3:  A execução do comando do Passo 2 retornará em sua saída uma URL (Exemplo: `http://192.168.56.101:5173`). Acesse essa URL em um navegador no host da VM (o endereço IP deve ser o IP da máquina virtual do Mininet-GUI)


# Experimentos

A execução da VM utiliza 1.5GB de RAM e requer um core de CPU reservado à VM.


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

