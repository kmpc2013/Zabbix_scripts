
"""
#######################################################################
# Empresa: Sercompe
# Autor: Luis G. Fernandes
# Email: luis.fernandes@sercompe.com.br
# Funcao: Obter dados do Veeam Agent StandAlone Linux
# Zabbix Version: 4.2
# Last updates - 17/05/2023 | luis.fernandes@sercompe.com.br - Script criado
######################################################################
# Reference code:
# 90001 -> Job nunca executado
# 601 -> Variaveis com erro
# 602 -> Opção não existe
# 603 -> Job nunca executado
######################################################################
"""

import subprocess
import re
import json
import sys
import datetime

def valueMap(jobState):
    if _COMMAND == 'sessionList':
        dict = {
            'Success': 1,
            'Running': 2,
            'Warning': 3,
            'Failed': 4,
            'Stopped': 5,
            'Never executed': 6,
            'Unknown': 7
        }
    
    try:
        result = dict[jobState]
    except:
        result = dict['Unknown']

    return result

def jobList():
    # Executa o comando e armazena o resultado na variável `output`
    output = subprocess.check_output(['veeamconfig', 'job', 'list']).decode()
    output = output.splitlines()[1:]

    # Extrai os dados relevantes da saída do comando usando expressões regulares
    regex = r'(\S+.+)\s\s+(\S+.+)\s\s+(\S+.+)\s\s+(\S+.+)\s\s+?'
    jobs = []
    for line in output:
        match = re.match(regex, line)
        if match:
            id = match.group(2).strip()[1:-1]
            name = match.group(1).strip()
            type = match.group(3).strip()
            repository = match.group(4).strip()
            jobs.append({'{#JOBID}': id, '{#JOBNAME}': name, '{#JOBTYPE}': type, '{#REPOSITORY}': repository})

    # Cria um objeto LLD compatível com o Zabbix
    lld_data = {'data': jobs}

    # Formata a saída como um objeto JSON
    json_output = json.dumps(lld_data, indent=4)

    return json_output

def sessionList(jobId):
    result = subprocess.run(['veeamconfig', 'session', 'list', '--jobId', jobId], capture_output=True, text=True)
    output = result.stdout.strip().split('\n')[1:-1]
    regex = r'(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+?'

    try:
        output = output[-1]
        match = re.match(regex, output)
        jobState = match.group(4).strip()
        finishDate = round((datetime.datetime.now() - datetime.datetime.strptime(match.group(7).strip(), '%Y-%m-%d %H:%M')).total_seconds()/3600,2)
    except:
        #print('603')
        #exit()
        jobState = 'Never executed'
        finishDate = '90001'
    
    jobState = valueMap(jobState)
    discovery = {'data': []}
    discovery['data'].append({
        #'{#JOBNAME}': match.group(1).strip(),
        #'{#JOBTYPE}': match.group(2).strip(),
        #'{#JOBID}': match.group(3).strip()[1:-1],
        '{#JOBSTATE}': jobState,
        #'{#CREATEDAT}': match.group(5).strip(),
        #'{#STARTDAT}': match.group(6).strip(),
        '{#FINISHDAT}': finishDate,
    })
    return json.dumps(discovery,indent=4)

# Criando e testando as variáveis
try:
    _COMMAND = sys.argv[1]
    _PARAM01 = sys.argv[2]
    _FILE = f'/etc/zabbix/reports/T.veeam.{_COMMAND}'
except:
    print('601')
    exit()

# Chamada das funções:
if _COMMAND == 'jobList':
    #with open(_FILE, "x") as f:
    #    f.write(jobList())
    print(jobList())
elif _COMMAND == 'sessionList':
    #_FILE = _FILE+'_'+_PARAM01
    #with open(_FILE, "x") as f:
    #    f.write(sessionList(_PARAM01))
    print(sessionList(_PARAM01))
else:
    print('602')