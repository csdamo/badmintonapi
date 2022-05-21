from flask import Flask, request, jsonify, make_response, render_template
import psycopg2
# import uuid
# from werkzeug.security import generate_password_hash, check_password_hash
# import jwt
import datetime
from functools import wraps
from jsonschema import validate, ValidationError, SchemaError
import json
import logging
import logging.handlers
import warnings
import locale
import requests

# from flask_mail import Mail
# from flask_mail import Message
from threading import Thread

from flask_cors import CORS

import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
CORS(app)


@app.route('/post_jogador', methods=['POST'])
def post_jogador():

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

    datetimenow = datetime.datetime.now()
    nome = data["nome"]
    data_nascimento = data["data_nascimento"]
    telefone = data["telefone"]
    email = data["email"]
    lateralidade = data["lateralidade"]
    foto = 'jogador/' + data["foto"]
    
    tupla = (nome, data_nascimento, telefone, email, lateralidade, foto, datetimenow, datetimenow)

    bloco = ("insert into jogador (nome_jogador, data_nascimento, telefone, \
                email, lateralidade, foto, criado_em, atualizado_em) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")

    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco, tupla)

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            connection.commit()
            cursor.close()
            connection.close()
    
    return jsonify({'mensagem' : "post_jogador executado"})


@app.route('/get_jogador', methods=['GET'])
def get_jogador():

    id_jogador = None
    
    if request.args.get('id_jogador'):
        id_jogador = request.args.get('id_jogador')
        
    if not id_jogador:
        id_jogador = '0'

    if not id_jogador.isdigit():
        return jsonify({'erro' : 'request.args[id_jogador] deve ser numerico'})



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

    lista_id_jogador = None
    if request.args.get('lista_id_jogador'):
        lista_id_jogador = (request.args.get('lista_id_jogador')).replace(" ", "").split(',')
        
        for jogador in lista_id_jogador:
            if not jogador.isdigit():
                return jsonify({'erro' : 'request.args[lista_id_jogador] deve ser numerico'})

    if not lista_id_jogador:
        lista_id_jogador = '0'

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

    if 'file' not in request.files:
        return jsonify({'erro' : 'Arquivo não carregado'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'erro' : 'Arquivo não carregado'})

    if file:
        unique_name = str(uuid.uuid4().hex) + file.filename
        filename = secure_filename(unique_name)
        file.save(os.path.join(config['UPLOAD_PATH'], filename))

        url_file_uploaded = config['UPLOAD_URL'] + '/' + filename

        lineout = {}
        lineout['nome_arquivo'] = filename

        return jsonify({'mensagem' : lineout})


@app.route('/get_golpes', methods=['GET'])
def get_golpes():

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

    data = request.get_json()

    if not data:
        return jsonify({'erro' : 'JSON inválido.'})

    schema = {
        "type": "object",
        "required": ["nome", "data_partida", "tipo_jogo", "modalidade", "jogador_1", "jogador_2", "jogador_adversario_1",  "jogador_adversario_2"],
        "properties": {
             "nome": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200
            },
            "data_partida": {
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


    datetimenow = datetime.datetime.now()
    nome = data["nome"]
    data_partida = data["data_partida"]
    tipo_jogo = data["tipo_jogo"]
    modalidade = data["modalidade"]
    jogador_1 = data["jogador_1"]
    jogador_2 = data["jogador_2"]
    jogador_adversario_1 = data["jogador_adversario_1"]
    jogador_adversario_2 = data["jogador_adversario_2"]

    if tipo_jogo == 'simples':
        jogador_2 = None
        jogador_adversario_2 = None
    
    sqlvar = (nome, data_partida, tipo_jogo, modalidade, jogador_1, jogador_2, jogador_adversario_1, jogador_adversario_2, datetimenow, datetimenow)

    bloco = ("insert into partida (nome, data_partida, tipo_jogo, modalidade, jogador_1_id, jogador_2_id, \
                 jogador_adversario_1_id, jogador_adversario_2_id, criado_em, atualizado_em) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                    returning id")

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
    partida = {}
    partida['partida_id'] = data_partida[0]

    return jsonify({'mensagem' : partida})


@app.route('/get_partida', methods=['GET'])
def get_partida():

    id_partida = None
    
    if request.args.get('id_partida'):
        id_partida = request.args.get('id_partida')
        
    if not id_partida:
        id_partida = '0'

    if not id_partida.isdigit():
        return jsonify({'erro' : 'request.args[id_partida] deve ser numerico'})



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
    lineout_jogador = {}
    if partida_data:
        lineout_jogador['id'] = partida_data[0]
        lineout_jogador['data'] = partida_data[1].strftime('%d-%m-%Y')
        lineout_jogador['tipo_jogo'] = partida_data[2]
        lineout_jogador['modalidade'] = partida_data[3]
        lineout_jogador['partida_nome'] = partida_data[4]
        lineout_jogador['jogador_1'] = partida_data[5]
        lineout_jogador['jogador_2'] = partida_data[6]
        lineout_jogador['jogador_adversario_1'] = partida_data[7]
        lineout_jogador['jogador_adversario_2'] = partida_data[8]

    return jsonify({'partida_badminton' : lineout_jogador})


@app.route('/get_partidas', methods=['GET'])
def get_partidas():

    bloco = " select partida.id, partida.data_partida, partida.tipo_jogo, partida.modalidade, partida.nome, \
                partida.jogador_1_id, partida.jogador_2_id, partida.jogador_adversario_1_id, partida.jogador_adversario_2_id \
                from partida "
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco)
        partidas_data = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    output_partidas = []
    if partidas_data:
        for line in partidas_data:
            lineout_partida = {}
            lineout_partida['id'] = line[0]
            lineout_partida['data'] = line[1].strftime('%d-%m-%Y')
            lineout_partida['tipo_jogo'] = line[2]
            lineout_partida['modalidade'] = line[3]
            lineout_partida['partida_nome'] = line[4]
            lineout_partida['jogador_1'] = line[5]
            lineout_partida['jogador_2'] = line[6]
            lineout_partida['jogador_adversario_1'] = line[7]
            lineout_partida['jogador_adversario_2'] = line[8]

            output_partidas.append(lineout_partida)

    return jsonify({'partidas_badminton' : output_partidas})

    

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
