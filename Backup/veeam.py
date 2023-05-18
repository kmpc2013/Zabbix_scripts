
"""
######################################################################
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
# 605 -> Erro na execução das funções
######################################################################
# Execute:
# python3 veeam.py jobList .
######################################################################
"""

import subprocess
import re
import json
import sys
import datetime
import inspect

def valueMap(jobState):
    nome_funcao_chamadora  = inspect.getframeinfo(inspect.currentframe().f_back).function
    if nome_funcao_chamadora == 'sessionList':
        dict = {
            'Success': 1,
            'Running': 2,
            'Never executed': 3,
            'Stopped': 4,
            'Failed': 5,
            'Warning': 6,
            'Unknown': 7
        }
    try:
        result = dict[jobState]
    except:
        result = dict['Unknown']
    return result

def veeamVersionRegex():
    veeamVersion = subprocess.check_output(['veeamconfig', '-v']).decode()
    veeamVersion = int(veeamVersion[1:2])
    if veeamVersion == 6:
        regex = r'(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+?'
    elif veeamVersion == 5:
        regex = r'(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+(\S.*)\s\s+?'
    else:
        print('604')
        exit()
    return regex

def jobList():
    # Executa o comando e armazena o resultado na variável `output`
    output = subprocess.check_output(['veeamconfig', 'job', 'list']).decode()
    output = output.splitlines()[1:]

    # Extrai os dados relevantes da saída do comando usando expressões regulares
    regex = r'(\S+.+)\s\s+(\S+.+)\s\s+(\S+.+)\s\s+(\S+.+)\s\s+?'
    jobs = []
    for line in output:
        match = re.match(regex, line)
        jobId = match.group(2).strip()[1:-1]
        session = sessionList(jobId)
        if match:
            id = jobId
            name = match.group(1).strip()
            type = match.group(3).strip()
            repository = match.group(4).strip()
            jobstate = json.loads(session)['JOBSTATE']
            startDate = json.loads(session)['STARTDATE']
            
            jobs.append({
                'JOBID': id, 
                'JOBNAME': name, 
                'JOBTYPE': type, 
                'REPOSITORY': repository, 
                'JOBSTATE': jobstate, 
                'STARTDATE': startDate
                })


    # Formata a saída como um objeto JSON
    json_output = json.dumps(jobs, indent=4)

    return json_output

def sessionList(jobId):
    result = subprocess.run(['veeamconfig', 'session', 'list', '--jobId', jobId], capture_output=True, text=True)
    output = result.stdout.strip().split('\n')[1:-1]

    regex = veeamVersionRegex()

    try:
        output = output[-1]
        match = re.match(regex, output)
        jobState = match.group(4).strip()
        startDate = round((datetime.datetime.now() - datetime.datetime.strptime(match.group(6).strip(), '%Y-%m-%d %H:%M')).total_seconds()/3600,2)
    except:
        jobState = 'Never executed'
        startDate = '90001'

    jobState = valueMap(jobState)
    discovery = {}
    discovery['JOBSTATE'] = jobState
    discovery['STARTDATE'] = startDate
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
try:
    if _COMMAND == 'jobList':
        with open(_FILE, "w") as f:
            f.write(jobList())
    else:
        print('602')
except:
    print('604')