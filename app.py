from flask import Flask, request, jsonify, make_response, render_template
import psycopg2
import datetime
from functools import wraps
from jsonschema import validate, ValidationError, SchemaError
import json
import logging
import logging.handlers
import warnings
import locale
import requests

from threading import Thread

from flask_cors import CORS

import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
CORS(app)


@app.route('/post_jogador', methods=['POST'])
def post_jogador():
    """ Cria registro de um jogador no banco de dados """

    data = request.get_json()

    if not data:
        return jsonify({'erro' : 'JSON inválido.'})

    schema = {
        "type": "object",
        "required": [ "nome", "data_nascimento", "telefone", "email", "lateralidade", "foto"],
        "properties": {
            "nome": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200
            },
            "data_nascimento": {
                "type": "string",
                "format": "date"
            },
            "telefone": {
                "type": "string",
                "minLength": 0,
                "maxLength": 12
            },
            "email": {
                "type": "string",
                "minLength": 0,
                "maxLength": 100
            },
            "lateralidade": {
                "type": "string",
                "enum": ["naoinformado", "destro", "canhoto", "ambidestro"]
            },

            "foto": {
                "type": "string",
                "minLength": 0,
            }
          }
        }

    #Verifica se Json é valido (conforme Json-schema).
    try:
        validate(data, schema)

    except ValidationError as e:
        mensagem = 'JSON inválido.' + ' - Path: ' + str(e.path)  + ' - Message: ' + str(e.message)
        return jsonify({'erro' : mensagem})

    # verifica se nome já está cadastrado
    nome = data["nome"]

    bloco = " select jogador.id, jogador.nome_jogador from jogador where jogador.nome_jogador = %s"
    sqlvar = (nome,)
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        jogador_data = cursor.fetchone()

        if jogador_data:
            return jsonify({'mensagem' : 'Jogador já cadastrado'})


    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    # variáveis com os dados a serem salvos
    data_nascimento = data["data_nascimento"]
    telefone = data["telefone"]
    email = data["email"]
    lateralidade = data["lateralidade"]
    foto = 'jogador/' + data["foto"]  # ainda não implementado
    datetimenow = datetime.datetime.now()
    
    # Insert no banco de dados
    tupla = (nome, data_nascimento, telefone, email, lateralidade, foto, datetimenow, datetimenow)
    bloco = ("insert into jogador (nome_jogador, data_nascimento, telefone, \
                email, lateralidade, foto, criado_em, atualizado_em) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
                returning id, nome_jogador, data_nascimento, telefone, \
                email, lateralidade, foto ")
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, tupla)
        data_jogador = cursor.fetchone()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()
    
    # Dados a serem retornados após salvamento do registro
    jogador= {}
    if data_jogador:
        jogador['id'] = data_jogador[0]
        jogador['nome'] = data_jogador[1]
        jogador['data_nascimento'] = data_jogador[2].strftime('%d-%m-%Y')
        jogador['telefone'] = data_jogador[3]
        jogador['email'] = data_jogador[4]
        jogador['lateralidade'] = data_jogador[5]
        jogador['foto'] = data_jogador[6]
    
    return jsonify({'Jogador' : jogador})


@app.route('/get_jogador', methods=['GET'])
def get_jogador():
    """ Devolve dados do jogador conforme id informado - esta rota pode ser substituida pela rota get_jogadores """

    # verifica parâmetro recebido
    id_jogador = None
    
    if request.args.get('id_jogador'):
        id_jogador = request.args.get('id_jogador')  
    
    if not id_jogador:
        id_jogador = '0'
    
    if not id_jogador.isdigit():
        return jsonify({'erro' : 'request.args[id_jogador] deve ser numerico'})

    # Pesquisa jogador conforme id informado no parâmetro
    bloco = " select jogador.id, jogador.nome_jogador, jogador.data_nascimento, jogador.telefone, \
                jogador.email, jogador.lateralidade, jogador.foto \
                from jogador where jogador.id = %s"
    sqlvar = (id_jogador,)
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        jogadore_data = cursor.fetchone()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()
    
    # Devolve dados do jogador pesquisado
    lineout_jogador = {}
    if jogadore_data:    
        lineout_jogador['id'] = jogadore_data[0]
        lineout_jogador['nome'] = jogadore_data[1]
        lineout_jogador['data_nascimento'] = jogadore_data[2].strftime('%d-%m-%Y')
        lineout_jogador['telefone'] = jogadore_data[3]
        lineout_jogador['email'] = jogadore_data[4]
        lineout_jogador['lateralidade'] = jogadore_data[5]
        foto = jogadore_data[6]
        if foto:
            lineout_jogador['foto'] = ''
        else:
            lineout_jogador['foto'] = ''

    return jsonify({'badminton' : lineout_jogador})


@app.route('/get_jogadores', methods=['GET'])
def get_jogadores():
    """ Devolve dados do(s) jogadore(s) conforme id(s) informado(s) 
        ou devolve todos os jogadores caso parametro esteja vazio"""

    # verifica parâmetro recebido
    lista_id_jogador = None
    
    if request.args.get('lista_id_jogador'):
        lista_id_jogador = (request.args.get('lista_id_jogador')).replace(" ", "").split(',')
        
        for jogador in lista_id_jogador:
            if not jogador.isdigit():
                return jsonify({'erro' : 'request.args[lista_id_jogador] deve ser numerico'})

    if not lista_id_jogador:
        lista_id_jogador = '0'

    # Pesquisa jogadores conforme ids informados no parâmetro
    posicao = 0
    blocoi = " select jogador.id, jogador.nome_jogador, jogador.data_nascimento, jogador.telefone, \
                jogador.email, jogador.lateralidade, jogador.foto \
                from jogador "
    blocof = ""
    tupla = ()
 
    if lista_id_jogador != '0':
        for jogador_id in lista_id_jogador:
            if posicao == 0:
                blocof = " where jogador.id = %s "
                tupla = (jogador_id,)
                posicao += 1
            else:
                blocof = blocof + " or jogador.id = %s "
                tupla = (tupla) + (jogador_id,)
    
    bloco = blocoi + blocof
    
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, tupla)
        jogadores_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    # Devolve dados dos jogadores pesquisado
    output_jogadores = []
    if jogadores_data:
        for line in jogadores_data:
            lineout_jogador = {}
            lineout_jogador['id'] = line[0]
            lineout_jogador['nome'] = line[1]
            lineout_jogador['data_nascimento'] = line[2].strftime('%d-%m-%Y')
            lineout_jogador['telefone'] = line[3]
            lineout_jogador['email'] = line[4]
            lineout_jogador['lateralidade'] = line[5]
            foto = line[6]
            if foto:
                lineout_jogador['foto'] = ''
            else:
                lineout_jogador['foto'] = ''

            output_jogadores.append(lineout_jogador)

    return jsonify({'jogadores_badminton' : output_jogadores})


@app.route('/upload_file', methods=['POST'])
def upload_file():
    """ Faz upload de arquivo para repositório """

    # Verifica se arquivo foi carregado
    if 'file' not in request.files:
        return jsonify({'erro' : 'Arquivo não carregado'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'erro' : 'Arquivo não carregado'})

    if file:
        unique_name = str(uuid.uuid4().hex) + file.filename  # Atribui um nome único ao arquivo
        filename = secure_filename(unique_name)  # Verifica a segurança do nome do arquivo
        file.save(os.path.join(config['UPLOAD_PATH'], filename))  # Salva arquivo em repositório remoto

        url_file_uploaded = config['UPLOAD_URL'] + '/' + filename

        # Devolve o nome do arquivo para ser salvo no banco de dados
        lineout = {}
        lineout['nome_arquivo'] = filename
        return jsonify({'mensagem' : lineout})


@app.route('/get_golpes', methods=['GET'])
def get_golpes():
    """ Devolve lista de golpes de badminton """
    
    # Pesquisa todos os golpes de badminton cadastrados
    bloco = " select golpe.id, golpe.descricao_golpe from golpe "
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco)
        golpe_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()
    # Devolve lista com dados dos golpes de badminton
    output = {}
    output_golpe = []
    if golpe_data:
        for line in golpe_data:
            lineout_golpe = {}
            lineout_golpe['id'] = line[0]
            lineout_golpe['descricao'] = line[1]
        
            output_golpe.append(lineout_golpe)

    output['golpes'] = output_golpe
    # Pesquisa tipos de erros de golpe
    bloco = " select tipoerro.id, tipoerro.descricao_erro from tipoerro "
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco)
        erro_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    # Devolve lista com tipos de erros de golpe
    output_erro = []
    if erro_data:
        for line in erro_data:
            lineout_erro = {}
            lineout_erro['id_erro'] = line[0]
            lineout_erro['descricao'] = line[1]
        
            output_erro.append(lineout_erro)
    output['tipo_erros'] = output_erro
    return jsonify({'golpes_badminton' : output})


