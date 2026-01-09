# gradio_network_chatbot_mcpserver_aiagent

gradio network chatbot with mcp server and ai agent for sso network automation functions (detect device type, get device backup, get serial numbers for cisco, arista and huawei)

intent classification model: facebook-bart-large-mnli

function calling and managing model: llama 3.2 3B

Single Sign On with Ldap server

Gradio Integration

MCP Server functions:

-detect device type

-get serial number

-get backup

python version: 3.12.9

pip install huggingface_hub

pip install transformers

pip install torch

pip install tensorflow

download facebook/bart-large-mnli model from hugginf face to your local env.:

python compare_intent_model_save.py

make sure ollama is working on your local env.:

for details check: setting up ollama for local llama.ipynb

download nodejs: https://nodejs.org/en/download/

npm -v

pip install langchain_core==1.2.6

pip install langchain_openai

pip install --upgrade --force-reinstall langgraph

pip install langgraph==1.0.5

pip install langchain_mcp_adapters 

pip install langchain_ollama 

pip install mcp==1.6.0

pip install fastmcp==2.2.6

pip install llama_index

pip install llama-index-llms-ollama 

pip install uv

pip install ldap3

pip install gradio==6.2.0

pip install netmiko

at one terminal run:

fastmcp dev sso_network_tools_mcp_server.py

at another teminal run:

python network_ai_agent_gradio.py

How to use: https://www.youtube.com/watch?v=6ABHe4Czy3o

