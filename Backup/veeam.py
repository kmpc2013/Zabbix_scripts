
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
# 605 -> Erro na execução das funções
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
        CreationTime = jobCreationTime(jobId)
        if match:
            id = jobId
            name = match.group(1).strip()
            type = match.group(3).strip()
            repository = match.group(4).strip()
            jobstate = json.loads(session)['JOBSTATE']
            startDate = json.loads(session)['STARTDATE']
            CreationTime = CreationTime
            
            jobs.append({
                'JOBID': id, 
                'JOBNAME': name, 
                'JOBTYPE': type, 
                'REPOSITORY': repository, 
                'JOBSTATE': jobstate, 
                'STARTDATE': startDate,
                'CREATIONTIME': CreationTime
                })


    # Formata a saída como um objeto JSON
    json_output = json.dumps(jobs, indent=4)

    return json_output

def sessionList(jobId):
    result = subprocess.run(['veeamconfig', 'session', 'list', '--jobId', jobId], capture_output=True, text=True)
    regex = r'(\S.*\S)\s\s+(\S+)\s\s+(\{\S+)\s\s+(\S+)\s\s+(\S+\s\S+)'
    
    try:
        output = result.stdout.strip().split('\n')[-2]
        match = re.match(regex, output)
        jobState = match.group(4).strip()
        startDate = round((datetime.datetime.now() - datetime.datetime.strptime(match.group(5).strip(), '%Y-%m-%d %H:%M')).total_seconds()/3600,2)
    except:
        jobState = 'Never executed'
        startDate = '90001'

    jobState = valueMap(jobState)
    discovery = {}
    discovery['JOBSTATE'] = jobState
    discovery['STARTDATE'] = startDate
    return json.dumps(discovery,indent=4)

def jobCreationTime(jobId):
    result = subprocess.check_output(['veeamconfig', 'job', 'info', '--id', jobId]).decode()
    regex = r"Creation time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    creationTime = re.findall(regex, result)
    creationTime = int(datetime.datetime.strptime(creationTime[0], "%Y-%m-%d %H:%M:%S").timestamp())
    return creationTime

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
    with open(_FILE, "w") as f:
        f.write(jobList())
    with open(_FILE, "r") as f:
        print(f.read())
else:
    print('602')