@app.route('/get_tipoerro', methods=['GET'])
def get_tipoerro():
    """ Devolve lista de erros de golpe """
    
    # Pesquisa tipos de erros de golpe
    bloco = " select tipoerro.id, tipoerro.descricao_erro from tipoerro "
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco)
        erro_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    # Devolve lista com tipos de erros de golpe
    output_erro = []
    if erro_data:
        for line in erro_data:
            lineout_erro = {}
            lineout_erro['id_erro'] = line[0]
            lineout_erro['descricao'] = line[1]
        
            output_erro.append(lineout_erro)
    return jsonify({'tipo_erros' : output_erro})


@app.route('/get_quadrantes', methods=['GET'])
def get_quadrantes():
    """ Devolve lista de quadrantes """
    
    # Pesquisa tods os quadrantes cadastrados
    bloco = " select quadrante.id, quadrante.descricao_quadrante, quadrante.lado \
                 from quadrante "
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco)
        quadrante_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    # Devolve lista com dados dos quadrantes
    output_quadrante = []
    if quadrante_data:
        for line in quadrante_data:
            lineout_quadrante = {}
            lineout_quadrante['id'] = line[0]
            lineout_quadrante['descricao'] = line[1]
            lineout_quadrante['lado'] = line[2]
        
            output_quadrante.append(lineout_quadrante)
    
    return jsonify({'quadrantes' : output_quadrante})


@app.route('/post_partida', methods=['POST'])
def post_partida():
    """ Cria registro da partida no banco de dados """
    
    data = request.get_json()

    if not data:
        return jsonify({'erro' : 'JSON inválido.'})

    data['jogador_2'] = 0
    data['jogador_adversario_2'] = 0
   
            
    schema = {
        "type": "object",
        "required": ["nome", "data", "tipo_jogo", "modalidade", "jogador_1", "jogador_2", "jogador_adversario_1",  "jogador_adversario_2"],
        "properties": {
            "nome": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200
            },
            "data": {
                "type": "string",
                "format": "date"
            },
            "tipo_jogo": {
                "type": "string",
                "enum": ["simples", "dupla"]
            },
            "modalidade": {
                "type": "string",
                "enum": ["misto", "feminino", "masculino"]
            },
            "jogador_1": {
                "type": "integer",
                "minimum": 1,
                "exclusiveMaximum": 999999999
            },
            "jogador_2": {
                "type": "integer",
            },
            "jogador_adversario_1": {
                "type": "integer",
                "minimum": 1,
                "exclusiveMaximum": 999999999
            },
            "jogador_adversario_2": {
                "type": "integer",
            }
        }
    }

    #Verifica se Json é valido (conforme Json-schema).
    try:
        validate(data, schema)

    except ValidationError as e:
        mensagem = 'JSON inválido.' + ' - Path: ' + str(e.path)  + ' - Message: ' + str(e.message)
        return jsonify({'erro' : mensagem})

    # Variáveis com os dados a serem salvos
    nome = data["nome"]
    data_partida = data["data"]
    tipo_jogo = data["tipo_jogo"]
    modalidade = data["modalidade"]
    jogador_1 = data["jogador_1"]
    jogador_adversario_1 = data["jogador_adversario_1"]
    datetimenow = datetime.datetime.now()

    if tipo_jogo == 'simples':
        jogador_2 = None
        jogador_adversario_2 = None
    
    else:
        jogador_2 = data["jogador_2"]
        jogador_adversario_2 = data["jogador_adversario_2"]
        if jogador_2 == 0:
            jogador_2 = None
        if jogador_adversario_2 == 0:
            jogador_adversario_2 = None

    # Insert no banco de dados
    sqlvar = (nome, data_partida, tipo_jogo, modalidade, jogador_1, jogador_2, jogador_adversario_1, jogador_adversario_2, datetimenow, datetimenow)

    bloco = ("insert into partida (nome, data_partida, tipo_jogo, modalidade, jogador_1_id, jogador_2_id, \
                 jogador_adversario_1_id, jogador_adversario_2_id, criado_em, atualizado_em) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                    returning id, nome, data_partida, tipo_jogo, modalidade, jogador_1_id, jogador_2_id, \
                 jogador_adversario_1_id, jogador_adversario_2_id")

    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        data_partida = cursor.fetchone()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()

    # Dados a serem retornados após salvamento do registro
    partida = {}
    if data_partida:
        partida['partida_id'] = data_partida[0]
        partida['nome'] = data_partida[1]
        partida['data'] = (data_partida[2]).strftime('%d-%m-%Y')
        partida['tipo_jogo'] = data_partida[3]
        partida['modalidade'] = data_partida[4]
        partida['jogador_1_id'] = data_partida[5]
        partida['jogador_2_id'] = data_partida[6]
        partida['jogador_adversario_1_id'] = data_partida[7]
        partida['jogador_adversario_2_id'] = data_partida[8]

    return jsonify({'partida' : partida})


@app.route('/get_partida', methods=['GET'])
def get_partida():
    """ Devolve dados da partida conforme id informado - esta rota pode ser substituida pela rota get_partidas """

    # verifica parâmetro recebido
    id_partida = None
    
    if request.args.get('id_partida'):
        id_partida = request.args.get('id_partida')
        
    if not id_partida:
        id_partida = '0'

    if not id_partida.isdigit():
        return jsonify({'erro' : 'request.args[id_partida] deve ser numerico'})


    # Pesquisa partida conforme id informado no parâmetro
    bloco = " select partida.id, partida.data_partida, partida.tipo_jogo, partida.modalidade, partida.nome, \
                partida.jogador_1_id, partida.jogador_2_id, partida.jogador_adversario_1_id, partida.jogador_adversario_2_id \
                from partida where partida.id = %s"

    sqlvar = (id_partida,)
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        partida_data = cursor.fetchone()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    if partida_data:
        # Pesquisa jogadores da partida
        bloco = " select jogador.nome_jogador, jogador.id  \
                from jogador where id = %s or id = %s  or id = %s  or id = %s " 
                    
        tupla = (partida_data[5], partida_data[6], partida_data[7], partida_data[8])

        try:
            connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
            cursor = connection.cursor()
            cursor.execute(bloco, tupla)
            jogador_data = cursor.fetchall()

        except (Exception, psycopg2.Error) as error:
            erro = str(error).rstrip()
            erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
            return jsonify({'erro' : erro_banco})

        finally:
            if (connection):
                cursor.close()
                connection.close()


    # Devolve dados da partida pesquisada
    lineout_partida = {}
    if partida_data:
        id_partida = partida_data[0] 
        lineout_partida['id'] = partida_data[0]
        lineout_partida['data'] = partida_data[1].strftime('%d-%m-%Y')
        lineout_partida['tipo_jogo'] = partida_data[2]
        lineout_partida['modalidade'] = partida_data[3]
        lineout_partida['nome'] = partida_data[4]
        
        # Insere dados do jogador: uma partida pode ter dois ou quatro jogadores
        lineout_partida['jogador_1'] = {
            'nome': (jogador_data[0])[0],
            'id': (jogador_data[0])[1],
        }

        if (len(jogador_data)) == 4:
            pass
            
            lineout_partida['jogador_2'] = {
                'nome': (jogador_data[1])[0],
                'id': (jogador_data[1])[1],
            }
            lineout_partida['jogador_adversario_1'] = {
                'nome': (jogador_data[2])[0],
                'id': (jogador_data[2])[1],
                }
            lineout_partida['jogador_adversario_2'] = {
                'nome': (jogador_data[3])[0],
                'id': (jogador_data[3])[1],
            }
        
        elif (len(jogador_data)) == 2:
            lineout_partida['jogador_2'] = {}
            lineout_partida['jogador_adversario_1'] = {
                'nome': (jogador_data[1])[0],
                'id': (jogador_data[1])[1],

            }
            lineout_partida['jogador_adversario_2'] = {}

        # Pesquisa os sets da partida
        bloco = " select set.id, set.ordem from set where set.partida_id = %s "

        sqlvar = (id_partida,)
                    
        try:
            connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
            cursor = connection.cursor()
            cursor.execute(bloco, sqlvar)
            set_ordem_data = cursor.fetchall()
            

        except (Exception, psycopg2.Error) as error:
            erro = str(error).rstrip()
            erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
            return jsonify({'erro' : erro_banco})

        finally:
            if (connection):
                cursor.close()
                connection.close()

        # Devolve os sets relacionados à partida pesquisada
        output_set = []
        if set_ordem_data:
            for set_data in set_ordem_data:
                set_partida = {}
                id_set = set_data[0]
                set_partida['id_set'] = id_set
                set_partida['ordem_set'] = set_data[1]


                # Pesquisa as jogadas dos sets da partida
                sqlvar = (id_set,)

                bloco = (" select count(acerto), acerto from jogada where set_id =%s  group by acerto; ")
                
                try:
                    connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                    cursor = connection.cursor()
                    cursor.execute(bloco, sqlvar)
                    acertos = cursor.fetchall()
                
                except (Exception, psycopg2.Error) as error:
                    erro = str(error).rstrip()
                    erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                    return jsonify({'erro' : erro_banco})

                finally:
                    if (connection):
                        connection.commit()
                        cursor.close()
                        connection.close()

                # Devolve pontuação e verifica se o jogo deve continuar ou parar
                if acertos:
                    quantidade_resultado1 =  (acertos[0])[0]
                    tipo_resultado1 = (acertos[0])[1]

                    if tipo_resultado1:
                        qtd_acertos = quantidade_resultado1
                        qtd_erros = 0
                    else:
                        qtd_erros = quantidade_resultado1
                        qtd_acertos = 0

                    if len(acertos) == 2:
                        quantidade_resultado2 =  (acertos[1])[0]
                        tipo_resultado2 = (acertos[1])[1]
                        if tipo_resultado2:
                            qtd_acertos = quantidade_resultado2
                        else:
                            qtd_erros = quantidade_resultado2

                else:
                    qtd_erros = 0
                    qtd_acertos = 0
                            
                diferenca_erro_acerto = abs(qtd_erros - qtd_acertos)
            
                if qtd_erros > qtd_acertos:
                    set_partida['resultado_set'] = 'perdeu'
                elif qtd_erros < qtd_acertos:
                    set_partida['resultado_set'] = 'ganhou'
                else:
                    set_partida['resultado_set'] = 'empate'

                set_partida['status'] = 'continuar'
                if (qtd_erros >= 21 or qtd_acertos >= 21):
                    if diferenca_erro_acerto >= 2:
                        set_partida['status'] = 'parar'
                    else:
                        if (qtd_erros >= 30 or qtd_acertos >= 30):
                            set_partida['status'] = 'parar'

                set_partida['erros'] = qtd_erros
                set_partida['acertos'] = qtd_acertos
                
                output_set.append(set_partida)

        lineout_partida['sets'] = output_set

    return jsonify({'partida_badminton' : lineout_partida})


