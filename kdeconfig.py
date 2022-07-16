#!/usr/bin/env python3

DOCUMENTATION = r'''
---
module: kdeconfig

short_description: Configure KDE

description: This module allows modifying KDE settings (i.e. general INI style config files)

options:
    file:
        description: Config file
        required: true
        type: str
    group:
        description: Group to look in.
        required: true
        type: list
    key:
        description: Key to look for
        required: true
        type: str
    value:
        description: Value to set
        type: str
    delete:
        description: Set to true if entry should be deleted
        type: bool
    enabled:
        description: For boolean values specify if setting should be enabled
        type: bool

author:
    - Gerrit M. Keller
'''

EXAMPLES = r'''
- name: "Set FOO=1"
  kdeconfig:
    file: "the_config_file"
    group: "a_group"
    key: "FOO"
    value: "1"

- name: "Enable BAR"
  kdeconfig:
    file: "the_config_file"
    group: "a_group"
    key: "BAR"
    enabled: true

- name: "Delete FOO=1"
  kdeconfig:
    file: "the_config_file"
    group: "a_group"
    key: "FOO"
    delete: true
'''

RETURN = r'''
cmd:
    description: Command and args used to set config.
    type: list
value_new:
    description: Config value after setting it.
    type: str
'''

from ansible.module_utils.basic import AnsibleModule

class KDEConfig:
    def __init__(self, module):
        self.module  = module
        self.args    = module.params
        self.file    = module.params['file']
        self.groups  = module.params['group']
        self.key     = module.params['key']
        self.value   = module.params['value']
        self.type    = module.params['type']
        self.delete  = module.params['delete']
        self.enabled = module.params['enabled']

        self.result = dict(
            changed=False,
            cmd=None,
        )

    def get_command(self, binary):
        cmd = [self.module.get_bin_path(binary, required=True)]
        cmd.extend(["--file", self.file])
        for g in self.groups:
            cmd.extend(["--group", g])
        cmd.extend(["--key", self.key])
        return cmd

    def read_config(self):
        read_cmd  = "kreadconfig5"
        cmd = self.get_command(read_cmd)
        rc, out, err = self.module.run_command(cmd)
        return out[:-1]

    def set_config(self):
        write_cmd = "kwriteconfig5"
        old_value = self.read_config()

        # TODO: set these only if value is changed?
        cmd = self.get_command(write_cmd)
        if self.delete:
            cmd.append("--delete")
        elif self.value:
            cmd.append(self.value)
        elif self.enabled is not None:
            cmd.extend(["--type", "bool", "true" if self.enabled else "false"])
        else:
            self.module.fail_json(msg="Invalid config! Please set one on 'value', 'delete', 'enabled'.", **self.result)

        rc, out, err = self.module.run_command(cmd)

        new_value = self.read_config()
        if new_value != old_value:
            self.result['changed'] = True
            self.result['value_new'] = new_value

        self.result['cmd'] = cmd


def main():
    module = AnsibleModule(
        argument_spec = dict(
            file      = dict(type='str', required=True),
            group     = dict(type='list', elements='str', required=True),
            key       = dict(type='str', required=True),
            value     = dict(type='str'),
            type      = dict(type='str', required=False),
            delete    = dict(type='bool'),
            enabled   = dict(type='bool')
        ),
        required_one_of= [['value', 'delete', 'enabled']]
    )
    # type: bool, num|int, path, … (str)

    c = KDEConfig(module)

    c.set_config()
    module.exit_json(**c.result)

if __name__ == '__main__':
    main()

