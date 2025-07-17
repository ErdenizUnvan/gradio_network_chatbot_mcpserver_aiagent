import asyncio
import gradio as gr
from ldap3 import Server, Connection, ALL, core
import ast
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import ipaddress
import platform
from langchain_openai import ChatOpenAI
import os
from enum import Enum
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser

def ping_device(ip):
    # Check the platform type
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    null = 'nul' if platform.system().lower() == 'windows' else '/dev/null'
    response = os.system(f"ping {param} 1 {ip} > {null} 2>&1")
    return response == 0

def validate_ip(ip):
    try:
        ipaddress.ip_network(ip, strict=False)
        return True
    except ValueError:
        return False

### === MODEL AYARLARI === ###

class Category(str, Enum):
    detect_device_type = 'detect device type'
    backup_device = 'get device backup'
    serial_device = 'get serial number'
    other = 'other'

#BaseModel
#veri doğrulama (data validation) ve modelleme için kullanılır.

class ResultModel(BaseModel):
    result: Category

candidate_labels = [e.value for e in Category]

system_prompt = (
    "You are a function-calling AI agent.\n"
    "The function you need to call will be selected according to the user's input for you and it will be informed to you\n"
    "Only provide the outcome of the function, do not make any additonal comments or statements\n"
)

os.environ['OPENAI_API_KEY'] = ''

#chat_model = ChatOllama(model="llama3.2").with_config({"system_prompt": system_prompt})
chat_model = ChatOpenAI(model="gpt-3.5-turbo",
 temperature=0).with_config({
    "system_prompt": system_prompt
})

### === LDAP LOGIN === ###
def ldap_login(username, password):
    server = Server('ldap://10.1.100.133', get_info=ALL)
    user_dn = f'{username}@test.com'
    try:
        conn = Connection(server, user=user_dn, password=password, authentication='SIMPLE', auto_bind=True)
        conn.search('dc=test,dc=com', f'(sAMAccountName={username})', attributes=['memberOf'])
        if conn.entries:
            for g in conn.entries[0]['memberOf']:
                if 'CN=kcusers' in str(g):
                    return True, "Login successful"
            return False, "User not in kcusers group"
        else:
            return False, "User not found"
    except core.exceptions.LDAPBindError:
        return False, "Invalid username or password"

### === AGENT WORKFLOW === ###
async def agent_pipeline(user_input, username, password):
    # IP bilgisi kullanıcıdan çekilecek, username & password state’ten otomatik alınacak
    input_query = (
        f"the sentence is: \"{user_input}.\" "
        "Extract only the value for keys of ip from this sentence. "
        "If you can not find the value for key of ip, then use None as value for the key instead. "
        "Return only the result value as either matching one or None in a dictionary:  "
        "{'ip':''}  Do not generate code. Do not return anything else except the result dictionary!"
    )

    try:
        ip_model = ChatOpenAI(model="gpt-3.5-turbo",temperature=0)
        ip_response=ip_model.invoke(input_query)
        #response = llama_model.complete(prompt=input_query)
        result_dict = ast.literal_eval(str(ip_response.content))
    except Exception as e:
        return f"Error extracting IP: {e}"

    ip = result_dict.get('ip', None)
    print(ip)
    if not ip:
        return "Could not extract IP address."

    if not validate_ip(ip):
        return "IP address is not correct for ipV4."

    if not ping_device(ip):
        return f"Can not ping ip address:{ip}"
    try:

        parser = PydanticOutputParser(pydantic_object=ResultModel)
        intent_model = ChatOpenAI(model="gpt-3.5-turbo",
        temperature=0)
        prompt = (
        "You are an AI assistant that classifies user queries into a category.\n"
        "Choose one of the following categories:\n"
        f"{', '.join(candidate_labels)}\n\n"
        f"User query: \"{user_input}\"\n\n"
        f"Respond **only** in this exact JSON format:\n\n"
        "{\"result\": \"<one of: detect device type, get device backup, get serial number, other>\"}"
        )

        intent_response = intent_model.invoke(prompt)

        try:
            parsed = parser.parse(intent_response.content)
        except Exception as e:
            return f"Intent parsing error: {e}"

        top_label = parsed.result
        print(top_label)

        if top_label == Category.other:
            return "Out of scope as function!"

        if top_label == Category.detect_device_type:
            top_label = 'detect_device_type'
            query = 'detect device type'
        elif top_label==Category.backup_device:
            top_label = 'backup_device'
            query = 'get device backup'
        elif top_label==Category.serial_device:
            top_label = 'serial_device'
            query = 'get serial number'
        else:
            return "Out of scope as function!"

        content = f"{query} for ip:{ip} user:{username} pass:{password}"
        #print(content)

        server_params = StdioServerParameters(command="python", args=["sso_network_tools_mcp_serverv2.py"])
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                selected_tools = [tool for tool in tools if tool.name == top_label]
                agent = create_react_agent(chat_model, selected_tools)

                msg = {"messages": [{"role": "user", "content": content}]}
                response = await agent.ainvoke(msg)

                for m in response["messages"]:
                    if m.type == "tool":
                        return m.content
                return "No function output returned."
    except Exception as e:
        return f"Agent error: {e}"

### === GRADIO ARAYÜZÜ === ###
with gr.Blocks(title="LDAP + AI Agent Chat") as demo:
    login_status = gr.State(False)
    username_state = gr.State("")
    password_state = gr.State("")


    with gr.Column() as login_area:
        gr.Markdown("##LDAP Login")
        username = gr.Textbox(label="Username")
        password = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_output = gr.Textbox(label="Login Status", interactive=False)

    with gr.Column(visible=False) as chat_area:
        gr.Markdown("##MCP Network AI Agent")
        user_query = gr.Textbox(label="Your Network Command (e.g. detect device type for ip:10.1.1.1)")
        agent_response = gr.Textbox(label="Agent Output")
        query_btn = gr.Button("Run MCP Agent")

    def handle_login(username, password):
        success, msg = ldap_login(username, password)
        return (success,
                msg,
                username if success else "",
                password if success else "",
                gr.update(visible=success),
                gr.update(visible=not success)
                )

    async def handle_query_wrapper(query, username, password):
        return await agent_pipeline(query, username, password)

    login_btn.click(handle_login,
                    inputs=[username, password],
                    outputs=[login_status,
                             login_output,
                             username_state,
                             password_state,
                             chat_area,
                             login_area])

    query_btn.click(
        fn=handle_query_wrapper,
        inputs=[user_query, username_state, password_state],
        outputs=agent_response
    )

demo.launch()