@app.route('/get_partidas', methods=['GET'])
def get_partidas():
    """ Devolve dados da(s) partidas(s) conforme id(s) informado(s) 
    ou devolve todas as partidas caso parametro esteja vazio"""
    
    # Verifica parâmetro recebido
    lista_id_partida = None
    if request.args.get('lista_id_partida'):
        lista_id_partida = (request.args.get('lista_id_partida')).replace(" ", "").split(',')
        
        for partida in lista_id_partida:
            if not partida.isdigit():
                return jsonify({'erro' : 'request.args[lista_id_partida] deve ser numerico'})

    if not lista_id_partida:
        lista_id_partida = '0'
    
    # Pesquisa partidas conforme ids informado no parâmetro
    posicao = 0
    blocoi = " select partida.id, partida.data_partida, partida.tipo_jogo, partida.modalidade, partida.nome, \
                partida.jogador_1_id, partida.jogador_2_id, partida.jogador_adversario_1_id, partida.jogador_adversario_2_id \
                  from partida " 
                
    blocof = ""
    tupla = ()
 
    if lista_id_partida != '0':
        for partida_id in lista_id_partida:
            if posicao == 0:
                blocof = " where partida.id = %s "
                tupla = (partida_id, )
                posicao += 1
            else:
                blocof = blocof + " or partida.id = %s "
                tupla = (tupla) + (partida_id, )
    
    bloco = blocoi + blocof

    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, tupla)
        partidas_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()
    
    # Devolve dados das partidas pesquisadas
    output_partidas = []
    if partidas_data:
        for line in partidas_data:

            # Pesquisa dados do jogador
            #bloco = " select jogador.nome_jogador, jogador.id, jogador.data_nascimento, jogador.telefone, \
            #            jogador.email, jogador.lateralidade \
            #        from jogador where id = %s or id = %s  or id = %s  or id = %s    " 
          
            # Pesquisa dados do jogador
            bloco = " select jogador.nome_jogador, jogador.id  \
                    from jogador where id = %s or id = %s  or id = %s  or id = %s " 
                        
            tupla = (line[5], line[6], line[7], line[8])
            try:
                connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                cursor = connection.cursor()
                cursor.execute(bloco, tupla)
                jogador_data = cursor.fetchall()

            except (Exception, psycopg2.Error) as error:
                erro = str(error).rstrip()
                erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                return jsonify({'erro' : erro_banco})

            finally:
                if (connection):
                    cursor.close()
                    connection.close()
            lineout_partida = {}
            id_partida = line[0]
            lineout_partida['id'] = line[0]
            lineout_partida['data'] = line[1].strftime('%d-%m-%Y')
            lineout_partida['tipo_jogo'] = line[2]
            lineout_partida['modalidade'] = line[3]
            lineout_partida['nome'] = line[4]

            # Insere dados do jogador: uma partida pode ter dois ou quatro jogadores
            lineout_partida['jogador_1'] = {
                'nome': (jogador_data[0])[0],
                'id': (jogador_data[0])[1],
                #'data_nascimento': (jogador_data[0])[2],
                #'telefone': (jogador_data[0])[3],
                #'email': (jogador_data[0])[4],
                #'lateralidade': (jogador_data[0])[5],
            }

            if (len(jogador_data)) == 4:
                
                lineout_partida['jogador_2'] = {
                    'nome': (jogador_data[1])[0],
                    'id': (jogador_data[1])[1],
                    #'data_nascimento': (jogador_data[1])[2],
                    #'telefone': (jogador_data[1])[3],
                    #'email': (jogador_data[1])[4],
                    #'lateralidade': (jogador_data[1])[5],
                }
                lineout_partida['jogador_adversario_1'] = {
                    'nome': (jogador_data[2])[0],
                    'id': (jogador_data[2])[1],
                    #'data_nascimento': (jogador_data[2])[2],
                    #'telefone': (jogador_data[2])[3],
                    #'email': (jogador_data[2])[4],
                    #'lateralidade': (jogador_data[2])[5],
                    }
                lineout_partida['jogador_adversario_2'] = {
                    'nome': (jogador_data[3])[0],
                    'id': (jogador_data[3])[1],
                    #'data_nascimento': (jogador_data[3])[2],
                    #'telefone': (jogador_data[3])[3],
                    #'email': (jogador_data[3])[4],
                    #'lateralidade': (jogador_data[3])[5],
                }
            
            elif (len(jogador_data)) == 2:
                lineout_partida['jogador_2'] = {}
                lineout_partida['jogador_adversario_1'] = {
                    'nome': (jogador_data[1])[0],
                    'id': (jogador_data[1])[1],
                    #'data_nascimento': (jogador_data[1])[2],
                    #'telefone': (jogador_data[1])[3],
                    #'email': (jogador_data[1])[4],
                    #'lateralidade': (jogador_data[1])[5],
                }
                lineout_partida['jogador_adversario_2'] = {}
                
            # lineout_partida['jogador_1'] = line[5]
            # lineout_partida['jogador_2'] = line[6]
            # lineout_partida['jogador_adversario_1'] = line[7]
            # lineout_partida['jogador_adversario_2'] = line[8]

            # Pesquisa os sets da partida
            bloco = " select set.id, set.ordem from set where set.partida_id = %s "

            sqlvar = (id_partida,)
                        
            try:
                connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                cursor = connection.cursor()
                cursor.execute(bloco, sqlvar)
                set_ordem_data = cursor.fetchall()
                

            except (Exception, psycopg2.Error) as error:
                erro = str(error).rstrip()
                erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                return jsonify({'erro' : erro_banco})

            finally:
                if (connection):
                    cursor.close()
                    connection.close()

            # Devolve os sets relacionados às partidas pesquisadas
            output_set = []
            if set_ordem_data:
                for set_data in set_ordem_data:
                    set_partida = {}
                    id_set = set_data[0]
                    set_partida['id_set'] = set_data[0]
                    set_partida['ordem_set'] = set_data[1]

            
                    # Pesquisa as jogadas dos sets da partida
                    sqlvar = (id_set,)

                    bloco = (" select count(acerto), acerto from jogada where set_id =%s  group by acerto; ")
                    
                    try:
                        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                        cursor = connection.cursor()
                        cursor.execute(bloco, sqlvar)
                        acertos = cursor.fetchall()
                    
                    except (Exception, psycopg2.Error) as error:
                        erro = str(error).rstrip()
                        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                        return jsonify({'erro' : erro_banco})

                    finally:
                        if (connection):
                            connection.commit()
                            cursor.close()
                            connection.close()

                    # Devolve pontuação e verifica se o jogo deve continuar ou parar
                    
                    if acertos:
                        quantidade_resultado1 =  (acertos[0])[0]
                        tipo_resultado1 = (acertos[0])[1]

                        if tipo_resultado1:
                            qtd_acertos = quantidade_resultado1
                            qtd_erros = 0
                        else:
                            qtd_erros = quantidade_resultado1
                            qtd_acertos = 0

                        if len(acertos) == 2:
                            quantidade_resultado2 =  (acertos[1])[0]
                            tipo_resultado2 = (acertos[1])[1]
                            if tipo_resultado2:
                                qtd_acertos = quantidade_resultado2
                            else:
                                qtd_erros = quantidade_resultado2
    
                    else:
                        qtd_erros = 0
                        qtd_acertos = 0
                    diferenca_erro_acerto = abs(qtd_erros - qtd_acertos)
                
                    if qtd_erros > qtd_acertos:
                        set_partida['resultado_set'] = 'perdeu'
                    elif qtd_erros < qtd_acertos:
                        set_partida['resultado_set'] = 'ganhou'
                    else:
                        set_partida['resultado_set'] = 'empate'

                    set_partida['status'] = 'continuar'
                    if (qtd_erros >= 21 or qtd_acertos >= 21):
                        if diferenca_erro_acerto >= 2:
                            set_partida['status'] = 'parar'
                        else:
                            if (qtd_erros >= 30 or qtd_acertos >= 30):
                                set_partida['status'] = 'parar'

                    set_partida['erros'] = qtd_erros
                    set_partida['acertos'] = qtd_acertos
                    
                    output_set.append(set_partida)

            lineout_partida['sets'] = output_set
            output_partidas.append(lineout_partida)

    return jsonify({'partidas_badminton' : output_partidas})


