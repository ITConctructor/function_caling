import streamlit as st
import json
import yaml
import requests
from src.service.core import Environment
import base64


def model_response(user_input, backend):
    string_dialogue =  "You are a helpful bartender-assistant at fantasy tavern." \
                       "You do not respond as 'User' or pretend to be 'User'."\
                       "You only respond once as 'Bartender-assistant'."
    
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    
    output = backend.interract(user_input)
    return output

def image_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string_bc = base64.b64encode(image_file.read())
        
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string_bc.decode()});
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

    st.markdown("""
    <style>
    .stTextInput > label {
    font-size:120%;
    font-weight:bold;
    color:white;
    background: #faedcd;
    border: 2px;
    border-radius: 3px;
    }

    [data-baseweb="base-input"]{
    background: #C28E57;
    border: 2px;
    border-radius: 3px;
    }

    input[class]{
    font-weight: bold;
    font-size:120%;
    color: black;
    }
    </style>
    """, unsafe_allow_html=True)

def show_main_page():

    image_local('faedcd.png')
    # initialize_ui()

    url = "" # localhost: ...
    backend = Environment(url)

    st.title("Добро пожаловать в таверну!")
    st.image("d81ae2_99c9dfa697944a0b9201348b7b60c875~mv2.jpg")


    with st.sidebar:
        if st.button('Очистить историю чата'): clear_chat_history()

        # st.write("У тебя есть: ", backend.get_state())

    
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "Чем сегодня могу Вам помочь, авантюрист?"}]

    for message in st.session_state.messages:
        if message['role'] == "assistant":
            with st.chat_message(message["role"], avatar = "bartender-drink-occupation-avatar-512.jpg"):
                st.write(message["content"])
        else:
            with st.chat_message(message["role"], avatar = "man-avatar-boy-adventure-fashion-1024.jpg"):
                st.write(message["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar = "man-avatar-boy-adventure-fashion-1024.jpg"):
            st.write(prompt)

# Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar = "bartender-drink-occupation-avatar-512.jpg"):
            with st.spinner("Хмммм..."):

                response = model_response(prompt, backend)
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Чем сегодня могу Вам помочь, авантюрист?"}]

if __name__ == "__main__":
    show_main_page()
