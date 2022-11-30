#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# Desenvolvido por: Diego Henrique Arenas Okawa - 2127890 &&                                                                                                            #
#                   Mario José Miyamoto Kowalski - 2128047                                                                                                              #
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

from flask import Flask, redirect, url_for, request, render_template, Response, stream_with_context
from flask_sse import sse
from gevent.pywsgi import WSGIServer
import json
import time
import datetime
import threading

clientes = {}
compromissos = []

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def index():
    return render_template('index.html')

def compromissoToString(compromisso):
    string = str(compromisso["nomeCompromisso"] + "," + compromisso["dataCompromisso"] + "," + compromisso["horarioCompromisso"])
    return string

@app.route('/cadastrar/<name>')
def cadastrar(name):
    clientes[name] = name
    return render_template('/cliente.html')

@app.route('/login',methods = ['POST'])
def login():
    nomeCliente = request.form['nome']
    return redirect(url_for('cadastrar',name = nomeCliente))

@app.route('/cadastroCompromisso',methods = ['POST'])
def cadastroCompromisso():
    compromisso = {}
    nomeCliente = request.form['nomeCliente']
    nomeCompromisso = request.form['nomeCompromisso']
    dataCompromisso = request.form['dataCompromisso']
    horarioCompromisso = request.form['horarioCompromisso']
    nomeConvidados = request.form['nomeConvidados']
    horarioAlerta = request.form['horarioAlerta']

    compromisso["nomeCompromisso"] = nomeCompromisso
    compromisso["dataCompromisso"] = dataCompromisso
    compromisso["horarioCompromisso"] = horarioCompromisso
    compromisso["nomeConvidados"] = nomeConvidados
    compromisso["horarioAlerta"] = horarioAlerta
    compromisso['alertado'] = False

    compromissos.append((nomeCliente, compromisso))

    if(nomeConvidados is not None and not nomeConvidados.isspace()):
        convidados = nomeConvidados.split(",")
        string = compromissoToString(compromisso)

    for convidado in convidados:
        sse.publish({"user": nomeCliente, "payload": string}, type="convite", channel=convidado)

    print(compromissos)

    return redirect(url_for('cadastrar',name = nomeCliente))

@app.route('/aceitarConvite',methods = ['POST'])
def aceitarConvite():
    compromisso = {}
    compromisso["nomeCompromisso"] = request.form['nomeCompromisso']
    compromisso["dataCompromisso"] = request.form['dataCompromisso']
    compromisso["horarioCompromisso"] = request.form['horarioCompromisso']
    compromisso["horarioAlerta"] = request.form['horarioAlerta']
    compromisso["alertado"] = False

    compromissos.append((request.form['nomeCliente'], compromisso))
    return redirect(url_for('cadastrar',name = request.form['nomeCliente']))
    

@app.route('/consultarCompromissos',methods = ['POST', 'GET'])
def consultarCompromissos():
    nomeCliente = request.form['nomeCliente']
    data = request.form['dataCompromissos']
    stringCompromissos = ""
    for compromisso in compromissos:
        if(compromisso[0] == nomeCliente and data == compromisso[1]["dataCompromisso"]):
            stringCompromissos = stringCompromissos + str(compromisso) + "\n"

    return stringCompromissos

@app.route('/cancelarCompromisso',methods = ['POST', 'GET'])
def cancelarCompromisso():
    nomeCliente = request.form['nomeCliente']
    nomeCompromisso = request.form['nomeCompromissoCancelado']

    for i in reversed(range(len(compromissos))):
        if nomeCompromisso == compromissos[i][1]["nomeCompromisso"] and nomeCliente == compromissos[i][0]:
            compromissos.pop(i)

    return redirect(url_for('cadastrar',name = nomeCliente))

def convertData(d):
    strings = d.split('/')
    data = strings[2]+ "-" + strings[1] + "-" + strings[0]
    return data

def verificarAlertas():
    with app.app_context():
        while True:
            for compromisso in compromissos:
                if convertData(compromisso[1]["dataCompromisso"]) == str(datetime.date.today()):
                    t = time.localtime()
                    horarioAtual = time.strftime("%H:%M", t)
                    if compromisso[1]["horarioAlerta"] == str(horarioAtual) and compromisso[1]["alertado"] == False:
                        nomeCompromisso = compromisso[1]["nomeCompromisso"]
                        canal = compromisso[0]
                        sse.publish({"payload": compromissoToString(compromisso[1])}, type="alerta", channel=canal)
                        compromisso[1]["alertado"] = True
                        print("Alerta")
                        time.sleep(0.3)

            time.sleep(0.3)
    
if __name__ == "__main__":
    thread = threading.Thread(target=verificarAlertas, daemon=True)
    thread.start()
    app.run(debug=True)