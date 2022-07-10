<h1>Scout Badminton  :badminton: </h1>


![Badge em Desenvolvimento](http://img.shields.io/static/v1?label=status&message=em%20desenvolvimento&color=GREEN&style=flat)





## Índice 

* [Sobre o projeto](#Sobre-o-projeto)
* [Funcionalidades do projeto](#Funcionalidades-do-projeto)
* [Principais tecnologias utilizadas](#Principais-tecnologias-utilizadas)
* [Como usar](#Como-usar)
* [Projeto backend](#Projeto-backend)
* [Projeto front end](#Projeto-frontend)
* [Time de desenvolvedoras](Time-de-desenvolvedoras)


## Sobre o projeto

Este projeto foi desenvolvido na disciplina de Laboratório de Software, do curso de Análise e Desenvolvimento de Sistemas da UCS, no primeiro semestre de 2022, tendo como escopo a criação de uma ferramenta de scout para avaliar jogadores de badminton.


## :hammer: Funcionalidades do projeto

- `Funcionalidade 1`: cadastrar e listar jogadores
- `Funcionalidade 2`: cadastrar e listar partida
- `Funcionalidade 3`: iniciar partida e gravar jogadas
- `Funcionalidade 4`: exibir relatório de desempenho do jogador na partida


## Principais tecnologias utilizadas
![download-icon-postgresql](https://user-images.githubusercontent.com/64370426/178146790-8b3d4bf8-e1db-4adf-a803-357f6a795637.png)

![Python](https://user-images.githubusercontent.com/64370426/178148552-27694dbc-9a49-487c-910a-c89ea1c96a49.png)
![Flask svg](https://user-images.githubusercontent.com/64370426/178146832-f8ee15bd-4b01-4227-a2e7-ff6a81fae06d.png)

![nodejs_logo](https://user-images.githubusercontent.com/64370426/178148545-ee01eed4-0093-4566-8a79-8e57f78904cc.png)
![Angular_ svg](https://user-images.githubusercontent.com/64370426/178146928-20b84988-d027-44ac-bb81-a316ae3d9708.png)

## Como usar

### Projeto backend:
#### Requisitos:
* Instalação do PostgreSQL (a partir da versão 13.3)
> https://www.postgresql.org/
 
* Instalação do Python (a partir da versão 3.9)
> https://www.python.org/

* Instalação do Git
> https://git-scm.com/book/pt-br/v2/Come%C3%A7ando-Instalando-o-Git
 
* Instalar uma plataforma de teste de APIs - sugestão: Postman
> https://www.postman.com/

#### Criar Data Base:
Pegar todos os scripts necessários no diretório e executálos na ordem indicada
> https://github.com/csdamo/sql_badminton

##### Ao rodar esses scripts você terá:
* Criado o Data Base
* Criado as tabelas
* Inserido os dados necessários para o projeto


#### Clonando projeto para máquina local:

* Criar repositório onde será mantido o projeto. 
> Ex.: C:\Users\seunome\desenv\badmintonapi

* No git bash, executar o comando:
```
git clone https://github.com/csdamo/badmintonapi
```

  
#### Criando ambiente virtual de desenvolvimento:

* No prompt de comando, executar o comando
```
pip install virtualenv
```

* Pelo prompt, vá até o diretório do projeto e execute o comando a seguir. Será criada uma pasta dentro do repositório com o nome "venv"
```
virtualenv venv
``` 


* Ative o ambiente virtual de desenvolvimento: ainda no prompt de comando (dentro do repositório do projeto) execute o comando
```
venv/Scripts/activate 
```
(Windows) 
```
source venv/bin/activate
```
(Linux) 

* Para você saber se o ambiente virtual foi ativado, perceba se antes do caminho do seu diretório, aparece o nome do ambiente entre parênteses. 
> Ex.: (venv) C:\Users\seunome\desenv\badmintonapi>

  

#### Iniciando a configuração do projeto Flask 

* Dentro do ambiente virtual, para instalar as bibliotecas na versão correta para o projeto , rodar o comando
```
pip install -r requirements.txt
```


* Configurar o arquivo **apibadminton.json** com os dados do Data base criado para o projeto

#### Subindo o servidor:

* No prompt de comando, com o ambiente virtual ativado, executar o arquivo **apibadminton.py** para subir o servidor



### Projeto frontend:
#### Requisitos:
##### Para iniciar o projeto na máquina local, será necessário fazer a instalação do node, npm e angular, nas seguintes versões e links:
> Node versão 14.17.3 https://nodejs.org/en/blog/release/v14.17.3/

> npm versão 8.5.0 https://www.npmjs.com/package/npm/v/8.5.0

> Angular versão 13.3.3 https://angular.io/guide/setup-local 

#### Instruções completas no repositório:
> https://github.com/clhobus013/scout-badminton

## Demonstração




https://user-images.githubusercontent.com/64370426/178149399-72120908-864c-4469-bce2-a4cb7dd7538c.mp4



## Time de desenvolvedoras

Claudia Hobus - 
Cristiane Sebem Damo - 
Maitê Bueno
