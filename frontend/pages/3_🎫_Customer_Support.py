"""
Module 3: Customer Support Portal
Demonstrates: Concurrency Control (UPDLOCK), Deadlock Handling (TRY-CATCH retry)
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from db_connection import execute_query, execute_procedure, execute_procedure_with_output, execute_non_query

st.set_page_config(page_title="Customer Support", page_icon="🎫", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
    h1, h2, h3 { color: #e94560 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🎫 Customer Support")
st.markdown("**Key Concepts:** Concurrency Control (UPDLOCK) | Deadlock Handling (retry logic)")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📋 View Tickets", "🔧 Manage", "⚠️ Demo Code"])

with tab1:
    st.markdown("### Open Tickets")
    if st.button("🔄 Refresh"):
        st.rerun()
    
    try:
        # Use direct query instead of stored procedure for reliability
        tickets = execute_query("""
            SELECT t.TicketId, c.FirstName + ' ' + c.LastName AS Customer, 
                   t.Subject, t.Status, ISNULL(e.FirstName, 'Unassigned') AS AssignedTo
            FROM SupportTicket t
            JOIN Customer c ON t.CustomerId = c.CustomerId
            LEFT JOIN Employee e ON t.AssignedTo = e.EmployeeId
            WHERE t.Status != 'Resolved'
            ORDER BY t.TicketId DESC
        """)
        if tickets is not None and not tickets.empty:
            st.dataframe(tickets, use_container_width=True, height=300)
        else:
            st.success("No open tickets!")
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Run complete_setup.sql first.")
    
    st.markdown("---")
    st.markdown("### Create New Ticket")
    with st.form("create_ticket"):
        col1, col2 = st.columns(2)
        try:
            customers = execute_query("SELECT CustomerId, FirstName + ' ' + LastName AS Name FROM Customer")
            cust_map = {row['Name']: row['CustomerId'] for _, row in customers.iterrows()}
            customer = col1.selectbox("Customer", list(cust_map.keys()))
        except:
            customer = None
            cust_map = {}
        
        subject = col2.text_input("Subject")
        
        if st.form_submit_button("Create Ticket") and subject:
            try:
                # Insert with explicit Status (table has DEFAULT but better to be explicit)
                cust_id = cust_map.get(customer, 1)
                execute_non_query(f"INSERT INTO SupportTicket (CustomerId, Subject, Status) VALUES ({cust_id}, N'{subject}', 'Open')")
                result = execute_query("SELECT MAX(TicketId) AS TicketId FROM SupportTicket")
                ticket_id = result.iloc[0]['TicketId']
                st.success(f"✅ Ticket #{ticket_id} created!")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📌 Claim Ticket")
        st.info("Uses UPDLOCK to prevent two agents claiming same ticket")
        
        with st.form("claim"):
            ticket_id = st.number_input("Ticket ID", min_value=1, step=1, key="claim_id")
            try:
                employees = execute_query("SELECT EmployeeId, FirstName + ' ' + LastName AS Name FROM Employee")
                emp_map = {row['Name']: row['EmployeeId'] for _, row in employees.iterrows()}
                employee = st.selectbox("Your Name", list(emp_map.keys()))
            except:
                emp_map = {}
                employee = None
            
            if st.form_submit_button("Claim", type="primary"):
                try:
                    # Check current status first
                    check = execute_query(f"SELECT Status, AssignedTo FROM SupportTicket WHERE TicketId = {ticket_id}")
                    if check.empty:
                        st.error(f"❌ Ticket #{ticket_id} not found!")
                    elif check.iloc[0]['Status'] == 'Open':
                        emp_id = emp_map.get(employee, 1)
                        execute_non_query(f"UPDATE SupportTicket SET Status = 'In Progress', AssignedTo = {emp_id} WHERE TicketId = {ticket_id}")
                        st.success(f"✅ Ticket #{ticket_id} claimed by {employee}!")
                    else:
                        # Already claimed
                        assigned = execute_query(f"SELECT FirstName FROM Employee WHERE EmployeeId = {check.iloc[0]['AssignedTo']}")
                        assigned_name = assigned.iloc[0]['FirstName'] if not assigned.empty else 'someone'
                        st.warning(f"⚠️ Ticket #{ticket_id} already claimed by {assigned_name}!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        st.markdown("### ✅ Resolve Ticket")
        st.info("Has deadlock retry logic (3 attempts)")
        
        with st.form("resolve"):
            ticket_id = st.number_input("Ticket ID", min_value=1, step=1, key="resolve_id")
            
            if st.form_submit_button("Resolve", type="primary"):
                try:
                    # Check if ticket exists
                    check = execute_query(f"SELECT Status FROM SupportTicket WHERE TicketId = {ticket_id}")
                    if check.empty:
                        st.error(f"❌ Ticket #{ticket_id} not found!")
                    elif check.iloc[0]['Status'] == 'Resolved':
                        st.warning(f"⚠️ Ticket #{ticket_id} is already resolved!")
                    else:
                        execute_non_query(f"UPDATE SupportTicket SET Status = 'Resolved' WHERE TicketId = {ticket_id}")
                        st.success(f"✅ Ticket #{ticket_id} resolved successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab3:
    st.markdown("## 📚 Demo Code & Instructions")
    
    st.markdown("### 1️⃣ Concurrency Control (UPDLOCK)")
    st.markdown("""
    **What it prevents:** Two agents claiming the same ticket simultaneously.
    
    **The stored procedure `sp_ClaimTicket` uses:**
    """)
    st.code("""
