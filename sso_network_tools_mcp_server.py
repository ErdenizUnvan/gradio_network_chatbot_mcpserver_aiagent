from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NetworkTools")

@mcp.tool()
def detect_device_type(ip: str, username: str, password: str) -> str:
    """Detect device type for a given IP, username, and password."""
    from netmiko import ConnectHandler, redispatch
    import time
    import re
    IDENTIFY_COMMANDS = ['show version', 'display version']

    try:
        server = {
            'device_type': 'terminal_server',
            'host': '192.168.23.145',
            'username': username,
            'password': password,
            'port': 2222,
            'conn_timeout': 80,
            'global_delay_factor': 40,
            'session_log': 'output.log'
        }

        jump_conn = ConnectHandler(**server)
    except Exception as e:
        result= f'ip:{ip},  sso_ssh:False, device_ssh:False, device_type:False'
        return str(result)
    else:
        try:
            # Hedef remote_host'a SSH bağlantı denemesi
            jump_conn.read_until_pattern(pattern='search or select one:',
                                         read_timeout=40)
            #time.sleep(2)
            # Handle the password prompt
            jump_conn.write_channel(f"{ip}\n")
            jump_conn.read_until_pattern(pattern=r"[Pp]assword:",read_timeout=50)
            jump_conn.write_channel(f"{server['password']}\n")
            prompt_out = jump_conn.read_until_pattern(pattern=r"[>#]",read_timeout=50)

            redispatch(jump_conn, device_type='autodetect')
            device_type = None
            for cmd in IDENTIFY_COMMANDS:
                jump_conn.write_channel(f'{cmd}\n')
                time.sleep(1)
                output=jump_conn.read_channel()
                if 'Huawei' in output or 'HUAWEI' in output:
                    device_type = 'huawei'
                    break
                elif 'Cisco' in output:
                    if 'Cisco IOS-XE software,' in output or 'IOS-XE ROMMON' in output:
                        device_type = 'cisco_xe'
                        break
                    elif 'Cisco IOS Software' in output:
                        device_type = 'cisco_ios'
                        break
                    elif 'Cisco Nexus Operating System' in output:
                        device_type = 'cisco_nxos'
                        break
                    elif 'Cisco IOS XR Software' in output:
                        device_type = 'cisco_xr'
                        break
                elif 'Arista' in output:
                    device_type = 'arista_eos'
                    break
            if device_type:
                result= f'ip:{ip},sso_ssh:True, device_ssh:True, device_type:{device_type}'
                return str(result)
            if not device_type:
                result= f'ip:{ip},sso_ssh:True, device_ssh:True, device_type:{device_type}'
                return str(result)
        except Exception as e:
            result= f'ip:{ip},sso_ssh:True, device_ssh:False, device_type:False'
            return str(result)
        finally:
            jump_conn.disconnect()

@mcp.tool()
def backup_device(ip: str, username: str, password: str) -> str:
    """Get backup for a given IP, username, password and device type"""
    from netmiko import ConnectHandler, redispatch
    import time
    import re
    from datetime import datetime
    import os
    import json

    IDENTIFY_COMMANDS = ['show version', 'display version']

    try:
        server = {
            'device_type': 'terminal_server',
            'host': '192.168.23.145',
            'username': username,
            'password': password,
            'port': 2222,
            'conn_timeout': 80,
            'global_delay_factor': 40,
            'session_log': 'output.log'
        }

        jump_conn = ConnectHandler(**server)
    except Exception as e:
        result= f'ip:{ip},  sso_ssh:False, device_ssh:False, device_type:False'
        return str(result)
    else:
        try:
            # Hedef remote_host'a SSH bağlantı denemesi
            jump_conn.read_until_pattern(pattern='search or select one:',
                                         read_timeout=40)
            jump_conn.write_channel(f"{ip}\n")
            jump_conn.read_until_pattern(pattern=r"[Pp]assword:",read_timeout=50)
            jump_conn.write_channel(f"{server['password']}\n")
            prompt_out = jump_conn.read_until_pattern(pattern=r"[>#]",read_timeout=50)
            redispatch(jump_conn, device_type='autodetect')
            device_type = None
            for cmd in IDENTIFY_COMMANDS:
                jump_conn.write_channel(f'{cmd}\n')
                time.sleep(1)
                output=jump_conn.read_channel()
                if 'Huawei' in output or 'HUAWEI' in output:
                    device_type = 'huawei'
                    try:
                        jump_conn.write_channel('display current-configuration\n')
                        time.sleep(3)
                        output_backup = jump_conn.read_channel()
                        now=datetime.now()
                        backup=f'{ip}_{device_type}_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}'
                        with open(f'{backup}.txt','w') as f:
                            f.write(output_backup)
                        result=f'{backup}.txt at folder:{os.getcwd()}'
                        return str(result)
                    except Exception as e:
                        return str(e)
                    break
                elif 'Cisco' in output:
                    device_type='cisco_ios'
                    try:
                        jump_conn.write_channel('show run\n')
                        time.sleep(2)
                        output_backup = jump_conn.read_channel()
                        now=datetime.now()
                        backup=f'{ip}_{device_type}_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}'
                        with open(f'{backup}.txt','w') as f:
                            f.write(output_backup)
                        result=f'{backup}.txt at folder:{os.getcwd()}'
                        return str(result)
                    except Exception as e:
                        return str(e)
                    break
                elif 'Arista' in output:
                    device_type = 'arista_eos'
                    try:
                        jump_conn.write_channel('show run\n')
                        time.sleep(2)
                        output_backup = jump_conn.read_channel()
                        now=datetime.now()
                        backup=f'{ip}_{device_type}_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}'
                        with open(f'{backup}.txt','w') as f:
                            f.write(output_backup)
                        result=f'{backup}.txt at folder:{os.getcwd()}'
                        return str(result)
                    except Exception as e:
                        return str(e)
                    break

            if not device_type:
                result= f'ip:{ip},sso_ssh:True, device_ssh:True, device_type:{device_type}  Back up alinamadi'
                return str(result)
        except Exception as e:
            result= f'ip:{ip},sso_ssh:True, device_ssh:False, device_type:False'
            return str(result)
        finally:
            jump_conn.disconnect()

