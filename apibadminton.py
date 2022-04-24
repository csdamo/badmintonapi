from flask import Flask, request, jsonify, make_response, render_template
import psycopg2
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from jsonschema import validate, ValidationError, SchemaError
import json
import logging
import logging.handlers
import warnings
import locale
import requests

from flask_mail import Mail
from flask_mail import Message
from threading import Thread

from flask_cors import CORS

import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
CORS(app)


@app.route('/get_jogadores', methods=['GET'])
def get_jogadores():

    bloco = " select jogador.id, jogador.nome_jogador, jogador.data_nascimento, jogador.telefone, \
                jogador.email, jogador.lateralidade, jogador.foto \
                from jogador "
                
    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(bloco)
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
            lineout_jogador['jogador_id'] = line[0]
            lineout_jogador['jogador_nome'] = line[1]
            lineout_jogador['jogador_data_nascimento'] = line[2].strftime('%d %B %Y')
            lineout_jogador['jogador_telefone'] = line[3]
            lineout_jogador['jogador_email'] = line[4]
            lineout_jogador['jogador_lateralidade'] = line[5]
            foto = line[6]
            if foto:
                lineout_jogador['jogador_foto'] = config['URLMEDIA'] + '/' + foto
            else:
                lineout_jogador['jogador_foto'] = ''

            output_jogadores.append(lineout_jogador)

    return jsonify({'jogadores_badminton' : output_jogadores})


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
        
        lineout_jogador['jogador_id'] = jogadore_data[0]
        lineout_jogador['jogador_nome'] = jogadore_data[1]
        lineout_jogador['jogador_data_nascimento'] = jogadore_data[2].strftime('%d %B %Y')
        lineout_jogador['jogador_telefone'] = jogadore_data[3]
        lineout_jogador['jogador_email'] = jogadore_data[4]
        lineout_jogador['jogador_lateralidade'] = jogadore_data[5]
        foto = jogadore_data[6]
        if foto:
            lineout_jogador['jogador_foto'] = config['URLMEDIA'] + '/' + foto
        else:
            lineout_jogador['jogador_foto'] = ''

    return jsonify({'jogadores_badminton' : lineout_jogador})



    sqlfix = ("select * from contausuarioapp where email = %s")
    sqlvar = (data['email'])

    try:
        connection = psycopg2.connect(host=config['DATABASE_HOST'], database=config['DATABASE_NAME'], user=config['DATABASE_USER'], password=config['DATABASE_PASSWORD'])
        cursor = connection.cursor()
        cursor.execute(sqlfix, (sqlvar,))
        conta_record = cursor.fetchone()
        
        if conta_record:
            user_data = {}
            user_data['status'] = '401'
            user_data['mensagem'] = 'Email ja esta sendo utilizado por outra conta.'
            return jsonify({'status' : user_data})

    except (Exception, psycopg2.Error) as error:
        erro = str(error).rstrip()
        erro_banco = 'Erro ao acessar o Banco de Dados (' + erro + ').'
        return jsonify({'erro' : erro_banco})

    finally:
        if (connection):
            cursor.close()
            connection.close()

    
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
        
        lineout_jogador['jogador_id'] = jogadore_data[0]
        lineout_jogador['jogador_nome'] = jogadore_data[1]
        lineout_jogador['jogador_data_nascimento'] = jogadore_data[2].strftime('%d %B %Y')
        lineout_jogador['jogador_telefone'] = jogadore_data[3]
        lineout_jogador['jogador_email'] = jogadore_data[4]
        lineout_jogador['jogador_lateralidade'] = jogadore_data[5]
        foto = jogadore_data[6]
        if foto:
            lineout_jogador['jogador_foto'] = config['URLMEDIA'] + '/' + foto
        else:
            lineout_jogador['jogador_foto'] = ''

    return jsonify({'jogadores_badminton' : lineout_jogador})


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
    
    sqlvar = (nome, data_nascimento, telefone, email, lateralidade, foto, datetimenow, datetimenow)

    bloco = ("insert into jogador (nome_jogador, data_nascimento, telefone, \
                email, lateralidade, foto, criado_em, atualizado_em) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")

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
    
    return jsonify({'mensagem' : "post_jogador executado"})


@app.route('/upload_file', methods=['POST'])
def upload_file():

    if 'file' not in request.files:
        return jsonify({'erro' : 'Arquivo não carregado'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'erro' : 'Arquivo não carregado'})

    if file:
        unique_name = str(uuid.uuid4().hex) + file.filename
        filename = secure_filename(file.filename)
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
            lineout_golpe['golpe_id'] = line[0]
            lineout_golpe['golpe_descricao'] = line[1]
        
            output_golpe.append(lineout_golpe)
    

    return jsonify({'golpes_badminton' : output_golpe})


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
            "maxLength": 50
        },
        "DATABASE_NAME": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50
        },
        "DATABASE_USER": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50
        },
        "DATABASE_PASSWORD": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50
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
