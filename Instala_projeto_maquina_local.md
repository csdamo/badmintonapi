## Instalação do projeto na máquina local:

### Requisitos na máquina local:

* Instalação do PostgreSQL: https://www.postgresql.org/

  * site oficial do PostgreSQL: https://www.postgresql.org/
  * vídeo passo a passo da instalação: https://www.youtube.com/watch?v=His77sqWfGU

* Instalação do Python (a partir da versão 3.9 ):

  * site oficial do python: https://www.python.org/
  * vídeo passo a passo da instalação: https://www.youtube.com/watch?v=pDBnCDuL-dc

* Instalação do Git:

  * site oficial do Git: https://git-scm.com/book/pt-br/v2/Come%C3%A7ando-Instalando-o-Git
  * vídeo passo a passo da instalação: https://www.youtube.com/watch?v=ONztz-yh4jY

* Instalar uma plataforma de teste de APIs - sugestão: Postman

  

### Clonando projeto para máquina local:

* Criar repositório onde será mantido o projeto. Ex.: C:\Users\seunome\desenv\badmintonapi

* No git bash, executar o comando: **git clone https://github.com/csdamo/badmintonapi**

  

### Criando ambiente virtual de desenvolvimento:

* No prompt de comando, executar o comando: **pip install virtualenv** (caso ainda não o tenha instalado)

* Pelo prompt, vá até o diretório do projeto e execute o comando: **virtualenv venv** - ele criará uma pasta dentro do repositório com o nome "venv"

* Agora, é possível ativar o ambiente virtual de desenvolvimento: ainda no prompt de comando (dentro do repositório do projeto) execute o comando: **venv/Scripts/activate** (Windows) ou **source venv/bin/activate** (Linux) 

* Para você saber se o ambiente virtual foi ativado, perceba se antes do caminho do seu diretório, aparece o nome do ambiente entre parênteses. Ex.: (venv) C:\Users\seunome\desenv\badmintonapi>

  

### Iniciando a configuração do projeto Flask 

* Dentro do ambiente virtual, rodar o comando **pip install -r requirements.txt** para instalar os pacotes na versão correta para o projeto 
* Baixar o arquivo **apibadminton.json** do projeto dentro do diretório do projeto basmintonapi - o arquivo apibadminton.json não ficará junto com o projeto no GitHub pois possui a senha do banco de dados
* Exemplo de configuração:

{

  "SECRET_KEY":"xxxxxxxxxxxx",

  "DATABASE_HOST":"127.0.0.1",

  "DATABASE_NAME":"nomebancodados",

  "DATABASE_USER":"usuariopostgres",

  "DATABASE_PASSWORD":"senhapostgres",

  "URLMEDIA":"C:/Users/seunome/desenv/badmintonbd/media",

  "UPLOAD_URL":"C:/Users/seunome/desenv/badmintonbd/media",

  "UPLOAD_PATH":"C:/Users/seunome/desenv/badmintonbd/media"

 }

### Subindo o servidor:

- No prompt de comando, com o ambiente virtual ativado, executar o arquivo apibadminton.py para subir o servidor



