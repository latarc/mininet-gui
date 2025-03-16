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
Espaço disponível em disco: Pelo menos 80GB


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

Apresente a licença.

