"""
Command line tool for Jaseci
"""

import click
from click_shell import shell
import os.path
import pickle
import functools
import json
import requests
from inspect import signature

from jaseci.utils.mem_hook import mem_hook
from jaseci.utils.utils import copy_func
from jaseci.master import master as master_class

session = {
    "filename": "js.session",
    "master": master_class(h=mem_hook()),
    "mem-only": False
}

connection = {'url': None, 'token': None, 'headers': None}


def blank_func():
    """No help provided"""
    pass


@shell(prompt='jaseci > ', intro='Starting Jaseci Shell...')
@click.option('--filename', '-f', default="js.session",
              help="Specify filename for session state.")
@click.option('--mem-only', '-m', is_flag=True,
              help="Set true to not save file for session.")
def cli(filename, mem_only):
    """
    The Jaseci Command Line Interface
    """
    session['mem-only'] = mem_only
    session['filename'] = filename if not mem_only else None
    if (not mem_only and os.path.isfile(filename)):
        session['master'] = pickle.load(open(filename, 'rb'))


def remote_api_call(payload, api_name):
    """Constructs and issues call to remote server"""
    if(api_name.startswith('api_')):
        path = '/jac/'+api_name[4:]
    elif(api_name.startswith('admin_api_')):
        path = '/admin/'+api_name[10:]
    ret = requests.post(connection['url']+path,
                        data=payload,
                        headers=connection['headers'])
    if ret.status_code > 205:
        ret = f"Status Code Error {ret.status_code}"
    else:
        ret = ret.json()
    return ret


def interface_api(api_name, **kwargs):
    """
    Interfaces Master apis after processing arguments/parameters
    from cli
    """
    if('code' in kwargs):
        if (os.path.isfile(kwargs['code'])):
            with open(kwargs['code'], 'r') as file:
                kwargs['code'] = file.read()
        else:
            click.echo(f"Code file {kwargs['code']} not found!")
            return
    if('ctx' in kwargs):
        kwargs['ctx'] = json.loads(kwargs['ctx'])
    if(connection['token'] and connection['url']):
        click.echo(json.dumps(
            remote_api_call(kwargs, api_name), indent=2
        ))
    else:
        click.echo(json.dumps(
            session['master'].general_interface_to_api(kwargs, api_name), indent=2
        ))
    if not session['mem-only']:
        pickle.dump(session['master'], open(session['filename'], 'wb'))


def extract_api_tree():
    """
    Generates a tree of command group names and function
    signatures in leaves from API function names in Master
    """
    api_funcs = {}
    for i in dir(session['master']):
        if (i.startswith('api_') or i.startswith('admin_api_')):
            # Get function names and signatures
            func_str = i[4:] if i.startswith('api_') else i[10:]
            cmd_groups = func_str.split('_')
            func_sig = signature(getattr(session['master'], i))

            # Build hierarchy of command groups
            api_root = api_funcs
            for j in cmd_groups:
                if (j not in api_root.keys()):
                    api_root[j] = {}
                api_root = api_root[j]
            api_root['leaf'] = [i, func_sig]
    return api_funcs


def build_cmd(group_func, func_name, api_name):
    """
    Generates Click function with options for each command
    group and leaf signatures
    """
    f = functools.partial(
        copy_func(interface_api, func_name), api_name=api_name)
    f.__name__ = func_name
    f.__doc__ = session['master'].get_api_doc(api_name)
    func_sig = session['master'].get_api_signature(api_name)
    for i in func_sig.parameters.keys():
        if(i == 'self'):
            continue
        p_default = func_sig.parameters[i].default
        p_type = func_sig.parameters[i].annotation
        if(p_type != int and p_type != bool):
            p_type = str
        if(p_default is not func_sig.parameters[i].empty):
            f = click.option(
                f'-{i}', default=p_type(p_default), required=False,
                type=p_type)(f)
        else:
            f = click.option(
                f'-{i}', required=True, type=p_type)(f)
    return group_func.command()(f)


def cmd_tree_builder(location, group_func=cli, cmd_str=''):
    """
    Generates Click command groups from API tree recursively
    """
    for i in location.keys():
        loc = location[i]
        if ('leaf' in loc):
            build_cmd(group_func, i, loc['leaf'][0])
            continue
        else:
            f = copy_func(blank_func, i)
            f.__doc__ = f'Group of `{(cmd_str+" "+i).lstrip()}` commands'
            new_func = group_func.group()(f)
        cmd_tree_builder(loc, new_func, cmd_str+' '+i)


@click.command()
@click.argument("url", type=str, required=True)
@click.option('--username', '-u', required=True, prompt=True,
              help="Username to be used for login.")
@click.password_option(help="Password to be used for login.",
                       confirmation_prompt=False)
def login(url, username, password):
    url = url[:-1] if url[-1] == '/' else url
    payload = {'email': username, 'password': password}
    r = requests.post(url+'/user/token/', data=payload).json()
    if('token' in r.keys()):
        connection['token'] = r['token']
        connection['url'] = url
        connection['headers'] = {
            'Authorization': 'token ' + r['token']}
        click.echo("Login successful!")
    else:
        click.echo(f"Login failed!\n{r.json()}")


cli.add_command(login)
cmd_tree_builder(extract_api_tree())


def main():
    cli()


if __name__ == '__main__':
    main()