import streamlit as st
from game_engine import Game
import json
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Shadow Circuit: A Night in Austin",
    page_icon="🌙",
    layout="wide"
)

st.write("✅ App script executed")



# Initialize session state
if 'game' not in st.session_state:
    st.session_state.game = Game()
    st.session_state.game_output = []
    st.session_state.command_history = []

# Title and introduction
st.title("🌙 Shadow Circuit: A Night in Austin")
st.markdown("*A neon-noir, urban-fantasy text adventure*")

# Game intro on first run
if not st.session_state.game_output:
    intro_text = """
**Welcome to Shadow Circuit**

You are MARLOWE CROSS, a newly-turned vampire detective, hunting the glue-obsessed necromancer EZRA VALE across Austin before dawn.

**Available Commands:**
- **Movement:** GO <direction>, N/S/E/W, INSIDE, OUT
- **Interaction:** LOOK, EXAMINE <item>, TAKE <item>, DROP <item>
- **Items:** USE <item> [ON <target>], COMBINE <item> WITH <item>
- **Social:** TALK <npc> [ABOUT <topic>], MESMERIZE <npc>
- **Vampire:** SENSE, BITE <target>
- **Special:** ENTER CODE ####, TRACE SIGIL, CRAFT COUNTER-INK
- **System:** INVENTORY, STATS, MAP, HINT, SAVE, LOAD

**Your Mission:** Stop Ezra Vale before dawn breaks over Austin!
    """
    st.session_state.game_output.append(intro_text)
    # Add initial room description
    initial_output = st.session_state.game.look_around()
    st.session_state.game_output.append(initial_output)

# Create layout with two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Game Output")
    
    # Display game output in a scrollable container
    output_container = st.container()
    with output_container:
        for output in st.session_state.game_output:
            if output.startswith("**") and output.endswith("**"):
                st.markdown(output)
            elif "═══════════════════════════════════════════════════════════════════════════════" in output:
                st.markdown(f"```\n{output}\n```")
            else:
                st.text(output)
    
    # Command input
    st.subheader("Enter Command")
    
    # Use form to handle command submission
    with st.form("command_form", clear_on_submit=True):
        command_input = st.text_input(
            "Command:", 
            placeholder="Type your command here (e.g., 'look', 'go east', 'examine radio')",
            key="command_input"
        )
        submit_button = st.form_submit_button("Execute Command")
        
        if submit_button and command_input:
            # Add command to history
            st.session_state.command_history.append(command_input)
            
            # Process command
            result = st.session_state.game.process_command(command_input)
            
            # Add command and response to output
            st.session_state.game_output.append(f"> {command_input}")
            
            if result == "QUIT":
                st.session_state.game_output.append("Thanks for playing Shadow Circuit!")
                st.stop()
            elif result == "GAME_OVER":
                st.session_state.game_output.append("**GAME OVER**")
            elif result:
                st.session_state.game_output.append(result)
            
            # Check for ending conditions only if game state indicates an ending
            # (Endings are now triggered by specific actions, not location)
            
            # Rerun to update display
            # st.rerun()

with col2:
    st.subheader("Game Status")
    
    # Current location
    current_room = st.session_state.game.current_room()
    if current_room:
        st.write(f"**Location:** {current_room['name']}")
    
    # Stats display
    stats = st.session_state.game.get_stats_display()
    st.write(f"**{stats}**")
    
    # Inventory
    st.subheader("Inventory")
    inventory = st.session_state.game.get_inventory_display()
    if st.session_state.game.s.inv:
        for item_key in st.session_state.game.s.inv:
            if item_key in st.session_state.game.items:
                item_name = st.session_state.game.items[item_key]['name']
                st.write(f"• {item_name}")
    else:
        st.write("*You carry nothing.*")
    
    # Quick commands
    st.subheader("Quick Commands")
    
    if st.button("Look Around"):
        result = st.session_state.game.process_command("look")
        st.session_state.game_output.append("> look")
        if result:
            st.session_state.game_output.append(result)
        # st.rerun()
    
    if st.button("Check Inventory"):
        result = st.session_state.game.process_command("inventory")
        st.session_state.game_output.append("> inventory")
        if result:
            st.session_state.game_output.append(result)
        # st.rerun()
    
    if st.button("Show Stats"):
        result = st.session_state.game.process_command("stats")
        st.session_state.game_output.append("> stats")
        if result:
            st.session_state.game_output.append(result)
        # st.rerun()
    
    if st.button("Get Hint"):
        result = st.session_state.game.process_command("hint")
        st.session_state.game_output.append("> hint")
        if result:
            st.session_state.game_output.append(result)
        # st.rerun()
    
    # Save/Load
    st.subheader("Save/Load Game")
    
    col_save, col_load = st.columns(2)
    
    with col_save:
        if st.button("Save Game"):
            result = st.session_state.game.process_command("save")
            st.session_state.game_output.append("> save")
            if result:
                st.session_state.game_output.append(result)
            # st.rerun()
    
    with col_load:
        if st.button("Load Game"):
            result = st.session_state.game.process_command("load")
            st.session_state.game_output.append("> load")
            if result:
                st.session_state.game_output.append(result)
            # st.rerun()
    
    # Command history
    if st.session_state.command_history:
        st.subheader("Recent Commands")
        recent_commands = st.session_state.command_history[-5:]  # Show last 5 commands
        for cmd in reversed(recent_commands):
            st.text(cmd)

# Game over check
if st.session_state.game.s.f["ending"]:
    st.subheader("🎭 Game Complete!")
    st.balloons()
    
    if st.button("Start New Game"):
        # Reset session state
        st.session_state.game = Game()
        st.session_state.game_output = []
        st.session_state.command_history = []
        # st.rerun()

# Footer
st.markdown("---")
st.markdown("*Shadow Circuit: A Night in Austin* - Navigate through Austin's supernatural underworld as vampire detective Marlowe Cross")
