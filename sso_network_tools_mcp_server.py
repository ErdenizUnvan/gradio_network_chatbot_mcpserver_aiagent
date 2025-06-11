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
            'host': '10.1.100.88',
            'username': username,
            'password': password,
            'port': 22,
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
            jump_conn.write_channel(f"ssh {username}@{ip}\n")
            time.sleep(2)
            # Handle the password prompt
            jump_conn.read_until_pattern(pattern=r"Password|password|PASSWORD:", read_timeout=50)
            jump_conn.write_channel(f"{password}\n")
            time.sleep(1)
            read_for_sso_problems = jump_conn.read_channel()
            sso_problems=["Received disconnect from","Disconnected from"]
            for x in sso_problems:
                if x in read_for_sso_problems:
                    raise ValueError()
            redispatch(jump_conn, device_type='autodetect')
            time.sleep(1)
            device_type = None
            for cmd in IDENTIFY_COMMANDS:
                output=jump_conn.send_command(cmd)
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
def backup_device(ip: str, username: str, password: str, devicetype: str) -> str:
    """Get backup for a given IP, username, password and device type"""
    from netmiko import ConnectHandler, redispatch
    import time
    import re
    import os
    from datetime import datetime

    try:
        server = {
            'device_type': 'terminal_server',
            'host': '10.1.100.88',
            'username': username,
            'password': password,
            'port': 22,
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
            jump_conn.write_channel(f"ssh {username}@{ip}\n")
            time.sleep(2)
            # Handle the password prompt
            jump_conn.read_until_pattern(pattern=r"Password|password|PASSWORD:", read_timeout=50)
            jump_conn.write_channel(f"{password}\n")
            time.sleep(1)
            read_for_sso_problems = jump_conn.read_channel()
            sso_problems=["Received disconnect from","Disconnected from"]
            for x in sso_problems:
                if x in read_for_sso_problems:
                    raise ValueError()
            redispatch(jump_conn, device_type=devicetype)
            time.sleep(1)

            if devicetype=='huawei':
                try:
                    output_backup=jump_conn.send_command('display current-configuration')
                    now=datetime.now()
                    backup=f'{ip}_{devicetype}_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}'
                    with open(f'{backup}.txt','w') as f:
                        f.write(output_backup)
                    result=f'{backup}.txt at folder:{os.getcwd()}'
                    return str(result)
                except Exception as e:
                    return str(e)

            elif devicetype in ['cisco_xe','cisco_ios','cisco_nxos','cisco_xr','arista_eos']:
                try:
                    output_backup=jump_conn.send_command('show run')
                    now=datetime.now()
                    backup=f'{ip}_{devicetype}_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}'
                    with open(f'{backup}.txt','w') as f:
                        f.write(output_backup)
                    result=f'{backup}.txt at folder:{os.getcwd()}'
                    return str(result)
                except Exception as e:
                    return str(e)

            else:
                result= f'ip:{ip},sso_ssh:True, device_ssh:True, device_type:False. Backup could not be taken'
                return str(result)
        except Exception as e:
            result= f'ip:{ip},sso_ssh:True, device_ssh:False, device_type:False. Backup could not be taken.'
            return str(result)
        finally:
            jump_conn.disconnect()

@mcp.tool()
def serial_device(ip: str, username: str, password: str, devicetype: str) -> str:
    """Get serial number for a given IP, username, password and device type"""
    from netmiko import ConnectHandler, redispatch
    import time
    import re
    import os
    from datetime import datetime

    try:
        server = {
            'device_type': 'terminal_server',
            'host': '10.1.100.88',
            'username': username,
            'password': password,
            'port': 22,
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
            jump_conn.write_channel(f"ssh {username}@{ip}\n")
            time.sleep(2)
            # Handle the password prompt
            jump_conn.read_until_pattern(pattern=r"Password|password|PASSWORD:", read_timeout=50)
            jump_conn.write_channel(f"{password}\n")
            time.sleep(1)
            read_for_sso_problems = jump_conn.read_channel()
            sso_problems=["Received disconnect from","Disconnected from"]
            for x in sso_problems:
                if x in read_for_sso_problems:
                    raise ValueError()
            redispatch(jump_conn, device_type=devicetype)
            time.sleep(1)

            if devicetype=='huawei':
                try:
                    output_seri=jump_conn.send_command('display device manufacture-info')
                    data=output_seri.splitlines()
                    for line in data:
                        if line.startswith('0'):
                            sonuc=line.split()
                            seri=sonuc[2]
                    return str(seri)

                except Exception as e:
                    return str(e)

            elif devicetype in ['cisco_xe','cisco_ios','cisco_nxos','arista_eos']:
                try:
                    output_seri=jump_conn.send_command('show version',use_textfsm=True)
                    if devicetype in ['cisco_xe','cisco_ios']:
                        seri=output_seri[0]['serial'][0]
                        return str(seri)
                    elif devicetype=='cisco_nxos':
                        seri=output_seri[0]['serial']
                        return str(seri)
                    elif devicetype=='arista_eos':
                        seri=output_seri[0]['serial_number']
                        return str(seri)
                except Exception as e:
                    return str(e)

            elif devicetype=='cisco_xr':
                try:
                    output_seri=jump_conn.send_command('show inventory',use_textfsm=True)
                    seri=[x['sn'] for x in output_seri if x['name']=='Rack 0'][0]
                    return str(seri)
                except Exception as e:
                    return str(e)

            else:
                result= f'ip:{ip},sso_ssh:True, device_ssh:True, device_type:False. Serial number could not be taken'
                return str(result)

        except Exception as e:
            result= f'ip:{ip},sso_ssh:True, device_ssh:False, device_type:False. Serial number could not be taken.'
            return str(result)
        finally:
            jump_conn.disconnect()

if __name__ == "__main__":
    mcp.run(transport="stdio")
