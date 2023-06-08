import digitalocean
import os
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
        region='lon1',
        image='debian-11-x64',
        #size_slug='s-2vcpu-4gb-amd',
        size_slug='s-1vcpu-1gb-amd',
        ssh_keys=[PUBLIC_KEY],
        backups=False,
        ipv6=False,
        private_networking=False,
        user_data=CONFIG,
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
    time.sleep(10)

    ip = digitalocean.Droplet.get_object(TOKEN, droplet.id).ip_address

    await print_func("`[] Restoring state...`")
    restore_state(ip)
    await print_func("`   Done`")

    await print_func(f"`[] Server IP: {ip}`")

async def stop(print_func):
    droplets = manager.get_all_droplets(tag_name='mc')
    if len(droplets) == 0:
        await print_func("`[] Server already stopped`")
        return
    
    droplet = droplets[0]

    await print_func("`[] Saving state...`")
    save_state(droplet.ip_address)
    await print_func("`   Done`")

    await print_func("`[] Destorying server...`")
    droplet.destroy()
    await print_func("`   Done`")

def restore_state(ip):
    print(os.popen(f"scp -i {PRIVATE_KEY_FILE} -o StrictHostKeyChecking=no ./state.tar root@{ip}:~/state.tar").read())
    print(os.popen(f"ssh -i {PRIVATE_KEY_FILE} -o StrictHostKeyChecking=no root@{ip} 'tar -xf ~/state.tar -C ~/'").read())

def save_state(ip):
    print(os.popen(f"ssh -i {PRIVATE_KEY_FILE} -o StrictHostKeyChecking=no root@{ip} 'tar -cf ~/state.tar ~/server'").read())
    print(os.popen(f"scp -i {PRIVATE_KEY_FILE} -o StrictHostKeyChecking=no root@{ip}:~/state.tar ./state.tar").read())