@app.route('/post_set', methods=['POST'])
def post_set():
    """ Cria registro do set no banco de dados """

    # Verifica parâmetros de entrada
    id_partida = None
    
    if request.args.get('id_partida'):
        id_partida = request.args.get('id_partida')
        
    if not id_partida:
        id_partida = '0'

    if not id_partida.isdigit():
        return jsonify({'erro' : 'request.args[id_partida] deve ser numerico'})

    ordem_set = None
    
    if request.args.get('ordem_set'):
        ordem_set = request.args.get('ordem_set')
        
    if not ordem_set:
        ordem_set = '0'

    if not ordem_set.isdigit():
        return jsonify({'erro' : 'request.args[ordem_set] deve ser numerico'})
    
    # Realiza insert no banco de dados
    datetimenow = datetime.datetime.now()
    sqlvar = (id_partida, ordem_set, datetimenow, datetimenow)

    bloco = ("insert into set (partida_id, ordem, criado_em, atualizado_em) \
            VALUES (%s, %s, %s, %s) \
            returning id, partida_id, ordem ")

    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        set_data = cursor.fetchone()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()

    # Devolve dados do set recém salvo
    data_set = {}
    if set_data:
        data_set['set_id'] = set_data[0]
        data_set['partida_id'] = set_data[1]
        data_set['ordem_set'] = set_data[2]

    return jsonify({'set_criado' : data_set})


@app.route('/post_jogada', methods=['POST'])
def post_jogada():
    """ Cria registro de jogada no banco de dados """

    data = request.get_json()

    if not data:
        return jsonify({'erro' : 'JSON inválido.'})

    schema = {
        "type": "object",
        "required": ["set", "golpe", "quadrante", "acerto"],
        "properties": {
            "set": {
                "type": "integer",
                "minimum": 1,
                "exclusiveMaximum": 999999999
            },
            "golpe": {
                "type": "integer",
                "minimum": 1,
                "exclusiveMaximum": 999999999
            },
            "quadrante": {
                "type": "integer",
                "minimum": 1,
                "exclusiveMaximum": 999999999
            },
            "tipoerro": {
                "type": "integer",
                "minimum": 0,
                "exclusiveMaximum": 999999999

            },
            "acerto": {
                "type": "boolean",
            }
          }
        }

    #Verifica se Json é valido (conforme Json-schema).
    try:
        validate(data, schema)

    except ValidationError as e:
        mensagem = 'JSON inválido.' + ' - Path: ' + str(e.path)  + ' - Message: ' + str(e.message)
        return jsonify({'erro' : mensagem})

    if data['tipoerro'] == 0:
        data['tipoerro'] = None
    
    # Realiza insert no banco de dados
    datetimenow = datetime.datetime.now()
    set_id = data['set']
    sqlvar = (set_id, data['golpe'], data['quadrante'], data['tipoerro'], data['acerto'], datetimenow, datetimenow)

    bloco = ("insert into jogada (set_id, golpe_id, quadrante_id, tipo_erro_id, acerto, criado_em, atualizado_em) \
            VALUES (%s, %s, %s, %s, %s, %s, %s) ")

    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()

    # Pesquisa as jogadas dos sets da partida
    sqlvar = (set_id,)

    bloco = (" select count(acerto), acerto from jogada where set_id =%s  group by acerto; ")
    
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        acertos = cursor.fetchall()
    
    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()
    # Devolve pontuação e verifica se o jogo deve continuar ou parar
    if acertos:
        quantidade_resultado1 =  (acertos[0])[0]
        tipo_resultado1 = (acertos[0])[1]

        if tipo_resultado1:
            qtd_acertos = quantidade_resultado1
            qtd_erros = 0
        else:
            qtd_erros = quantidade_resultado1
            qtd_acertos = 0

        
        if len(acertos) == 2:
            quantidade_resultado2 =  (acertos[1])[0]
            tipo_resultado2 = (acertos[1])[1]
            if tipo_resultado2:
                qtd_acertos = quantidade_resultado2
            else:
                qtd_erros = quantidade_resultado2

    else:
        qtd_erros = 0
        qtd_acertos = 0

    # Pesquisar ordem do set

    sqlvar = (set_id,)

    bloco = (" select ordem from set where id = %s  ")
    
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        ordem_set = cursor.fetchone()
    
    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()

    # Devolve pontuação e verifica se o jogo deve continuar ou parar
    data_pontuacao = {}
    
    data_pontuacao['set_id'] = data['set']
    data_pontuacao['ordem_set'] = ordem_set[0]


    diferenca_erro_acerto = abs(qtd_erros - qtd_acertos)
    
    if qtd_erros > qtd_acertos:
        data_pontuacao['resultado_set'] = 'perdendo'
    elif qtd_erros < qtd_acertos:
        data_pontuacao['resultado_set'] = 'ganhando'
    else:
        data_pontuacao['resultado_set'] = 'empatando'
    
    data_pontuacao['status'] = 'continuar'
    if (qtd_erros >= 21 or qtd_acertos >= 21):
        if diferenca_erro_acerto >= 2:
            data_pontuacao['status'] = 'parar'
        else:
            if (qtd_erros >= 30 or qtd_acertos >= 30):
                data_pontuacao['status'] = 'parar'

    data_pontuacao['erros'] = qtd_erros
    data_pontuacao['acertos'] = qtd_acertos

    return jsonify({'pontuacao_set': data_pontuacao})


