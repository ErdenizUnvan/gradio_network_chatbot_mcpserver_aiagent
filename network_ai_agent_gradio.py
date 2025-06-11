import asyncio
import gradio as gr
from ldap3 import Server, Connection, ALL, core
from openai import OpenAI
import ast
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
import ipaddress
import platform
import os
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
MODEL_DIR = r"C:\Users\Dell\llama3_2\mcp\project\facebook-bart-large-mnli"
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, local_files_only=True)
classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer,
                      hypothesis_template="This request is about {}.")
candidate_labels = ["detect device type", "get device backup", "get serial number","other"]


system_prompt = (
    "You are a function-calling AI agent.\n"
    "The function you need to call will be selected according to the user's input for you and it will be informed to you\n"
    "Only provide the outcome of the function, do not make any additonal comments or statements\n"
)

chat_model = ChatOllama(model="llama3.2").with_config({"system_prompt": system_prompt})
Settings.llm = Ollama(model="llama3.2", base_url="http://127.0.0.1:11434", request_timeout=120.0)

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
    result = classifier(user_input, candidate_labels)
    top_label = result['labels'][0]
    top_score = result['scores'][0]
    THRESHOLD = 0.55

    if top_label == 'other' or top_score < THRESHOLD:
        return "Out of scope as function!"


    # IP bilgisi kullanıcıdan çekilecek, username & password state’ten otomatik alınacak
    input_query = (
        f"the sentence is: \"{user_input}.\" "
        "Extract only the values for keys of ip and device type from this sentence. "
        "use lower letters for devicetype "
        "If you can not find the value for key of ip or device type, then use None as value for the key instead. "
        "Return only the result values as either matching ones or None in a dictionary:  "
        "{'ip':'','devicetype':''}  Do not generate code. Do not return anything else except the result dictionary!"
    )

    llama_model = Settings.llm
    try:
        response = llama_model.complete(prompt=input_query)
        result_dict = ast.literal_eval(str(response))
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

    if top_label == 'detect device type':
        top_label = 'detect_device_type'
        query = 'detect device type'
        content = f"{query} for ip:{ip} user:{username} pass:{password}"

    else:
        if top_label=='get device backup':
            top_label = 'backup_device'
            query = 'get device backup'
        elif top_label=='get serial number':
            top_label = 'serial_device'
            query = 'get serial number'
        devicetype = result_dict.get('devicetype', None)
        if not devicetype:
            return "Could not extract device type."
        print(devicetype)
        content = f"{query} for ip:{ip} user:{username} pass:{password} devicetype: {devicetype} "

    print(content)
    try:
        server_params = StdioServerParameters(command="python", args=["sso_network_tools_mcp_server.py"])
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

    with gr.Column():
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

    def handle_login(user, pw):
        success, msg = ldap_login(user, pw)
        return success, msg, user if success else "", pw if success else "", gr.update(visible=success)

    async def handle_query_wrapper(query, username, password):
        return await agent_pipeline(query, username, password)

    login_btn.click(handle_login,
                    inputs=[username, password],
                    outputs=[login_status, login_output, username_state, password_state, chat_area])

    query_btn.click(
        fn=handle_query_wrapper,
        inputs=[user_query, username_state, password_state],
        outputs=agent_response
    )

demo.launch()
