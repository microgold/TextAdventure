import streamlit as st
from game_engine import Game
import json
import os

# Configure Streamlit page (must be FIRST)
st.set_page_config(
    page_title="Shadow Circuit: A Night in Austin",
    page_icon="🌙",
    layout="wide"
)

# --- Initialize session state ---
if "game" not in st.session_state:
    st.session_state.game = Game()
    st.session_state.game_output = []
    st.session_state.command_history = []
    st.session_state.command_input = ""

# --- Command handler ---
def handle_command():
    cmd = st.session_state.command_input
    if cmd:
        st.session_state.command_history.append(cmd)
        result = st.session_state.game.process_command(cmd)
        st.session_state.game_output.append(f"> {cmd}")

        if result == "QUIT":
            st.session_state.game_output.append("Thanks for playing Shadow Circuit!")
            st.session_state.command_input = ""
            st.stop()
        elif result == "GAME_OVER":
            st.session_state.game_output.append("**GAME OVER**")
        elif result:
            st.session_state.game_output.append(result)

        # Clear the input box
        st.session_state.command_input = ""

# --- Title and intro ---
st.title("🌙 Shadow Circuit: A Night in Austin")
st.markdown("*A neon-noir, urban-fantasy text adventure*")

if not st.session_state.game_output:
    intro_text = """
**Welcome to Shadow Circuit**

You are MARLOWE CROSS, a newly-turned vampire detective, hunting the glue-obsessed necromancer EZRA VALE across Austin before dawn.
    """
    st.session_state.game_output.append(intro_text)
    st.session_state.game_output.append(st.session_state.game.look_around())

# --- Layout ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Game Output")

    # Scrollable output
    output_container = st.container()
    with output_container:
        for output in st.session_state.game_output:
            st.text(output)

    # Command input
    st.subheader("Enter Command")
    st.text_input(
        "Command:",
        placeholder="Type your command here (e.g., 'look', 'go east')",
        key="command_input",
        on_change=handle_command
    )

with col2:
    st.subheader("Game Status")

    current_room = st.session_state.game.current_room()
    if current_room:
        st.write(f"**Location:** {current_room['name']}")

    stats = st.session_state.game.get_stats_display()
    st.write(f"**{stats}**")

    st.subheader("Inventory")
    if st.session_state.game.s.inv:
        for item_key in st.session_state.game.s.inv:
            item = st.session_state.game.items.get(item_key, {})
            st.write(f"• {item.get('name','Unknown')}")
    else:
        st.write("*You carry nothing.*")

    st.subheader("Recent Commands")
    for cmd in reversed(st.session_state.command_history[-5:]):
        st.text(cmd)

# Footer
st.markdown("---")
st.markdown("*Shadow Circuit: A Night in Austin* - Navigate through Austin's supernatural underworld as vampire detective Marlowe Cross")
