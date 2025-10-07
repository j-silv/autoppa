import streamlit as st
from autoppa.agent import Agent, Role, Message
import time


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


# def dummy():
#     yield Message(Role.SYSTEM, "1")
#     time.sleep(0.5)
#     yield Message(Role.USER, "2")
#     time.sleep(0.5)
#     yield Message(Role.ASSISTANT, "3")
#     time.sleep(0.5)
#     yield Message(Role.ASSISTANT, "4")
#     time.sleep(0.5)
#     yield Message(Role.ASSISTANT, "5")
#     time.sleep(0.5)
#     yield Message(Role.ASSISTANT, "6")
#     time.sleep(0.5)
#     yield Message(Role.TOOL, "7")
#     time.sleep(0.5)

st.title("AutoPPA")
st.text("PPAgent for RTL code optimization")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "task_num" not in st.session_state:
    st.session_state.task_num = 1

agent = init_agent(st.session_state.task_num)


# --- Display chat history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"].value,
                         avatar=role_to_emoji(message["role"])):
        
        if message["role"] == Role.ASSISTANT:
            st.code(message["content"])
        else:
            st.text(message["content"])


with st.sidebar:
    run_agent = st.button("Run Agent")

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
            if current_role == Role.ASSISTANT:
                st.code(buffer)
            else:
                st.text(buffer)
                
    # last role 
    new_messages.append({"role": current_role,
                         "content": buffer})  


    # Once streaming finishes, persist the conversation
    st.session_state.messages.extend(new_messages)
    


