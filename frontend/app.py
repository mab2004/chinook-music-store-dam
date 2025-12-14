"""
Chinook Music Store - Simplified Dashboard (3 Modules)
DAM Semester Project
"""

import streamlit as st

st.set_page_config(
    page_title="Chinook Music Store",
    page_icon="🎵",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
    h1, h2, h3 { color: #e94560 !important; }
    .module-card {
        background: rgba(233, 69, 96, 0.1);
        border: 1px solid #e94560;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🎵 Chinook Music Store")
st.markdown("### Database Administration & Management - Semester Project")
st.markdown("---")

st.markdown("""
<div class="module-card">
    <h3>📋 Project Overview</h3>
    <p>This application demonstrates key database concepts through 3 modules:</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="module-card">
        <h3>📀 Catalog Management</h3>
        <p><strong>Concepts:</strong></p>
        <ul>
            <li>DML Triggers</li>
            <li>Audit Logging</li>
            <li>Stored Procedures</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="module-card">
        <h3>💰 Sales Processing</h3>
        <p><strong>Concepts:</strong></p>
        <ul>
            <li>Transactions (ACID)</li>
            <li>Isolation Levels</li>
            <li>Stored Procedures</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="module-card">
        <h3>🎫 Customer Support</h3>
        <p><strong>Concepts:</strong></p>
        <ul>
            <li>Concurrency Control</li>
            <li>Deadlock Handling</li>
            <li>Stored Procedures</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Test Connection
st.markdown("### 🔌 Database Connection")
if st.button("Test Connection"):
    try:
        from db_connection import test_connection
        success, msg = test_connection()
        if success:
            st.success("✅ Connected to Chinook database!")
        else:
            st.error(f"❌ Failed: {msg}")
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")
st.markdown("👈 **Use the sidebar to navigate to different modules**")
