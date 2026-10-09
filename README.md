# Multi_Vendor_SSO_Via_MCP_Server_With_Ollama_Qwen2.5_3B

Gradio network chatbot with mcp server and ai agent for sso network automation functions (detect device type, get device backup, get serial numbers for cisco, arista and huawei)

MCP Server functions:

-detect device type

-get serial number

-get backup

download nodejs: https://nodejs.org/en/download/

npm -v

pip install virtualenv

#download python 3.12.9

virtualenv env -p C:\Users\your_pc_username_\AppData\Local\Programs\Python\Python312\python.exe

env\Scripts\activate

pip install -r requirements.txt

pip install --upgrade --force-reinstall langgraph

at one terminal run:

fastmcp dev test_tools_mcp_server.py

at another teminal run:

python network_ai_agent_gradio_local_ollama.py

How to use: https://www.youtube.com/watch?v=ht-aV1UJRf0

