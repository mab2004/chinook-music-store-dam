"""
Module 2: Sales Processing
Demonstrates: Transactions (ACID), Isolation Levels, Stored Procedures
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from db_connection import execute_query, execute_procedure_with_output

st.set_page_config(page_title="Sales Processing", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
    h1, h2, h3 { color: #e94560 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 💰 Sales Processing")
st.markdown("**Key Concept:** SERIALIZABLE transactions ensure ACID properties")
st.markdown("---")

# Initialize cart
if 'cart' not in st.session_state:
    st.session_state.cart = []

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Browse Tracks")
    search = st.text_input("🔍 Search", placeholder="Track name, artist...")
    
    try:
        query = """
            SELECT TOP 30 t.TrackId, t.Name AS Track, ar.Name AS Artist, t.UnitPrice AS Price
            FROM Track t
            JOIN Album a ON t.AlbumId = a.AlbumId
            JOIN Artist ar ON a.ArtistId = ar.ArtistId
        """
        if search:
            query += f" WHERE t.Name LIKE '%{search}%' OR ar.Name LIKE '%{search}%'"
        query += " ORDER BY t.Name"
        
        tracks = execute_query(query)
        if not tracks.empty:
            st.dataframe(tracks, use_container_width=True, height=300)
            
            track_id = st.number_input("Track ID to add", min_value=1, step=1)
            if st.button("Add to Cart"):
                track = tracks[tracks['TrackId'] == track_id]
                if not track.empty:
                    item = {'id': track_id, 'name': track.iloc[0]['Track'], 'price': float(track.iloc[0]['Price'])}
                    if item not in st.session_state.cart:
                        st.session_state.cart.append(item)
                        st.success(f"Added: {item['name']}")
                    else:
                        st.warning("Already in cart")
    except Exception as e:
        st.error(f"Error: {e}")

with col2:
    st.markdown("### 🛒 Cart")
    
    if st.session_state.cart:
        total = 0
        for item in st.session_state.cart:
            st.write(f"• {item['name']} - ${item['price']:.2f}")
            total += item['price']
        
        st.markdown(f"**Total: ${total:.2f}**")
        
        if st.button("🗑️ Clear"):
            st.session_state.cart = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Checkout")
        
        try:
            customers = execute_query("SELECT CustomerId, FirstName + ' ' + LastName AS Name FROM Customer ORDER BY LastName")
            customer_map = {row['Name']: row['CustomerId'] for _, row in customers.iterrows()}
            selected = st.selectbox("Customer", list(customer_map.keys()))
            
            if st.button("💳 Complete Purchase", type="primary"):
                track_ids = ','.join(str(i['id']) for i in st.session_state.cart)
                try:
                    invoice_id = execute_procedure_with_output(
                        "sp_CompletePurchase",
                        {"CustomerId": customer_map[selected], "TrackIds": track_ids},
                        "InvoiceId"
                    )
                    st.success(f"✅ Purchase complete! Invoice #{invoice_id}")
                    st.balloons()
                    st.info("💡 Used SERIALIZABLE isolation - highest level!")
                    st.session_state.cart = []
                except Exception as e:
                    st.error(f"❌ Transaction rolled back: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Cart is empty")

st.markdown("---")
st.markdown("### Recent Invoices")
try:
    invoices = execute_query("""
        SELECT TOP 10 i.InvoiceId, c.FirstName + ' ' + c.LastName AS Customer,
               FORMAT(InvoiceDate, 'yyyy-MM-dd') AS Date, Total
        FROM Invoice i JOIN Customer c ON i.CustomerId = c.CustomerId
        ORDER BY InvoiceId DESC
    """)
    st.dataframe(invoices, use_container_width=True)
except Exception as e:
    st.error(f"Error: {e}")
