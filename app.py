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

    # variáveis com os dados a serem salvos
    nome = data["nome"]
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
        if len(foto) < 1:
            lineout_jogador['foto'] = config['URLMEDIA'] + '/' + foto
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
            if len(foto) < 1:
                lineout_jogador['foto'] = config['URLMEDIA'] + '/' + foto
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
    
    # Pesquisa tods os golpes de badminton cadastrados
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
    output_golpe = []
    if golpe_data:
        for line in golpe_data:
            lineout_golpe = {}
            lineout_golpe['id'] = line[0]
            lineout_golpe['descricao'] = line[1]
        
            output_golpe.append(lineout_golpe)

    return jsonify({'golpes_badminton' : output_golpe})


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
    jogador_2 = data["jogador_2"]
    jogador_adversario_1 = data["jogador_adversario_1"]
    jogador_adversario_2 = data["jogador_adversario_2"]
    datetimenow = datetime.datetime.now()

    if tipo_jogo == 'simples':
        jogador_2 = None
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
        partida['partida_id'] = data_partida[0].strftime('%d-%m-%Y')
        partida['nome'] = data_partida[1]
        partida['data'] = data_partida[2]
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


    # Pesquisa jogador conforme id informado no parâmetro
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

    # Devolve dados da partida pesquisado
    lineout_partida = {}
    if partida_data:
        id_partida = partida_data[0] 
        lineout_partida['id'] = partida_data[0]
        lineout_partida['data'] = partida_data[1].strftime('%d-%m-%Y')
        lineout_partida['tipo_jogo'] = partida_data[2]
        lineout_partida['modalidade'] = partida_data[3]
        lineout_partida['nome'] = partida_data[4]
        lineout_partida['jogador_1'] = partida_data[5]
        lineout_partida['jogador_2'] = partida_data[6]
        lineout_partida['jogador_adversario_1'] = partida_data[7]
        lineout_partida['jogador_adversario_2'] = partida_data[8]

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
                erros = False

                sqlvar = (erros, id_set)

                bloco = (" select count (acerto) from jogada where acerto = %s and jogada.set_id = %s  ")
                
                try:
                    connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                    cursor = connection.cursor()
                    cursor.execute(bloco, sqlvar)
                    erros = cursor.fetchone()
                
                except (Exception, psycopg2.Error) as error:
                    erro = str(error).rstrip()
                    erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
                    return jsonify({'erro' : erro_banco})

                finally:
                    if (connection):
                        connection.commit()
                        cursor.close()
                        connection.close()

                acertos = True

                sqlvar = (acertos, id_set)

                bloco = (" select count (acerto) from jogada where acerto = %s and jogada.set_id = %s  ")
                
                try:
                    connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
                    cursor = connection.cursor()
                    cursor.execute(bloco, sqlvar)
                    acertos = cursor.fetchone()
                
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
                qtd_erros = erros[0]
                qtd_acertos = acertos[0]
                diferenca_erro_acerto = abs(qtd_erros - qtd_acertos)
            
                if qtd_erros > qtd_acertos:
                    set_partida['resultado_set'] = 'perdeu'
                elif qtd_erros < qtd_acertos:
                    set_partida['resultado_set'] = 'ganhou'
                else:
                    set_partida['resultado_set'] = 'empate'

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
    
    # Pesquisa jogador conforme id informado no parâmetro
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
            lineout_partida = {}
            id_partida = line[0]
            lineout_partida['id'] = line[0]
            lineout_partida['data'] = line[1].strftime('%d-%m-%Y')
            lineout_partida['tipo_jogo'] = line[2]
            lineout_partida['modalidade'] = line[3]
            lineout_partida['nome'] = line[4]
            lineout_partida['jogador_1'] = line[5]
            lineout_partida['jogador_2'] = line[6]
            lineout_partida['jogador_adversario_1'] = line[7]
            lineout_partida['jogador_adversario_2'] = line[8]

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
                    set_partida['id_set'] = set_data[0]
                    set_partida['ordem_set'] = set_data[1]
                    
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
    
    # Realiza insert no banco de dados
    datetimenow = datetime.datetime.now()
    set_id = data['set']
    sqlvar = (set_id, data['golpe'], data['quadrante'], data['acerto'], datetimenow, datetimenow)

    bloco = ("insert into jogada (set_id, golpe_id, quadrante_id, acerto, criado_em, atualizado_em) \
            VALUES (%s, %s, %s, %s, %s, %s) ")

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

    # Pesquisar a quantidade de acertos
    acerto = True

    sqlvar = (acerto, set_id)

    bloco = (" select count (jogada.acerto) from jogada \
                where jogada.acerto = %s and jogada.set_id = %s ")
    
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        acerto = cursor.fetchone()
    
    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()

    # Pesquisar a quantidade de erros
    erro = False

    sqlvar = (erro, set_id)

    bloco = (" select count (acerto) from jogada \
                where acerto = %s and jogada.set_id = %s  ")
    
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, sqlvar)
        erro = cursor.fetchone()
    
    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()

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

    qtd_erros = erro[0]
    qtd_acertos = acerto[0]
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
        set_data['set_id'] = data_set[0]
        set_data['partida_id'] = data_set[1]
        set_data['ordem'] = data_set[2] 

        erros = False

        sqlvar = (erros, id_set)

        bloco = (" select count (acerto) from jogada where acerto = %s and jogada.set_id = %s  ")
        
        try:
            connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
            cursor = connection.cursor()
            cursor.execute(bloco, sqlvar)
            erros = cursor.fetchone()
        
        except (Exception, psycopg2.Error) as error:
            erro = str(error).rstrip()
            erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
            return jsonify({'erro' : erro_banco})

        finally:
            if (connection):
                connection.commit()
                cursor.close()
                connection.close()

        acertos = True

        sqlvar = (acertos, id_set)

        bloco = (" select count (acerto) from jogada where acerto = %s and jogada.set_id = %s  ")
        
        try:
            connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
            cursor = connection.cursor()
            cursor.execute(bloco, sqlvar)
            acertos = cursor.fetchone()
        
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
        qtd_erros = erros[0]
        qtd_acertos = acertos[0]
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




LOGFILE = 'apibadminton.log'   #Log-File-Name
LOGFILESIZE = 5000000    #Log-File-Size (bytes)
LOGFILECOUNT = 4 #Rotate-Count-File

#Config Log-File
logger = logging.getLogger()
logger.setLevel(logging.INFO)
h = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=LOGFILESIZE, backupCount=LOGFILECOUNT)
f = logging.Formatter('[%(asctime)s] %(levelname)s:%(message)s', datefmt='%d/%m/%Y %H:%M:%S')
h.setFormatter(f)
logger.addHandler(h)
logging.info('apibadminton started')

#logging.warning('testa warning')

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


#Verifica se Json é valido (conforme Json-schema)
try:
    validate(config, schema)

except ValidationError as e:
    errormessage = 'apibadminton.json formato invalido' + ' (mensagem: [' + str(e.message) + ']) ' + '(path: [' + str(e.path) + '])'
    logging.error(errormessage)
    exit()


if __name__ == '__main__':
    app.run(debug=True)
