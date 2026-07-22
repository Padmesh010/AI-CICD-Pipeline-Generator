from typing import Dict

def generate_ansible_playbook(
    app_name: str = "my-app",
    deploy_host: str = "webservers",
    target_port: int = 8000
) -> Dict[str, str]:
    """Generate standardized Ansible deployment playbook files."""

    site_yml = f"""---
- name: Deploy {app_name} Application Workloads
  hosts: {deploy_host}
  become: true
  vars:
    app_name: "{app_name}"
    app_port: {target_port}
    docker_image: "{app_name}:latest"

  roles:
    - deploy
"""

    inventory_ini = f"""[webservers]
192.168.1.10 ansible_user=deploy_user ansible_ssh_private_key_file=~/.ssh/id_rsa
192.168.1.11 ansible_user=deploy_user ansible_ssh_private_key_file=~/.ssh/id_rsa

[all:vars]
ansible_python_interpreter=/usr/bin/python3
"""

    tasks_main = f"""---
- name: Ensure Docker engine is installed and running
  ansible.builtin.service:
    name: docker
    state: started
    enabled: true

- name: Pull latest production image
  community.docker.docker_image:
    name: "{{{{ docker_image }}}}"
    source: pull
    force_source: true

- name: Stop and remove existing container
  community.docker.docker_container:
    name: "{{{{ app_name }}}}"
    state: absent

- name: Start updated application container
  community.docker.docker_container:
    name: "{{{{ app_name }}}}"
    image: "{{{{ docker_image }}}}"
    state: started
    restart_policy: always
    published_ports:
      - "{{{{ app_port }}}}:{{{{ app_port }}}}"
    env:
      ENVIRONMENT: "production"
"""

    return {
        "site.yml": site_yml,
        "inventory.ini": inventory_ini,
        "roles/deploy/tasks/main.yml": tasks_main
    }