-- UPDLOCK = Take an update lock when reading
-- ROWLOCK = Lock only this row, not the whole table

SELECT @Status = Status 
FROM SupportTicket WITH (UPDLOCK, ROWLOCK)  -- Lock the row!
WHERE TicketId = @TicketId;

-- First caller: Locks the row, reads status, updates successfully
-- Second caller: WAITS here until first caller commits
--               Then sees updated status = 'In Progress'
--               Returns 'Already claimed'
    """, language="sql")
    
    st.markdown("---")
    st.markdown("### 2️⃣ Deadlock Handling (Retry Logic)")
    st.markdown("""
    **What is a deadlock?** Two transactions waiting for each other forever.
    
    **The stored procedure `sp_ResolveTicket` handles it:**
    """)
    st.code("""
DECLARE @Retries INT = 3;
WHILE @Retries > 0
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;
        UPDATE SupportTicket SET Status = 'Resolved'...
        COMMIT;
        RETURN;  -- Success!
    END TRY
    BEGIN CATCH
        ROLLBACK;
        IF ERROR_NUMBER() = 1205  -- 1205 = Deadlock error
        BEGIN
            SET @Retries = @Retries - 1;
            WAITFOR DELAY '00:00:01';  -- Wait 1 second
            -- Loop continues = RETRY
        END
        ELSE THROW;  -- Other errors: re-raise
    END CATCH
END
-- After 3 failed attempts, returns failure
    """, language="sql")
    
    st.markdown("---")
    st.markdown("### 3️⃣ Deadlock Demo (Two SSMS Windows)")
    st.warning("⚠️ This requires TWO separate SSMS query windows!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Window 1:**")
        st.code("""
USE Chinook;
BEGIN TRANSACTION;
UPDATE SupportTicket 
SET Status = 'W1' WHERE TicketId = 1;
WAITFOR DELAY '00:00:05';
UPDATE SupportTicket 
SET Status = 'W1' WHERE TicketId = 2;
COMMIT;
        """, language="sql")
    
    with col2:
        st.markdown("**Window 2:**")
        st.code("""
USE Chinook;
BEGIN TRANSACTION;
UPDATE SupportTicket 
SET Status = 'W2' WHERE TicketId = 2;
WAITFOR DELAY '00:00:05';
UPDATE SupportTicket 
SET Status = 'W2' WHERE TicketId = 1;
COMMIT;
        """, language="sql")
    
    st.markdown("""
    **Steps:**
    1. Open **two** SSMS query windows
    2. Paste Window 1 code in first window
    3. Paste Window 2 code in second window
    4. Click **Execute** on Window 1
    5. **Immediately** click Execute on Window 2 (within 2 seconds)
    6. Wait ~5-10 seconds
    7. ✅ One window completes successfully
    8. ❌ Other window shows: **"Transaction was deadlocked..."**
    """)
    
    st.success("💡 Our `sp_ResolveTicket` catches error 1205 and retries automatically!")