@app.route('/get_set', methods=['GET'])
def get_set():
    """ Devolve todos os dados de um set e suas jogadas """

    # Verifica parâmetros de entrada
    id_set = None
    
    if request.args.get('id_set'):
        id_set = request.args.get('id_set')
        
    if not id_set:
        id_set = '0'

    if not id_set.isdigit():
        return jsonify({'erro' : 'request.args[id_set] deve ser numerico'})

    sqlvar = (id_set, )

    bloco = (" select set.id, set.partida_id, set.ordem from set where set.id = %s ")
    
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        data_set = cursor.fetchone()
    
    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()

    set_data = {}
    if data_set:
        set_id = data_set[0]
        set_data['set_id'] = data_set[0]
        set_data['partida_id'] = data_set[1]
        set_data['ordem'] = data_set[2] 

        
        # Pesquisa as jogadas dos sets da partida
        sqlvar = (set_id,)

        bloco = (" select count(acerto), acerto from jogada where set_id =%s  group by acerto; ")
        
        try:
            connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
            cursor = connection.cursor()
            cursor.execute(bloco, sqlvar)
            acertos = cursor.fetchall()
        
        except (Exception, psycopg2.Error) as error:
            erro = str(error).rstrip()
            erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
            return jsonify({'erro' : erro_banco})

        finally:
            if (connection):
                connection.commit()
                cursor.close()
                connection.close()
        # Devolve pontuação e verifica se o jogo deve continuar ou parar
        if acertos:
            quantidade_resultado1 =  (acertos[0])[0]
            tipo_resultado1 = (acertos[0])[1]

            if tipo_resultado1:
                qtd_acertos = quantidade_resultado1
                qtd_erros = 0
            else:
                qtd_erros = quantidade_resultado1
                qtd_acertos = 0

            if len(acertos) == 2:
                quantidade_resultado2 =  (acertos[1])[0]
                tipo_resultado2 = (acertos[1])[1]
                if tipo_resultado2:
                    qtd_acertos = quantidade_resultado2
                else:
                    qtd_erros = quantidade_resultado2

        else:
            qtd_erros = 0
            qtd_acertos = 0

        diferenca_erro_acerto = abs(qtd_erros - qtd_acertos)
       
        if qtd_erros > qtd_acertos:
            set_data['resultado_set'] = 'perdeu'
        elif qtd_erros < qtd_acertos:
            set_data['resultado_set'] = 'ganhou'
        else:
            set_data['resultado_set'] = 'empate'

        set_data['status'] = 'continuar'
        if (qtd_erros >= 21 or qtd_acertos >= 21):
            if diferenca_erro_acerto >= 2:
                set_data['status'] = 'parar'
            else:
                if (qtd_erros >= 30 or qtd_acertos >= 30):
                    set_data['status'] = 'parar'

        set_data['erros'] = qtd_erros
        set_data['acertos'] = qtd_acertos

    return jsonify({'data_set': set_data})


# versão 1
@app.route('/v1/get_relatoriopartida', methods=['GET'])
def get_relatoriopartida_v1():
    """ Retorna resultados da partida """

    # Verifica parâmetros de entrada
    id_partida = None
    
    if request.args.get('id_partida'):
        id_partida = request.args.get('id_partida')
        
    if not id_partida:
        id_partida = '0'

    if not id_partida.isdigit():
        return jsonify({'erro' : 'request.args[id_partida] deve ser numerico'})

    sqlvar = (id_partida, )

    # Pesquisa partida conforme id informado no parâmetro
    bloco = " select set.id, set.ordem, partida.id, partida.data_partida, partida.tipo_jogo, partida.modalidade, partida.nome, \
                partida.jogador_1_id, jogador.nome_jogador from set \
                inner join partida on (partida.id = set.partida_id)\
                inner join jogador on (partida.jogador_1_id = jogador.id) \
                where set.partida_id = %s"
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        partida_set_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    output_partida = []
    if partida_set_data:
        lineout_partida = {}
        lineout_partida['set_resultado'] = []
        
        set_resultado_global = []
        jogada_resultado_global = []

        jogadas_partida = 0
        acertos_partida = 0
        erros_partida = 0
        
        for line in partida_set_data:
            lineout_set = {}
            
            jogadas_set = 0
            acertos_set = 0
            erros_set = 0

            id_set = line[0]

            tupla = (id_set,)
            
            bloco = ("  SELECT jogada.golpe_id, jogada.quadrante_id, jogada.set_id, jogada.acerto, \
                        count(jogada.id) \
                        FROM jogada \
                        where set_id = %s GROUP BY (golpe_id, quadrante_id, set_id, acerto);")

            try:
                connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                cursor = connection.cursor()
                cursor.execute(bloco, tupla)
                dados_jogada = cursor.fetchall()
            
            except (Exception, psycopg2.Error) as error:
                erro = str(error).rstrip()
                erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                return jsonify({'erro' : erro_banco})

            finally:
                if (connection):
                    connection.commit()
                    cursor.close()
                    connection.close()
           
            if dados_jogada:
                for jogada in dados_jogada:

                    golpe_id = jogada[0]
                    quadrante_id = jogada[1]
                    set_id = jogada[2]
                    acerto_jogada = jogada[3]
                    quantidade_jogada = jogada[4]

                    jogadas_set = jogadas_set + quantidade_jogada

                    if acerto_jogada:
                        acertos_set = acertos_set + quantidade_jogada
                    else:
                        erros_set = erros_set + quantidade_jogada


                    tupla = (golpe_id,)
                    bloco = ("  SELECT golpe.descricao_golpe from golpe where golpe.id = %s ")

                    try:
                        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                        cursor = connection.cursor()
                        cursor.execute(bloco, tupla)
                        golpe = cursor.fetchone()
                    
                    except (Exception, psycopg2.Error) as error:
                        erro = str(error).rstrip()
                        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                        return jsonify({'erro' : erro_banco})

                    finally:
                        if (connection):
                            connection.commit()
                            cursor.close()
                            connection.close()
                    
                    tupla = (quadrante_id,)
                    bloco = ("  select quadrante.descricao_quadrante FROM quadrante \
                                where quadrante.id = %s ")

                    try:
                        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                        cursor = connection.cursor()
                        cursor.execute(bloco, tupla)
                        quadrante = cursor.fetchone()
                    
                    except (Exception, psycopg2.Error) as error:
                        erro = str(error).rstrip()
                        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                        return jsonify({'erro' : erro_banco})

                    finally:
                        if (connection):
                            connection.commit()
                            cursor.close()
                            connection.close()
                
                    golpe = golpe[0]
                    quadrante = quadrante[0]

                    jogada_tupla = (set_id, acerto_jogada, golpe_id, golpe, quadrante_id, quadrante, quantidade_jogada)    
                    jogada_resultado_global.append(jogada_tupla)


            jogadas_partida = jogadas_partida + jogadas_set
            acertos_partida = acertos_partida + acertos_set
            erros_partida = erros_partida + erros_set
            
            set_data = (line[0], line[1], jogadas_set, acertos_set, erros_set)
            set_resultado_global.append(set_data)
        if jogadas_partida > 0:
            # Dados da partida
            lineout_partida['partida_id'] = line[2]
            lineout_partida['data'] = line[3].strftime('%d-%m-%Y')
            lineout_partida['tipo_jogo'] = line[4]
            lineout_partida['modalidade'] = line[5]
            lineout_partida['nome'] = line[6]
            lineout_partida['jogador'] = line[8]

            # Resultados da partida
            lineout_partida['total_jogadas_partida'] = jogadas_partida
            lineout_partida['total_acertos_partida'] = acertos_partida
            lineout_partida['total_acertos_partida_%'] = round(((acertos_partida / jogadas_partida)*100), 2)
            lineout_partida['total_erros_partida'] = erros_partida
            lineout_partida['total_erros_partida_%'] = round(((erros_partida / jogadas_partida)*100), 2)
            
            if jogadas_partida > 0:
                for line_set in set_resultado_global:
                    set_resultado = {}
                    if line_set[2] > 0:
                        # Dados do set
                        id_set = line_set[0]
                        set_resultado['set_id'] = line_set[0]
                        set_resultado['set_ordem'] = line_set[1]

                        # Resultados individual do set
                        set_resultado['set_total_jogadas'] = line_set[2]
                        set_resultado['set_total_acertos'] = line_set[3]
                        set_resultado['set_acertos_relacao_set'] = round(((line_set[3] / line_set[2])*100), 2)
                        set_resultado['set_total_erros'] = line_set[4]
                        set_resultado['set_erros_relacao_set'] = round(((line_set[4] / line_set[2])*100), 2)
                        
                        # Resultados individual do set
                        set_resultado['set_total_relacao_partida'] = round(((line_set[2] / jogadas_partida)*100), 2)
                        set_resultado['set_acertos_relacao_partida'] = round(((line_set[3] / jogadas_partida)*100), 2)
                        set_resultado['set_erros_relacao_partida'] = round(((line_set[4] / jogadas_partida)*100), 2)
                        
                        set_resultado['jogadas'] = []
                        if line_set[2] > 0:
                            for line_jogada in jogada_resultado_global:
                                jogada = {}
                                if id_set == line_jogada[0]:
                                    jogada['acerto'] = line_jogada[1]
                                    jogada['golpe_id'] = line_jogada[2]
                                    jogada['golpe'] = line_jogada[3]
                                    jogada['quadrante'] = line_jogada[4]
                                    jogada['quadrante'] = line_jogada[5]
                                    jogada['quantidade'] = line_jogada[6]
                                    jogada['relacao_set'] = round(((line_jogada[6] / line_set[2])*100), 2)
                                    set_resultado['jogadas'].append(jogada)

                        lineout_partida['set_resultado'].append(set_resultado)
            
            output_partida.append(lineout_partida)


    return jsonify({'relatorio_partida': output_partida})

