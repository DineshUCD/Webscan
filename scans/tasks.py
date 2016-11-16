from __future__ import absolute_import, unicode_literals
from celery import shared_task
import subprocess, os

@shared_task
def add():
    p = subprocess.Popen(['/bin/ls', '-l'], shell=True, stdout=subprocess.PIPE)
    lines = list()
    while True:
        output = p.stdout.readline()
        if output:
            lines.append(output)
        else: 
            break
    return lines
