import digitalocean
import os
import subprocess
import time

TOKEN = os.getenv('DIGITALOCEAN_ACCESS_TOKEN')
with open('cloud-config.yaml', 'r') as f:
    CONFIG = f.read()
with open('id_rsa.pub', 'r') as f:
    PUBLIC_KEY = f.read()
PRIVATE_KEY_FILE = 'id_rsa'

manager = digitalocean.Manager(token=TOKEN)

def wait_for_complete(droplet):
    while True:
        time.sleep(1)
        actions = droplet.get_actions()
        for action in actions:
            action.load()
            if action.status == 'completed':
                return

async def start(print_func):
    droplets = manager.get_all_droplets(tag_name='mc')
    if len(droplets) > 0:
        await print_func("`[] Server already running`")
        return
    
    await print_func("`[] Creating instance...`")
    droplet = digitalocean.Droplet(
        token=TOKEN,
        name='mc-main',
        region='ams3',
        image='ubuntu-22-10-x64',
        size_slug='s-2vcpu-4gb-amd',
        #size_slug='s-1vcpu-1gb-amd',
        ssh_keys=[PUBLIC_KEY],
        backups=False,
        ipv6=False,
        private_networking=False,
        #user_data=CONFIG,
        monitoring=True
    )

    droplet.create()

    tag = digitalocean.Tag(
        token=TOKEN,
        name='mc'
    )
    tag.create()
    tag.add_droplets([droplet])

    wait_for_complete(droplet)

    await print_func("`   Done`")

    print(droplet)

    # Wait for IP to be assigned
    time.sleep(20)

    ip = digitalocean.Droplet.get_object(TOKEN, droplet.id).ip_address

    await print_func("`[] Attaching volume...`")

    volumes = manager.get_all_volumes()
    for volume in volumes:
        if volume.name == 'volume-mc':
            volume.attach(droplet.id, 'ams3')
            break

    time.sleep(20)

    await print_func("`   Done`")
    await print_func(f"`[] Starting server...`")

    launch_java_server(ip)

    await print_func("`   Done`")
    await print_func(f"`[] Server IP: {ip}`")

async def stop(print_func):
    droplets = manager.get_all_droplets(tag_name='mc')
    if len(droplets) == 0:
        await print_func("`[] Server already stopped`")
        return
    
    droplet = droplets[0]

    await print_func("`[] Destorying server...`")
    droplet.destroy()
    await print_func("`   Done`")

def run_remote_cmd(ip, cmd):
    subprocess.call(['ssh', '-i', PRIVATE_KEY_FILE, '-o', 'StrictHostKeychecking=no', f'root@{ip}', f'\'{cmd}\''])

def launch_java_server(ip):
    run_remote_cmd(ip, "apt-get update")
    run_remote_cmd(ip, "apt-get install -y openjdk-8-jre")
    run_remote_cmd(ip, "mkdir -p /mnt/volume_mc")
    run_remote_cmd(ip, "mount -o discard,defaults,noatime /dev/disk/by-id/scsi-0DO_Volume_volume-mc /mnt/volume_mc")
    run_remote_cmd(ip, "java -Xmx1024M -Xms1024M -jar /mnt/volume_mc/mc-server/forge-1.7.10-10.13.4.1614-1.7.10-universal.jar --nogui")
