#!/usr/bin/python2.6
from fabric.api import *
import os.path
import sys

sys.path.append(os.path.abspath('../'))

@task
def get_host_sshdkeys(sshdir="/etc/ssh"):
    run("mkdir -p /tmp/ssh")
    sudo("cp /etc/ssh/ssh_host_* /tmp/ssh")
    sudo("chown clane:wheel -R /tmp/ssh")
    local("mkdir -p hostkeys/%s/etc/ssh" %(env.host))
    local("scp -r %s:/tmp/ssh/ hostkeys/%s/etc/ssh" %(env.host, env.host))

# need to find a way to do a disk file system check before we can continue with this
def get_dir(dir):
    run("mkdir -p /tmp/%s" %(dir))
    run("ROOT_FREE_SPACE=$(df -k / | awk '{print $3}' | tail -1); echo \"$ROOT_FREE_SPACE\"")

def gitpull(dir):
    sudo("(cd %s; git pull)" %(dir))

@task
@parallel
def pullpuppet():
    gitpull("/etc/puppet")

@task
@parallel
def pullnagios():
    gitpull("/etc/nagios")
    service("nagios", "configtest")

@task
@parallel
def nagios_restart():
    service("nagios", "configtest")
    service("nagios", "reload")

@task
def service(name, action="status"):
    sudo("service %s %s" %(name, action))

@task
@parallel
def runpuppet():
    with settings(warn_only=True):
        result = sudo("puppet agent --test")

@task
def get_grub_conf():
    sudo("cat /etc/grub.conf")

@task
def omreport_storage(*args, **kwargs):
    pargs= " ".join(args)
    for k, v in kwargs.items():
        pargs+= " %s=%s" %(k, v)
    run("omreport storage %s" %(pargs))

def dmidecode(*args):
    pargs= ' '.join(args)
    sudo("dmidecode %s" %(pargs))

@task
def dmidecode_system():
    dmidecode('-t system')

@task
def hot_add_disk():
    sudo("echo '- - -' > /sys/class/scsi_host/host0/scan")

@task
def vgextend(volgroup, disk):
    sudo("vgextend %s %s" %(volgroup, disk))

@task
def lvextend(extents, lvpath):
    sudo("lvextend -l%s %s" %(extents, lvpath))

@task
def system_audit():
    data = sudo("facter -p hostname memoryfree memorysize memorytotal proc_meminfo_cached virtual")
    fd = open('system_audit.log', 'a')
    fd.write(data + '\n\n')

@task
def pullagileu():
    sudo('su - tomcat -s /bin/bash -c "cd /usr/share/tomcat5/webapps/ROOT; git pull"')

@task
def postqueue(username=None):
    if username:
        cmd = "postqueue -p | grep \"%s\" | awk '{print $1}' | grep -v \"host\" | sort | uniq -c" %(username)
    else:
        cmd = "postqueue -p | grep host | awk \"{print $2}\" | sort | uniq -c"
    run("%s" %(cmd))
