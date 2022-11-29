#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# Desenvolvido por: Diego Henrique Arenas Okawa - 2127890 &&                                                                                                            #
#                   Mario José Miyamoto Kowalski - 2128047                                                                                                              #
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# import Pyro5.api
# import datetime
# import threading
# import time
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA

from flask import Flask, redirect, url_for, request, render_template
from flask_sse import sse
from apscheduler.schedulers.background import BackgroundScheduler

key = RSA.generate(2048)
clientes = {}
compromissos = []
public_key = key.publickey().exportKey("PEM")
private_key = key.exportKey("PEM")

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
# app.register_blueprint(sse, url_prefix='/cadastrar')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastrar/<name>')
def cadastrar(name):
    clientes[name] = name
    # sse.publish({"message": "TESTANDO"}, type='publish')
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

    compromissos.append((nomeCliente, compromisso))

    if(nomeConvidados is not None):
        convidados = nomeConvidados.split(",")

    for convidado in convidados:
        novoCompromisso = compromisso.copy()
        compromissos.append((str(convidado), novoCompromisso))

    print(compromissos)

    # sse.publish({"message": "TESTANDO"}, type='publish')
    return redirect(url_for('cadastrar',name = nomeCliente))

@app.route('/consultarCompromissos',methods = ['POST', 'GET'])
def consultarCompromissos():
    nomeCliente = request.form['nomeCliente']
    stringCompromissos = ""
    for compromisso in compromissos:
        if(compromisso[0] == nomeCliente):
            stringCompromissos = stringCompromissos + str(compromisso) + "\n"

    return stringCompromissos

@app.route('/cancelarCompromisso',methods = ['POST', 'GET'])
def cancelarCompromisso():
    nomeCliente = request.form['nomeCliente']
    nomeCompromisso = request.form['nomeCompromissoCancelado']

    for i in reversed(range(len(compromissos))):
        if nomeCompromisso == compromissos[i][1]["nomeCompromisso"]:
            compromissos.pop(i)

    return redirect(url_for('cadastrar',name = nomeCliente))

# @Pyro5.api.expose
# class Servidor(object):
#     key = RSA.generate(2048)
#     clientes = {}
#     compromissos = []
#     public_key = key.publickey().exportKey("PEM")
#     private_key = key.exportKey("PEM")

#     @Pyro5.server.oneway
#     def cadastro(self, referenciaCliente, nome):
#         cliente = Pyro5.api.Proxy(referenciaCliente)
#         Servidor.clientes[nome] = (referenciaCliente)
#         cliente.setPublic_key(Servidor.public_key)

#     @Pyro5.server.oneway
#     def cadastrarCompromisso(self, nome, compromisso, convidadosCompromisso):
#         Servidor.compromissos.append((nome, compromisso))
#         msg = 'Compromisso "' + compromisso['nome'] + '" confirmado'
#         callback = Pyro5.api.Proxy(Servidor.clientes[nome])
#         callback.receberMensagemConfirmacao(msg, self.assinar(msg))

#         if(convidadosCompromisso is not None):
#             convidados = convidadosCompromisso.split(",")
#             nomeCompromisso = compromisso["nome"]

#             for convidado in convidados:
#                 if(Servidor.clientes.get(convidado) is not None):
#                     callbackConvidado = Pyro5.api.Proxy(Servidor.clientes[convidado])   
#                     msg = 'Deseja participar do compromisso: ' + nomeCompromisso + '?\n1 - Sim\n2 - Não\n'
#                     option = callbackConvidado.receberMensagemCompromisso(msg, self.assinar(msg))
                    
#                     if option == 1:
#                         novoCompromisso = compromisso.copy()
#                         novoCompromisso['alertado'] = False
#                         msg = "Deseja ser alertado: " + nomeCompromisso + "?\n1 - Sim\n2 - Não\n"
#                         option = callbackConvidado.receberMensagemCompromisso(msg, self.assinar(msg))

#                         if option == 1:
#                             msg = "Em que horario deseja ser alertado? "
#                             novoCompromisso['horarioAlerta'] = callbackConvidado.receberMensagemHorario(msg, self.assinar(msg))
#                         elif option == 2:
#                             novoCompromisso['horarioAlerta'] = None
#                         Servidor.compromissos.append((callbackConvidado.getNome(), novoCompromisso))

#     @Pyro5.server.oneway
#     def cancelarCompromisso(self, nome):
#         for i in reversed(range(len(Servidor.compromissos))):
#             if nome == Servidor.compromissos[i][1]["nome"]:
#                 Servidor.compromissos.pop(i)
#         print(Servidor.compromissos)

#     @Pyro5.server.oneway
#     def consultarCompromisso(self, data, referenciaCliente):
#         callbackCliente = Pyro5.api.Proxy(referenciaCliente)
#         comp = []        

#         for compromisso in Servidor.compromissos:
#             if data == compromisso[1]["data"] and compromisso[0] == callbackCliente.getNome():
#                 if not self.isInList(comp, compromisso[1]["nome"]):
#                     comp.append(compromisso[1])

#         callbackCliente.imprimirCompromissos(comp)   
    
#     def isInList(self, list, name):
#         for element in list:
#             if name == element['nome']:
#                 return True
#         return False

#     def assinar(self, msg):
#         bmsg = bytes(msg, 'utf-8')
#         h = SHA256.new()
#         h.update(bmsg)
#         key = RSA.import_key(self.private_key)
#         sig = pkcs1_15.new(key).sign(h)
#         return sig


# def verificarAlertas():
#     while True:
#         try:
#             for compromisso in Servidor.compromissos:
#                 if compromisso[1]["data"] == str(datetime.date.today()):
#                     t = time.localtime()
#                     horarioAtual = time.strftime("%H:%M", t)
#                     if compromisso[1]["horarioAlerta"] == str(horarioAtual) and compromisso[1]["alertado"] == False:
#                         nomeCompromisso = compromisso[1]["nome"]
#                         callbackCliente = Pyro5.api.Proxy(Servidor.clientes[compromisso[0]])
#                         callbackCliente.notificacao(f"ALERTA DE COMPROMISSO: {nomeCompromisso}")
#                         compromisso[1]["alertado"] = True
#                         time.sleep(0.3)
#         except:
#             pass

#         time.sleep(0.3)

# def main():
#     daemon = Pyro5.server.Daemon()         # make a Pyro daemon
#     ns = Pyro5.api.locate_ns()             # find the name server
#     uri = daemon.register(Servidor)        # register the greeting maker as a Pyro object
#     ns.register("Agenda", uri)             # register the object with a name in the name server

#     print("Ready.")  
#     thread = threading.Thread(target=verificarAlertas)
#     thread.start()              
#     daemon.requestLoop()   
    
if __name__ == "__main__":
    app.run(debug=True)