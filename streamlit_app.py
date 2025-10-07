import streamlit as st
from autoppa.agent import Agent, Role, Message
import time
import json


@st.cache_resource(show_spinner="Initializing AI agent...")
def init_agent(task_num, system_prompt=None, max_context_len=100000):
    agent = Agent(task_num,
                  system_prompt=system_prompt,
                  max_context_len=max_context_len)
    
    return agent

def role_to_emoji(role):
    if role == Role.SYSTEM:
        return ":material/keyboard:"
    if role == Role.USER:
        return ":material/person:"
    if role == Role.ASSISTANT:
        return ":material/robot_2:"
    if role == Role.TOOL:
        return ":material/build:"

st.title("AutoPPA")
st.text("PPAgent for RTL code optimization")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Display chat history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"].value,
                         avatar=role_to_emoji(message["role"])):
        
        with st.container(height=500):
            if message["role"] == Role.ASSISTANT:
                st.code(message["content"], language="verilog", wrap_lines=True)
            else:
                st.text(message["content"])


with open('benchmark/metadata.json') as f:
    task_info = json.load(f)

with st.sidebar:
    run_agent = st.button("Run Agent")
    task_num = st.number_input("Task number", min_value=1, max_value=5, value=1)
    st.write(task_info[task_num-1])
    

agent = init_agent(task_num)

# --- Trigger button ---
if run_agent:
    new_messages = []
    
    chat = None
    current_role = None
    buffer = ""
    
    # Stream results
    for message in agent(): 
    # for message in dummy(): 

        if message.role != current_role:
            if current_role != None:
                # Record each message for later
                new_messages.append({"role": current_role,
                                    "content": buffer}) 
            
            current_role = message.role 
            
            # empty otherwise we will create new chatboxes everytime
            chat = st.chat_message(current_role.value, avatar=role_to_emoji(current_role))
            chat = chat.empty()
            buffer = ""
            

        buffer += message.content
        
        with chat:
            
            with st.container(height=500):
                if current_role == Role.ASSISTANT:
                    st.code(buffer, language="verilog", height=500, wrap_lines=True)
                else:
                    st.text(buffer)
                
    # last role 
    new_messages.append({"role": current_role,
                         "content": buffer})  


    # Once streaming finishes, persist the conversation
    st.session_state.messages.extend(new_messages)
    


