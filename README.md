# 🎵 Chinook Music Store - Database Administration Project

A comprehensive **Database Administration and Management (DAM)** semester project that demonstrates advanced SQL Server concepts through a digital music store application built with Python/Streamlit.

![SQL Server](https://img.shields.io/badge/SQL%20Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Database Concepts Covered](#database-concepts-covered)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Module Details](#module-details)
- [Demo Scripts](#demo-scripts)
- [Screenshots](#screenshots)
- [License](#license)

## Overview

This project extends the classic **Chinook Database** (a sample database representing a digital music store) with advanced database administration features. It showcases real-world database management concepts including triggers, stored procedures, transaction management, concurrency control, and deadlock handling.

The frontend is built with **Streamlit**, providing an interactive web interface to demonstrate and test all database features.

## Features

### 📀 Module 1: Catalog Management
- Add new artists to the catalog
- Update track prices
- View audit logs for all track modifications
- Schema change tracking
- Blocked action logging

### 💰 Module 2: Sales Processing
- Browse music catalog with search and filters
- Shopping cart functionality
- Complete purchase transactions
- Transaction history and invoice management

### 🎫 Module 3: Customer Support
- Create and manage support tickets
- Ticket claiming with concurrency control
- Ticket resolution with deadlock handling
- Support agent dashboard

## Database Concepts Covered

| Concept | Implementation |
|---------|---------------|
| **DML Triggers** | `trg_Track_Audit` - Logs all INSERT/UPDATE/DELETE operations on Track table |
| **DDL Triggers** | `trg_DDL_SchemaChanges` - Logs CREATE/ALTER/DROP operations on tables and procedures |
| **INSTEAD OF Triggers** | `trg_Artist_BlockDelete` - Blocks unauthorized deletions and logs attempts |
| **Stored Procedures** | Multiple procedures for CRUD operations and business logic |
| **Transactions (ACID)** | Purchase processing with full transaction support |
| **Isolation Levels** | SERIALIZABLE isolation for purchase transactions |
| **Concurrency Control** | UPDLOCK and ROWLOCK hints for ticket claiming |
| **Deadlock Handling** | Automatic retry mechanism (up to 3 retries) for deadlock victims |
| **Indexing** | Non-clustered index on Track.GenreId for performance |

## Project Structure

```
DAM Project/
├── 📁 database/
│   ├── complete_setup.sql      # Complete database setup script
│   └── demo_scripts.sql        # Step-by-step demonstration scripts
├── 📁 frontend/
│   ├── app.py                  # Main Streamlit application
│   ├── db_connection.py        # Database connection utilities
│   ├── requirements.txt        # Python dependencies
│   └── 📁 pages/
│       ├── 1_📀_Catalog_Management.py   # Module 1
│       ├── 2_💰_Sales_Processing.py      # Module 2
│       └── 3_🎫_Customer_Support.py      # Module 3
└── Chinook_SqlServer.sql       # Base Chinook database schema
```

## Prerequisites

Before you begin, ensure you have the following installed:

- **SQL Server** (Express edition works fine)
  - Tested on: SQL Server Express (SQLEXPRESS instance)
- **SQL Server Management Studio (SSMS)** - For running SQL scripts
- **Python 3.8+** - For the Streamlit frontend
- **ODBC Driver 17 for SQL Server** - For Python-SQL connectivity

## Installation & Setup

### Step 1: Set Up the Database

1. **Install the base Chinook database:**
   - Open SSMS and connect to your SQL Server instance
   - Open and execute `Chinook_SqlServer.sql` to create the base database

2. **Run the complete setup script:**
   - Open `database/complete_setup.sql` in SSMS
   - Execute the entire script
   - This creates:
     - Additional tables (AuditLog, SupportTicket, SchemaChangeLog, BlockedActionLog)
     - All triggers (DML, DDL, INSTEAD OF)
     - All stored procedures
     - Sample data

### Step 2: Configure Database Connection

Edit `frontend/db_connection.py` and update the connection settings:

```python
SERVER = r'YOUR-PC\SQLEXPRESS'  # Change to your SQL Server instance
DATABASE = 'Chinook'
DRIVER = '{ODBC Driver 17 for SQL Server}'
```

### Step 3: Install Python Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

**Required packages:**
- `streamlit>=1.28.0`
- `pyodbc>=4.0.39`
- `pandas>=2.0.0`
- `plotly>=5.18.0`

## Running the Application

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

3. Open your browser and go to `http://localhost:8501`

4. Use the sidebar to navigate between modules

## Module Details

### 📀 Module 1: Catalog Management

**Purpose:** Demonstrates trigger functionality and audit logging

| Feature | Database Concept |
|---------|-----------------|
| Add Artist | Stored procedure with OUTPUT parameter |
| Update Price | DML trigger captures old/new values |
| DML Audit Log | View trigger-generated audit records |
| DDL Schema Log | DDL trigger logs schema changes |
| Blocked Actions | INSTEAD OF trigger prevents unauthorized deletes |

**Key Triggers:**
- `trg_Track_Audit` - Logs all Track table modifications
- `trg_DDL_SchemaChanges` - Logs CREATE/ALTER/DROP statements
- `trg_Artist_BlockDelete` - Blocks deletes on vw_Artist view

### 💰 Module 2: Sales Processing

**Purpose:** Demonstrates transactions and isolation levels

| Feature | Database Concept |
|---------|-----------------|
| Browse Tracks | Parameterized queries with search |
| Add to Cart | Session-based cart management |
| Complete Purchase | SERIALIZABLE transaction isolation |
| View Invoice | Transaction integrity verification |

**Key Stored Procedure:**
- `sp_CompletePurchase` - Uses SERIALIZABLE isolation level to ensure atomic purchases

### 🎫 Module 3: Customer Support

**Purpose:** Demonstrates concurrency control and deadlock handling

| Feature | Database Concept |
|---------|-----------------|
| View Tickets | Stored procedure with JOINs |
| Create Ticket | Stored procedure with OUTPUT parameter |
| Claim Ticket | UPDLOCK + ROWLOCK for concurrency |
| Resolve Ticket | Automatic deadlock retry (3 attempts) |

**Key Stored Procedures:**
- `sp_ClaimTicket` - Uses lock hints to prevent double-claiming
- `sp_ResolveTicket` - Implements deadlock victim retry logic

## Demo Scripts

The `database/demo_scripts.sql` file contains step-by-step demonstrations:

1. **DML Trigger Demo** - Shows audit trail creation
2. **DDL Trigger Demo** - Shows schema change logging
3. **INSTEAD OF Trigger Demo** - Shows blocked action logging
4. **Concurrency Control Demo** - Shows ticket claiming prevention
5. **Isolation Levels Demo** - Shows SERIALIZABLE transaction
6. **Deadlock Handling Demo** - Shows automatic retry mechanism (requires 2 SSMS windows)
7. **Index Performance Demo** - Shows index usage in execution plans

### Running the Deadlock Demo

This requires two separate SSMS query windows:

1. Run preparation script first
2. Open two SSMS query windows
3. Execute Window 1 script, then immediately Window 2
4. Observe one transaction becomes a deadlock victim
5. The `sp_ResolveTicket` procedure demonstrates automatic retry

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **SQL Server** | Database engine |
| **T-SQL** | Stored procedures, triggers, transactions |
| **Python** | Backend application logic |
| **Streamlit** | Web frontend framework |
| **pyodbc** | Database connectivity |
| **Pandas** | Data manipulation |
| **Plotly** | Data visualization |

## Troubleshooting

### Connection Issues

1. **ODBC Driver not found:**
   - Download and install [ODBC Driver 17 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

2. **Cannot connect to SQL Server:**
   - Ensure SQL Server Browser service is running
   - Check if TCP/IP is enabled in SQL Server Configuration Manager
   - Verify your server instance name in `db_connection.py`

3. **Stored procedures not found:**
   - Run `database/complete_setup.sql` in SSMS first

### Frontend Issues

1. **Module import errors:**
   - Ensure you're running from the `frontend` directory
   - Check all packages are installed: `pip install -r requirements.txt`

## Author

Created as part of the Database Administration and Management (DAM) course semester project.

## License

This project is for educational purposes. The Chinook database is a sample database commonly used for SQL tutorials and demonstrations.

---

⭐ If you found this project helpful, please consider giving it a star!