# versão 2
@app.route('/v2/get_relatoriopartida', methods=['GET'])
def get_relatoriopartida_v2():
    """ Retorna resultados da partida """

    # Verifica parâmetros de entrada
    id_partida = None
    
    if request.args.get('id_partida'):
        id_partida = request.args.get('id_partida')
        
    if not id_partida:
        id_partida = '0'

    if not id_partida.isdigit():
        return jsonify({'erro' : 'request.args[id_partida] deve ser numerico'})

    sqlvar = (id_partida, )

    # Pesquisa partida conforme id informado no parâmetro
    bloco = " select set.id, set.ordem, partida.id, partida.data_partida, partida.tipo_jogo, partida.modalidade, partida.nome, \
                partida.jogador_1_id, jogador.nome_jogador from set \
                inner join partida on (partida.id = set.partida_id)\
                inner join jogador on (partida.jogador_1_id = jogador.id) \
                where set.partida_id = %s"
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        partida_set_data = cursor.fetchall()

        """
        RESULTADO DOS 3 SETS 
        [
            (7, 1, 23, 
            datetime.datetime(2022, 5, 30, 0, 0, tzinfo=datetime.timezone(datetime.timedelta
            (days=-1, seconds=75600))), 'simples', 'misto', 'Partida Relatorio', 3, 'Fabiana da Silva'), 
            
            (8, 2, 23, datetime.datetime(2022, 5, 30, 0, 0, tzinfo=datetime.timezone(datetime.timedelta
            (days=-1, seconds=75600))), 'simples', 'misto', 'Partida Relatorio', 3, 'Fabiana da Silva')]

        """

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    output_partida = []  # Verificar se é necessario criar uma lista de partidas
    if partida_set_data:
        lineout_partida = {}
        lineout_partida['L_set_resultado'] = []
        
        set_resultado_global = []
        jogada_resultado_global = []
        quadrante_resultado_global = []
        
        jogadas_partida = 0
        acertos_partida = 0
        erros_partida = 0

        
   
        for line in partida_set_data:

            jogadas_set = 0
            acertos_set = 0
            erros_set = 0
          
            lineout_set = {}
            
            id_set = line[0]
            
            tupla = (id_set,)
            
            # Pesquiusa quantidade de cada golpe no set
            bloco = ("  SELECT jogada.golpe_id, jogada.set_id, golpe.descricao_golpe, count(jogada.id) \
                        FROM jogada \
                        inner join golpe on (golpe.id = jogada.golpe_id)    \
                        where set_id = %s GROUP BY (golpe_id, set_id, golpe.descricao_golpe);")

            try:
                connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                cursor = connection.cursor()
                cursor.execute(bloco, tupla)
                dados_jogada = cursor.fetchall()

                """
                JOGADAS POR SET:  [(1, 7, 'Saque', 5), (3, 7, 'Backhand', 9), (7, 7, 'Drive', 8)]
                JOGADAS POR SET:  [(1, 8, 'Saque', 2)]

                """
            
            except (Exception, psycopg2.Error) as error:
                erro = str(error).rstrip()
                erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                return jsonify({'erro' : erro_banco})

            finally:
                if (connection):
                    connection.commit()
                    cursor.close()
                    connection.close()
            
            if dados_jogada:
                for jogada in dados_jogada:

                    total_jogadas = 0
                    total_acertos_jogadas = 0
                    total_erros_jogadas = 0

                    id_golpe = jogada[0]
                    golpe = jogada[2]
                    set_id = jogada[1]   
                    quantidade_jogada = jogada[3]  # total de jogadas do golpe
                    jogadas_set = jogadas_set + quantidade_jogada  # Total de jogadas do set

                    tupla = (id_set, id_golpe)

                    # Pesquisa os quadrantes agrupados por erro e acerto 
                    bloco = ("  SELECT jogada.quadrante_id, acerto, quadrante.descricao_quadrante, count(jogada.id), jogada.set_id \
                            FROM jogada \
                            inner join quadrante on (quadrante.id = jogada.quadrante_id)    \
                            where set_id = %s and golpe_id = %s GROUP BY (quadrante_id, acerto, quadrante.descricao_quadrante, jogada.set_id);")

                    try:
                        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                        cursor = connection.cursor()
                        cursor.execute(bloco, tupla)
                        dados_quadrante = cursor.fetchall()

                        """
                        DADOS QUADRANTES:  [(1, False, 'Q 01', 2), (1, True, 'Q 01', 3)]
                        DADOS QUADRANTES:  [(2, False, 'Q 02', 4), (2, True, 'Q 02', 1), (5, False, 'Q 05', 2), (5, True, 'Q 05', 2)]
                        DADOS QUADRANTES:  [(2, False, 'Q 02', 3), (2, True, 'Q 02', 5)]
                        DADOS QUADRANTES:  [(1, True, 'Q 01', 2)]

                        """
                    
                    except (Exception, psycopg2.Error) as error:
                        erro = str(error).rstrip()
                        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                        return jsonify({'erro' : erro_banco})

                    finally:
                        if (connection):
                            connection.commit()
                            cursor.close()
                            connection.close()

                    if dados_quadrante:
                        for line_quadrante in dados_quadrante:

                            id_quadrante = line_quadrante[0]
                            acerto_quadrante = line_quadrante[1]
                            quadrante = line_quadrante[2]
                            quantidade_jogada_quadrante = line_quadrante[3]
                            set_id_quadrante = line_quadrante[4]

                            if acerto_quadrante:
                                total_acertos_jogadas = total_acertos_jogadas + quantidade_jogada_quadrante
                            else:
                                total_erros_jogadas = total_erros_jogadas + quantidade_jogada_quadrante
                                
                            tupla = (id_set, id_golpe, id_quadrante)

                            quadrante_tupla = (set_id_quadrante, id_golpe, id_quadrante, quadrante, acerto_quadrante, quantidade_jogada_quadrante)
                            quadrante_resultado_global.append(quadrante_tupla)
                            

                            if acerto_quadrante:
                                acertos_set = acertos_set + quantidade_jogada_quadrante
                            else:
                                erros_set = erros_set + quantidade_jogada_quadrante


                        # total_jogadas = total_acertos_jogadas + total_erros_jogadas
                    
                    jogada_tupla = (set_id, id_golpe, golpe, quantidade_jogada, total_acertos_jogadas, total_erros_jogadas)    
                    jogada_resultado_global.append(jogada_tupla)
                          
                # acertos_set = acertos_set + total_acertos_jogadas
                # erros_set = erros_set + total_erros_jogadas

            jogadas_partida = jogadas_partida + jogadas_set
            acertos_partida = acertos_partida + acertos_set
            erros_partida = erros_partida + erros_set

            set_data = (line[0], line[1], jogadas_set, acertos_set, erros_set)
            set_resultado_global.append(set_data)


        if jogadas_partida > 0:
            # Dados da partida
            lineout_partida['A_partida_id'] = line[2]
            lineout_partida['B_data'] = line[3].strftime('%d-%m-%Y')
            lineout_partida['C_tipo_jogo'] = line[4]
            lineout_partida['D_modalidade'] = line[5]
            lineout_partida['E_nome'] = line[6]
            lineout_partida['F_jogador'] = line[8]

            # Resultados da partida
            lineout_partida['G_partida_total'] = jogadas_partida
            lineout_partida['H_partida_acertos'] = acertos_partida
            lineout_partida['I_partida_acertos_%'] = round(((acertos_partida / jogadas_partida)*100), 2)
            lineout_partida['J_partida_erros'] = erros_partida
            lineout_partida['K_partida_erros_%'] = round(((erros_partida / jogadas_partida)*100), 2)
            
            if jogadas_partida > 0:
                for line_set in set_resultado_global:
                    set_resultado = {}
                    if line_set[2] > 0:
                        # Dados do set
                        id_set = line_set[0]
                        set_resultado['A_set_id'] = line_set[0]
                        set_resultado['B_set_ordem'] = line_set[1]

                        # Resultados individual do set
                        set_resultado['C_set_total'] = line_set[2]
                        set_resultado['E_set_acertos'] = line_set[3]
                        set_resultado['G_set_acertos_relacao_set'] = round(((line_set[3] / line_set[2])*100), 2)
                        set_resultado['H_set_erros'] = line_set[4]
                        set_resultado['J_set_erros_relacao_set'] = round(((line_set[4] / line_set[2])*100), 2)
                        
                        # Resultados individual do set
                        set_resultado['D_set_total_relacao_partida'] = round(((line_set[2] / jogadas_partida)*100), 2)
                        set_resultado['F_set_acertos_relacao_partida'] = round(((line_set[3] / jogadas_partida)*100), 2)
                        set_resultado['I_set_erros_relacao_partida'] = round(((line_set[4] / jogadas_partida)*100), 2)
                        
                        set_resultado['K_jogadas'] = []
                        if line_set[2] > 0:
                            for line_jogada in jogada_resultado_global:
                                jogada = {}
                                if id_set == line_jogada[0]:
                                    id_golpe = line_jogada[1]
                                    jogada['A_golpe_id'] = line_jogada[1]
                                    jogada['B_golpe'] = line_jogada[2]
                                    jogada['C_golpe_total'] = line_jogada[3]
                                    jogada['D_golpe_total_relacao_set'] = round(((line_jogada[3] / line_set[2])*100), 2)

                                    jogada['I_quadrantes_acerto'] = []
                                    jogada['J_quadrantes_erro'] = []
                                    if line_jogada[3] > 0:
                                        jogadas_acerto = 0
                                        jogadas_erro = 0
                                        for line_quadrante in quadrante_resultado_global:
                                            quadrante = {}
                                            if id_golpe == line_quadrante[1] and line_jogada[0] == line_quadrante[0]:
                                                if line_quadrante[4]:
                                                    quadrante['A_quadrante_id'] = line_quadrante[2]
                                                    quadrante['B_quadrante'] = line_quadrante[3]
                                                    quadrante['C_quadrante_total'] = line_quadrante[5]
                                                    quadrante['D_quadrante_relacao_golpe'] = round(((line_quadrante[5] / line_jogada[3])*100), 2)
                                                    # jogadas_acerto = jogadas_acerto + line_quadrante[5]
                                                    jogada['I_quadrantes_acerto'].append(quadrante)
                                                else:
                                                    quadrante['A_quadrante_id'] = line_quadrante[2]
                                                    quadrante['B_quadrante'] = line_quadrante[3]
                                                    quadrante['C_quadrante_total'] = line_quadrante[5]
                                                    quadrante['D_quadrante_relacao_golpe'] = round(((line_quadrante[5] / line_jogada[3])*100), 2)
                                                    # jogadas_erro = jogadas_erro + line_quadrante[5]
                                                    jogada['J_quadrantes_erro'].append(quadrante)

                                    jogada['E_golpe_acertos'] = line_jogada[4]
                                    jogada['F_golpe_acertos_porc'] = round(((line_jogada[4]/line_jogada[3])*100), 2)
                                    jogada['G_golpe_erros'] = line_jogada[5]
                                    jogada['H_golpe_erros_porc'] = round(((line_jogada[5]/line_jogada[3])*100), 2)
                                    set_resultado['K_jogadas'].append(jogada)

                        lineout_partida['L_set_resultado'].append(set_resultado)
            
            output_partida.append(lineout_partida)


    return jsonify({'relatorio_partida': output_partida})


