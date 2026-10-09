from ldap3 import Server, Connection, ALL

def ldap_login(username, password):
    try:
        server = Server('192.168.23.141', get_info=ALL)
        conn = Connection(server,user=f"{username}@test.com",password=password,auto_bind=True)
        conn.search('dc=test,dc=com',f'(sAMAccountName={username})',attributes=['memberOf'])
        groups = str(conn.entries)
        if "kcusers" in groups:
            return True, "Login successful from kcusers group"
        else:
            return False, "User not in kcusers group"

    except Exception as e:
        return False, "Invalid username or password"

username=input('username: ')
password=input('password: ')
status,result=ldap_login(username, password)
print(result)
