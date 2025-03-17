# Mininet-GUI: Uma Abordagem Visual e Interativa para Experimentação em Redes SDN

Resumo descrevendo o objetivo do artefato, com o respectivo título e resumo do artigo.


# Estrutura do readme.md

Apresenta a estrutura do readme.md, descrevendo como o repositório está organizado.


# Selos Considerados

Os selos considerados são: Disponíveis, Funcionais, Sustentáveis e Reprodutíveis.


# Informações básicas

Para a demonstração, foi utilizado um laptop com as seguintes configurações:

Processador:	Intel(R) Core(TM) i5-10300H CPU @ 2.50GHz   2.50 GHz
RAM instalada:	8,00 GB
Sistema Operacional:	Windows 11 Home Single Language
Tipo de sistema:	Sistema operacional de 64 bits, processador baseado em x64
Espaço disponível em disco: Pelo menos 80GB livres


# Dependências

A demonstração do Mininet-GUI utilizou o Oracle VirtualBox (versão 7.1.6 r167084).


# Preocupações com segurança

A instalação nativa do Mininet é invasiva, e pode alterar ou remover arquivos importantes do sistema de arquivos. 
Por isso, recomenda-se a utilização da VM do Mininet-GUI que disponibilizamos no repositório.


# Instalação

Pré-requisitos: Oracle VirtualBox (<https://www.virtualbox.org/wiki/Downloads>)

Passo 1: Baixe o arquivo zip neste link: <https://link.para.vm>

Passo 2: Descompacte o arquivo, que contém uma pasta chamada "mininet-gui-vm"

Passo 3: Abra o arquivo `Mininet-GUI-VM-SBRC2025.ovf` no VirtualBox, para importar a máquina virtual


# Teste mínimo

Passo 1: Execute a VM dentro do VirtualBox e faça login (usuário: `mininet`, senha: `mininet`)

Passo 2: Rode o seguinte comando: `cd mininet-gui && ./run.sh`

Passo 3: Abra em um navegador a URL retornada como saída da execução do comando do Passo 2. Exemplo: `http://192.168.56.101:5173` (o endereço IP deve ser o IP da máquina virtual do Mininet-GUI).


# Experimentos

Esta seção deve descrever um passo a passo para a execução e obtenção dos resultados do artigo. Permitindo que os revisores consigam alcançar as reivindicações apresentadas no artigo. 
Cada reivindicações deve ser apresentada em uma subseção, com detalhes de arquivos de configurações a serem alterados, comandos a serem executados, flags a serem utilizadas, tempo esperado de execução, expectativa de recursos a serem utilizados como 1GB RAM/Disk e resultado esperado. 

Caso o processo para a reprodução de todos os experimento não seja possível em tempo viável. Os autores devem escolher as principais reivindicações apresentadas no artigo e apresentar o respectivo processo para reprodução.


## Reivindicações #X

## Reivindicações #Y


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