# versão 3
@app.route('/v3/get_relatoriopartida', methods=['GET'])
def get_relatoriopartida_v3():
    """ Retorna resultados da partida """

    # Verifica parâmetros de entrada
    id_partida = None
    
    if request.args.get('id_partida'):
        id_partida = request.args.get('id_partida')
        
    if not id_partida:
        id_partida = '0'

    if not id_partida.isdigit():
        return jsonify({'erro' : 'request.args[id_partida] deve ser numerico'})

    sqlvar = (id_partida, )

    # Pesquisa partida conforme id informado no parâmetro
    bloco = " select set.id, set.ordem, partida.id, partida.data_partida, partida.tipo_jogo, partida.modalidade, partida.nome, \
                partida.jogador_1_id, jogador.nome_jogador from set \
                inner join partida on (partida.id = set.partida_id)\
                inner join jogador on (partida.jogador_1_id = jogador.id) \
                where set.partida_id = %s"
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        partida_set_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    output_partida = []  # Verificar se é necessario criar uma lista de partidas
    if partida_set_data:
        lineout_partida = {}
        lineout_partida['L_set_resultado'] = []
        
        set_resultado_global = []
        jogada_resultado_global = []
        quadrante_resultado_global = []
        erros_golpe_global = []

        jogadas_partida = 0
        acertos_partida = 0
        erros_partida = 0
   
        for line in partida_set_data:

            jogadas_set = 0
            acertos_set = 0
            erros_set = 0
          
            lineout_set = {}
            
            id_set = line[0]
            
            tupla = (id_set,)
            
            # Pesquiusa quantidade de cada golpe no set
            bloco = ("  SELECT jogada.golpe_id, jogada.set_id, golpe.descricao_golpe, count(jogada.id) \
                        FROM jogada \
                        inner join golpe on (golpe.id = jogada.golpe_id)    \
                        where set_id = %s GROUP BY (golpe_id, set_id, golpe.descricao_golpe);")

            try:
                connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                cursor = connection.cursor()
                cursor.execute(bloco, tupla)
                dados_jogada = cursor.fetchall()
            
            except (Exception, psycopg2.Error) as error:
                erro = str(error).rstrip()
                erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                return jsonify({'erro' : erro_banco})

            finally:
                if (connection):
                    connection.commit()
                    cursor.close()
                    connection.close()
            
            if dados_jogada:
                for jogada in dados_jogada:

                    total_jogadas = 0
                    total_acertos_jogadas = 0
                    total_erros_jogadas = 0

                    id_golpe = jogada[0]
                    golpe = jogada[2]
                    set_id = jogada[1]   
                    quantidade_jogada = jogada[3]  # total de jogadas do golpe
                    jogadas_set = jogadas_set + quantidade_jogada  # Total de jogadas do set

                    tupla = (id_set, id_golpe)

                    # Pesquisa os quadrantes agrupados por erro e acerto 
                    bloco = ("  SELECT jogada.quadrante_id, acerto, quadrante.descricao_quadrante, count(jogada.id), jogada.set_id \
                            FROM jogada \
                            inner join quadrante on (quadrante.id = jogada.quadrante_id)    \
                            where set_id = %s and golpe_id = %s GROUP BY (quadrante_id, acerto, quadrante.descricao_quadrante, jogada.set_id);")

                    try:
                        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                        cursor = connection.cursor()
                        cursor.execute(bloco, tupla)
                        dados_quadrante = cursor.fetchall()
                    
                    except (Exception, psycopg2.Error) as error:
                        erro = str(error).rstrip()
                        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                        return jsonify({'erro' : erro_banco})

                    finally:
                        if (connection):
                            connection.commit()
                            cursor.close()
                            connection.close()

                    if dados_quadrante:
                        for line_quadrante in dados_quadrante:

                            id_quadrante = line_quadrante[0]
                            acerto_quadrante = line_quadrante[1]
                            quadrante = line_quadrante[2]
                            quantidade_jogada_quadrante = line_quadrante[3]
                            set_id_quadrante = line_quadrante[4]

                            if acerto_quadrante:
                                total_acertos_jogadas = total_acertos_jogadas + quantidade_jogada_quadrante
                            else:
                                total_erros_jogadas = total_erros_jogadas + quantidade_jogada_quadrante


                          
                                
                            tupla = (id_set, id_golpe, id_quadrante)

                            # Pesquisar os erros de saque 
                            bloco = ("  SELECT jogada.golpe_id, jogada.quadrante_id, acerto, tipoerro.descricao_erro, \
                                    count(jogada.id), jogada.set_id, jogada.tipo_erro_id \
                                    FROM jogada \
                                    inner join tipoerro on (tipoerro.id = jogada.tipo_erro_id)    \
                                    where set_id = %s and golpe_id = %s and quadrante_id = %s \
                                    GROUP BY (golpe_id, quadrante_id, acerto, tipoerro.descricao_erro, jogada.set_id, jogada.tipo_erro_id);")

                            try:
                                connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                                cursor = connection.cursor()
                                cursor.execute(bloco, tupla)
                                dados_tipo_erro = cursor.fetchall()    
                                                        
                            except (Exception, psycopg2.Error) as error:
                                erro = str(error).rstrip()
                                erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                                return jsonify({'erro' : erro_banco})

                            finally:
                                if (connection):
                                    connection.commit()
                                    cursor.close()
                                    connection.close()
                                    
                            if dados_tipo_erro:
                                for line_erro in dados_tipo_erro:
                                    golpe_id_erro = line_erro[0]
                                    quadrante_id_erro = line_erro[1]
                                    acerto = line_erro[2]
                                    descricao_erro = line_erro[3]
                                    quantidade_erro = line_erro[4]
                                    set_id_erro = line_erro[5]
                                    tipo_erro_id = line_erro[6]
                            
                                    erros_golpe_tupla = (golpe_id_erro, quadrante_id_erro, acerto, descricao_erro, quantidade_erro, set_id_erro, tipo_erro_id)
                                    erros_golpe_global.append(erros_golpe_tupla)


                            quadrante_tupla = (set_id_quadrante, id_golpe, id_quadrante, quadrante, acerto_quadrante, quantidade_jogada_quadrante)
                            quadrante_resultado_global.append(quadrante_tupla)
                            

                            if acerto_quadrante:
                                acertos_set = acertos_set + quantidade_jogada_quadrante
                            else:
                                erros_set = erros_set + quantidade_jogada_quadrante
                    
                    jogada_tupla = (set_id, id_golpe, golpe, quantidade_jogada, total_acertos_jogadas, total_erros_jogadas)    
                    jogada_resultado_global.append(jogada_tupla)

            jogadas_partida = jogadas_partida + jogadas_set
            acertos_partida = acertos_partida + acertos_set
            erros_partida = erros_partida + erros_set

            set_data = (line[0], line[1], jogadas_set, acertos_set, erros_set)
            set_resultado_global.append(set_data)


        if jogadas_partida > 0:
            # Dados da partida
            lineout_partida['A_partida_id'] = line[2]
            lineout_partida['B_data'] = line[3].strftime('%d-%m-%Y')
            lineout_partida['C_tipo_jogo'] = line[4]
            lineout_partida['D_modalidade'] = line[5]
            lineout_partida['E_nome'] = line[6]
            lineout_partida['F_jogador'] = line[8]

            # Resultados da partida
            lineout_partida['G_partida_total'] = jogadas_partida
            lineout_partida['H_partida_acertos'] = acertos_partida
            lineout_partida['I_partida_acertos_%'] = round(((acertos_partida / jogadas_partida)*100), 2)
            lineout_partida['J_partida_erros'] = erros_partida
            lineout_partida['K_partida_erros_%'] = round(((erros_partida / jogadas_partida)*100), 2)
            
            if jogadas_partida > 0:
                for line_set in set_resultado_global:
                    set_resultado = {}
                    if line_set[2] > 0:
                        # Dados do set
                        id_set = line_set[0]
                        set_resultado['A_set_id'] = line_set[0]
                        set_resultado['B_set_ordem'] = line_set[1]

                        # Resultados individual do set
                        set_resultado['C_set_total'] = line_set[2]
                        set_resultado['E_set_acertos'] = line_set[3]
                        set_resultado['G_set_acertos_relacao_set'] = round(((line_set[3] / line_set[2])*100), 2)
                        set_resultado['H_set_erros'] = line_set[4]
                        set_resultado['J_set_erros_relacao_set'] = round(((line_set[4] / line_set[2])*100), 2)
                        
                        # Resultados individual do set
                        set_resultado['D_set_total_relacao_partida'] = round(((line_set[2] / jogadas_partida)*100), 2)
                        set_resultado['F_set_acertos_relacao_partida'] = round(((line_set[3] / jogadas_partida)*100), 2)
                        set_resultado['I_set_erros_relacao_partida'] = round(((line_set[4] / jogadas_partida)*100), 2)
                        
                        set_resultado['K_jogadas'] = []
                        if line_set[2] > 0:
                            for line_jogada in jogada_resultado_global:
                                jogada = {}
                                if id_set == line_jogada[0]:
                                    id_golpe = line_jogada[1]
                                    jogada['A_golpe_id'] = line_jogada[1]
                                    jogada['B_golpe'] = line_jogada[2]
                                    jogada['C_golpe_total'] = line_jogada[3]
                                    jogada['D_golpe_total_relacao_set'] = round(((line_jogada[3] / line_set[2])*100), 2)

                                    jogada['I_quadrantes_acerto'] = []
                                    jogada['J_quadrantes_erro'] = []
                                    if line_jogada[3] > 0:
                                        jogadas_acerto = 0
                                        jogadas_erro = 0
                                        for line_quadrante in quadrante_resultado_global:
                                            quadrante = {}
                                            if id_golpe == line_quadrante[1] and line_jogada[0] == line_quadrante[0]:
                                                if line_quadrante[4]:
                                                    quadrante['A_quadrante_id'] = line_quadrante[2]
                                                    quadrante['B_quadrante'] = line_quadrante[3]
                                                    quadrante['C_quadrante_total'] = line_quadrante[5]
                                                    quadrante['D_quadrante_relacao_golpe'] = round(((line_quadrante[5] / line_jogada[3])*100), 2)
                                                    # jogadas_acerto = jogadas_acerto + line_quadrante[5]
                                                    jogada['I_quadrantes_acerto'].append(quadrante)
                                                else:
                                                    quadrante['A_quadrante_id'] = line_quadrante[2]
                                                    quadrante['B_quadrante'] = line_quadrante[3]
                                                    quadrante['C_quadrante_total'] = line_quadrante[5]
                                                    quadrante['D_quadrante_relacao_golpe'] = round(((line_quadrante[5] / line_jogada[3])*100), 2)
                                                    quadrante['E_tipo_erro'] = []
                                                    if erros_golpe_global:
                                                            for line_erro in erros_golpe_global:
                                                                if line_erro[5] == line_quadrante[0] and line_erro[0] == line_quadrante[1] and line_erro[1] == line_quadrante[2]:
                                                            
                                                                    tipo_erro = {}
                                                                    tipo_erro['A_id'] = line_erro[6]
                                                                    tipo_erro['B_tipo_erro'] = line_erro[3]
                                                                    tipo_erro['C_quantidade'] = line_erro[4]
                                                                    quadrante['E_tipo_erro'].append(tipo_erro)
                                                                    
                                                    jogada['J_quadrantes_erro'].append(quadrante)
                                    jogada['E_golpe_acertos'] = line_jogada[4]
                                    jogada['F_golpe_acertos_porc'] = round(((line_jogada[4]/line_jogada[3])*100), 2)
                                    jogada['G_golpe_erros'] = line_jogada[5]
                                    jogada['H_golpe_erros_porc'] = round(((line_jogada[5]/line_jogada[3])*100), 2)
                                    set_resultado['K_jogadas'].append(jogada)

                        lineout_partida['L_set_resultado'].append(set_resultado)
            
            output_partida.append(lineout_partida)


    return jsonify({'relatorio_partida': output_partida})







try:
    f = open('apibadminton.json',)
    config = json.load(f)
except:
    errormessage = 'erro ao abrir o arquivo apibadminton.json'
    logging.error(errormessage)
    exit()
finally:
    f.close()

if not config:
    errormessage = 'apibadminton.json formato invalido'
    logging.error(errormessage)
    exit()

schema = {
    "title": "config",
    "type": "object",
    "required": [ "SECRET_KEY", "DATABASE_HOST", "DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD", "URLMEDIA", "UPLOAD_URL", "UPLOAD_PATH"],
    "properties": {
        "SECRET_KEY": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50
        },
        "DATABASE_HOST": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
        },
        "DATABASE_NAME": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
        },
        "DATABASE_USER": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "DATABASE_PASSWORD": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
        },
        "URLMEDIA": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "UPLOAD_URL": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "UPLOAD_PATH": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
    }
}


# Verifica se Json é valido (conforme Json-schema)
try:
    validate(config, schema)

except ValidationError as e:
    errormessage = 'apibadminton.json formato invalido' + ' (mensagem: [' + str(e.message) + ']) ' + '(path: [' + str(e.path) + '])'
    logging.error(errormessage)
    exit()


if __name__ == '__main__':
    app.run(debug=True)