@mcp.tool()
def serial_device(ip: str, username: str, password: str) -> str:
    """Detect device type for a given IP, username, and password."""
    from netmiko import ConnectHandler, redispatch
    import time
    import re
    IDENTIFY_COMMANDS = ['show version', 'display version']
    try:
        server = {
            'device_type': 'terminal_server',
            'host': '192.168.23.145',
            'username': username,
            'password': password,
            'port': 2222,
            'conn_timeout': 80,
            'global_delay_factor': 40,
            'session_log': 'output.log'
        }
        jump_conn = ConnectHandler(**server)
    except Exception as e:
        result= {'ip':ip,'sso_ssh':False, 'device_ssh':False, 'device_type':False}
        return result
    else:
        try:
            # Hedef remote_host'a SSH bağlantı denemesi
            jump_conn.read_until_pattern(pattern='search or select one:',
                                         read_timeout=40)
            #time.sleep(2)
            # Handle the password prompt
            jump_conn.write_channel(f"{ip}\n")
            jump_conn.read_until_pattern(pattern=r"[Pp]assword:",read_timeout=50)
            jump_conn.write_channel(f"{server['password']}\n")
            prompt_out = jump_conn.read_until_pattern(pattern=r"[>#]",read_timeout=50)

            redispatch(jump_conn, device_type='autodetect')
            device_type = None
            seri=None
            for cmd in IDENTIFY_COMMANDS:
                jump_conn.write_channel(f'{cmd}\n')
                time.sleep(1)
                output=jump_conn.read_channel()
                if 'Huawei' in output or 'HUAWEI' in output:
                    device_type = 'huawei'
                    jump_conn.write_channel(f'display esn\n')
                    time.sleep(1)
                    output2=jump_conn.read_channel()
                    data=output2.splitlines()
                    for x in data:
                        if x.startswith(' ESN of device: '):
                            seri=x.split(' ESN of device: ')[1]
                    break
                elif 'Cisco' in output:
                    device_type = 'cisco_ios'
                    data=output.splitlines()
                    for x in data:
                        if x.startswith('Processor board ID'):
                            seri=x.split('Processor board ID')[1]
                    break
                elif 'Arista' in output:
                    device_type = 'arista_eos'
                    data=output.splitlines()
                    for x in data:
                        if x.startswith('Serial number: '):
                            seri=x.split('Serial number: ')[1]
                    break
            if device_type and seri:
                result= {'device_type':device_type,'seri':seri}
                return result
            if device_type and not seri:
                result= {'device_type':device_type,'seri':False}
                return result
            if not device_type and not seri:
                result= {'device_type':False,'seri':False}
                return result
        except Exception as e:
            result= {'ip':ip,'sso_ssh':True, 'device_ssh':False, 'device_type':False,'seri':False}
            return result
        finally:
            jump_conn.disconnect()

if __name__ == "__main__":
    mcp.run(transport="stdio")
