import streamlit as st
from datetime import datetime
from mcp_engine import MCPWorkflow
import re

def strip_html_tags(text):
    # Remove all HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    return clean

st.set_page_config(page_title="🧠 MCP Chatbox", layout="centered")

# CSS for chatbox UI
st.markdown("""
<style>
  .chatbox {
    width: 420px;
    height: 600px;
    border: 1px solid #ccc;
    border-radius: 10px;
    padding: 12px;
    background: #fafafa;
    display: flex;
    flex-direction: column;
    font-family: Arial, sans-serif;
    margin: 2rem auto;
  }
  .chat-history {
    flex-grow: 1;
    overflow-y: auto;
    padding-right: 8px;
  }
  .message {
    margin-bottom: 15px;
    max-width: 85%;
    word-wrap: break-word;
  }
  .user {
    background: #d4f1c5;
    align-self: flex-end;
    border-radius: 10px 10px 0 10px;
    padding: 8px 12px;
    color: #000;
    font-size: 14px;
  }
  .bot {
    background: #fff;
    border: 1px solid #ccc;
    align-self: flex-start;
    border-radius: 10px 10px 10px 0;
    padding: 8px 12px;
    color: #222;
    font-size: 14px;
  }
  .timestamp {
    font-size: 10px;
    color: #666;
    margin-bottom: 3px;
    user-select: none;
  }
  .input-area {
    border-top: 1px solid #ccc;
    padding-top: 10px;
  }
  input[type="text"] {
    width: 100%;
    padding: 10px 12px;
    border-radius: 20px;
    border: 1px solid #bbb;
    font-size: 15px;
    outline: none;
    box-sizing: border-box;
  }
  button[type="submit"] {
    display: none;
  }
</style>

<script>
  window.addEventListener('load', () => {
    const chatEnd = document.getElementById('chat-end');
    if (chatEnd) {
      chatEnd.scrollIntoView({ behavior: 'smooth' });
    }
  });
</script>
""", unsafe_allow_html=True)

# Initialize session state
if "selected_option" not in st.session_state:
    st.session_state.selected_option = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Landing page - select option
if st.session_state.selected_option is None:
    st.title("🤖 MCP Assistant")
    st.markdown("Please select an option to get started:")

    options = {
        "1": "Knowledge base of screen",
        "2": "Defect Raise",
        "3": "Similar Defect Identification",
        "4": "Reporting & Dashboard"
    }

    for k, v in options.items():
        st.markdown(f"**{k}. {v}**")

    choice = st.text_input("Option Input", label_visibility="hidden", placeholder="Type the number of your choice (e.g., 2):")
    if choice in options:
        st.session_state.selected_option = choice
        st.experimental_rerun()
    else:
        st.stop()

# Only Option 2 implemented
if st.session_state.selected_option == "2":
    # Initialize MCPWorkflow instance
    if "mcp" not in st.session_state or not hasattr(st.session_state.mcp, "get_current_manifest"):
        st.session_state.mcp = MCPWorkflow()
        try:
            st.session_state.mcp.start("create_defect")
        except Exception as e:
            st.error(f"⚠️ MCP Engine failed to start: {e}")
        st.session_state.chat_history = []

    mcp = st.session_state.mcp
    manifest = mcp.get_current_manifest()
    input_required = manifest.get("input_required", [])
    allowed = manifest.get("allowed_next_steps", [])
    chat = st.session_state.chat_history

    # Render chatbox container
    st.markdown('<div class="chatbox">', unsafe_allow_html=True)
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)

    # Display chat history
    for entry in chat:
        ts = entry.get("timestamp", "")
        user_text = entry.get("user", "")
        assistant_text = strip_html_tags(entry.get("assistant", ""))
        st.markdown(f'<div class="timestamp">{ts}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="message user">{user_text}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="timestamp">{ts}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="message bot">{assistant_text}</div>', unsafe_allow_html=True)

    st.markdown('<div id="chat-end"></div></div>', unsafe_allow_html=True)  # close chat-history

    # Input area form
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_input("Type your message here...", key="chat_input", label_visibility="hidden")
        submitted = st.form_submit_button("Send")
    st.markdown('</div>', unsafe_allow_html=True)  # close input-area

    st.markdown('</div>', unsafe_allow_html=True)  # close chatbox

    # Process submitted input
    if submitted and user_text.strip():
        now_str = datetime.now().strftime("%H:%M")
        manifest = mcp.get_current_manifest()
        input_required = manifest.get("input_required", [])
        allowed = manifest.get("allowed_next_steps", [])

        missing_field = next((f for f in input_required if not mcp.context.get(f)), None)

        if missing_field:
            mcp.update_context({missing_field: user_text})
            manifest = mcp.get_current_manifest()
            input_required = manifest.get("input_required", [])
            allowed = manifest.get("allowed_next_steps", [])
            remaining = [f for f in input_required if not mcp.context.get(f)]

            if remaining:
                chat.append({
                    "user": user_text,
                    "assistant": f"❓ Please provide `{remaining[0]}`",
                    "timestamp": now_str
                })
            else:
                if len(allowed) == 1:
                    selected_step = allowed[0]
                    mcp.proceed_to_next(selected_step)
                    manifest = mcp.get_current_manifest()
                    input_required = manifest.get("input_required", [])
                    allowed = manifest.get("allowed_next_steps", [])
                    ctx = "\n".join(
                        [f"**{k.replace('_',' ').capitalize()}**: {v}" for k, v in mcp.context.items() if not k.startswith("note_")]
                    )
                    next_q = f"❓ Please provide `{input_required[0]}`" if input_required else "✅ No input required."
                    chat.append({
                        "user": user_text,
                        "assistant": f"➡️ Moved to `{selected_step}`\n\n📌 Context:\n{ctx}\n\n{next_q}",
                        "timestamp": now_str
                    })
                else:
                    step_options = "\n".join([f"{i+1}. {s}" for i, s in enumerate(allowed)])
                    ctx = "\n".join(
                        [f"**{k.replace('_',' ').capitalize()}**: {v}" for k, v in mcp.context.items() if not k.startswith("note_")]
                    )
                    chat.append({
                        "user": user_text,
                        "assistant": f"➡️ All inputs done.\n\n📌 Context:\n{ctx}\n\nPlease select next step:\n{step_options}",
                        "timestamp": now_str
                    })

        elif allowed and user_text.strip().isdigit():
            idx = int(user_text.strip()) - 1
            if 0 <= idx < len(allowed):
                selected_step = allowed[idx]
                mcp.proceed_to_next(selected_step)
                manifest = mcp.get_current_manifest()
                input_required = manifest.get("input_required", [])
                allowed = manifest.get("allowed_next_steps", [])
                ctx = "\n".join(
                    [f"**{k.replace('_',' ').capitalize()}**: {v}" for k, v in mcp.context.items() if not k.startswith("note_")]
                )
                question = f"❓ Please provide `{input_required[0]}`" if input_required else "✅ No input needed."
                chat.append({
                    "user": user_text,
                    "assistant": f"➡️ Moved to `{selected_step}`\n\n📌 Context:\n{ctx}\n\n{question}",
                    "timestamp": now_str
                })

        else:
            mcp.update_context({f"note_{len(chat)}": user_text})
            chat.append({
                "user": user_text,
                "assistant": f"✅ Noted: {user_text}",
                "timestamp": now_str
            })

        st.experimental_rerun()

else:
    st.title("📌 This option is currently not enabled.")
    st.markdown("Please restart and pick Option 2 to continue.")

