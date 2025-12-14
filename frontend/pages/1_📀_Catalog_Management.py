"""
Module 1: Catalog Management
Demonstrates: DML Triggers, DDL Triggers, INSTEAD OF Triggers, Stored Procedures
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from db_connection import execute_query, execute_procedure_with_output, execute_non_query

st.set_page_config(page_title="Catalog Management", page_icon="📀", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
    h1, h2, h3 { color: #e94560 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📀 Catalog Management")
st.markdown("**Key Concepts:** DML Triggers, DDL Triggers, INSTEAD OF Triggers")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Add Artist", "💰 Update Price", "📋 DML Audit Log", "🔧 DDL Schema Log", "🚫 Blocked Actions"
])

with tab1:
    st.markdown("### Add New Artist")
    with st.form("add_artist"):
        name = st.text_input("Artist Name")
        if st.form_submit_button("Add Artist", type="primary") and name:
            try:
                # Get next ArtistId and insert directly (Chinook doesn't have IDENTITY)
                result = execute_query("SELECT ISNULL(MAX(ArtistId), 0) + 1 AS NextId FROM Artist")
                next_id = int(result.iloc[0]['NextId'])
                execute_non_query(f"INSERT INTO Artist (ArtistId, Name) VALUES ({next_id}, N'{name}')")
                st.success(f"✅ Artist added! ID: {next_id}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("#### Existing Artists")
    try:
        artists = execute_query("SELECT TOP 20 ArtistId, Name FROM Artist ORDER BY ArtistId DESC")
        st.dataframe(artists, use_container_width=True, height=250)
    except Exception as e:
        st.error(f"Error: {e}")

with tab2:
    st.markdown("### Update Track Price")
    st.info("This demonstrates the DML UPDATE trigger - old and new values are logged!")
    
    search = st.text_input("Search track name")
    if search:
        try:
            tracks = execute_query(f"""
                SELECT TOP 10 TrackId, Name, UnitPrice FROM Track 
                WHERE Name LIKE '%{search}%' ORDER BY Name
            """)
            if not tracks.empty:
                st.dataframe(tracks, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
    
    with st.form("update_price"):
        col1, col2 = st.columns(2)
        track_id = col1.number_input("Track ID", min_value=1, step=1)
        new_price = col2.number_input("New Price ($)", min_value=0.01, value=0.99, step=0.10)
        
        if st.form_submit_button("Update Price", type="primary"):
            try:
                execute_non_query(f"EXEC sp_UpdateTrackPrice @TrackId={track_id}, @NewPrice={new_price}")
                st.success(f"✅ Price updated! Check DML Audit Log tab.")
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.markdown("### 📋 DML Audit Log")
    st.markdown("**Trigger:** `trg_Track_Audit` logs INSERT/UPDATE/DELETE on Track table")
    
    if st.button("🔄 Refresh", key="refresh_dml"):
        st.rerun()
    
    try:
        logs = execute_query("""
            SELECT LogId, TableName, Operation, RecordId, OldValue, NewValue, 
                   ChangedBy, FORMAT(ChangedAt, 'yyyy-MM-dd HH:mm:ss') AS ChangedAt
            FROM AuditLog ORDER BY LogId DESC
        """)
        if not logs.empty:
            st.dataframe(logs, use_container_width=True, height=350)
        else:
            st.info("No audit logs yet. Add or update something!")
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Run complete_setup.sql first.")

with tab4:
    st.markdown("### 🔧 DDL Schema Change Log")
    st.markdown("**Trigger:** `trg_DDL_SchemaChanges` logs CREATE/ALTER/DROP on tables and procedures")
    
    if st.button("🔄 Refresh", key="refresh_ddl"):
        st.rerun()
    
    try:
        schema_logs = execute_query("""
            SELECT LogId, EventType, ObjectName, LoginName,
                   FORMAT(EventDate, 'yyyy-MM-dd HH:mm:ss') AS EventDate,
                   LEFT(SQLCommand, 100) AS SQLCommand
            FROM SchemaChangeLog ORDER BY LogId DESC
        """)
        if not schema_logs.empty:
            st.dataframe(schema_logs, use_container_width=True, height=350)
        else:
            st.info("No schema changes logged yet. Try creating a table in SSMS!")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    st.markdown("**How to test:** Run this in SSMS:")
    st.code("CREATE TABLE TestTable (Id INT);\nDROP TABLE TestTable;", language="sql")

with tab5:
    st.markdown("### 🚫 Blocked Action Log")
    st.markdown("**Trigger:** `trg_Artist_BlockDelete` (INSTEAD OF) blocks unauthorized deletes")
    
    if st.button("🔄 Refresh", key="refresh_blocked"):
        st.rerun()
    
    try:
        blocked_logs = execute_query("""
            SELECT LogId, TableName, AttemptedAction, RecordId, AttemptedBy,
                   FORMAT(AttemptedAt, 'yyyy-MM-dd HH:mm:ss') AS AttemptedAt, Reason
            FROM BlockedActionLog ORDER BY LogId DESC
        """)
        if not blocked_logs.empty:
            st.dataframe(blocked_logs, use_container_width=True, height=350)
        else:
            st.info("No blocked actions yet. Try deleting an artist via the view!")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    st.markdown("**How to test:** Run this in SSMS (it will be BLOCKED):")
    st.code("DELETE FROM vw_Artist WHERE ArtistId = 1;", language="sql")
    st.markdown("Then refresh this page to see the logged attempt.")
