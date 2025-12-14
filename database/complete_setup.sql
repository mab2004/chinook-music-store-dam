/*
=============================================================
DAM SEMESTER PROJECT - CHINOOK MUSIC STORE (SIMPLIFIED)
Complete SQL Script - 3 Modules
=============================================================
Server: AMD-PC\SQLEXPRESS
Database: Chinook

MODULES:
1. Catalog Management - Triggers, Stored Procedures
2. Sales Processing - Transactions, Isolation Levels
3. Support Portal - Concurrency, Deadlock Handling
=============================================================
*/

USE Chinook;
GO

-- ============================================================
-- PART 1: NEW TABLES
-- ============================================================

-- Audit Log (for trigger demo)
IF OBJECT_ID('dbo.AuditLog', 'U') IS NOT NULL DROP TABLE dbo.AuditLog;
GO

CREATE TABLE AuditLog (
    LogId INT IDENTITY(1,1) PRIMARY KEY,
    TableName VARCHAR(50),
    Operation VARCHAR(10),
    RecordId INT,
    OldValue NVARCHAR(500),
    NewValue NVARCHAR(500),
    ChangedBy VARCHAR(100) DEFAULT SYSTEM_USER,
    ChangedAt DATETIME DEFAULT GETDATE()
);
GO

-- Support Tickets (for concurrency demo)
IF OBJECT_ID('dbo.SupportTicket', 'U') IS NOT NULL DROP TABLE dbo.SupportTicket;
GO

CREATE TABLE SupportTicket (
    TicketId INT IDENTITY(1,1) PRIMARY KEY,
    CustomerId INT FOREIGN KEY REFERENCES Customer(CustomerId),
    Subject VARCHAR(200),
    Status VARCHAR(20) DEFAULT 'Open',
    AssignedTo INT NULL FOREIGN KEY REFERENCES Employee(EmployeeId),
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

-- Sample tickets
INSERT INTO SupportTicket (CustomerId, Subject, Status)
VALUES (1, 'Download issue', 'Open'),
       (2, 'Refund request', 'Open'),
       (3, 'Login problem', 'Open'),
       (5, 'Billing question', 'Open');
GO

PRINT 'Tables created.';

-- ============================================================
-- PART 2: DML TRIGGER (Requirement 1)
-- ============================================================

IF OBJECT_ID('trg_Track_Audit', 'TR') IS NOT NULL DROP TRIGGER trg_Track_Audit;
GO

CREATE TRIGGER trg_Track_Audit
ON Track
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- INSERT
    IF EXISTS (SELECT 1 FROM inserted) AND NOT EXISTS (SELECT 1 FROM deleted)
        INSERT INTO AuditLog (TableName, Operation, RecordId, NewValue)
        SELECT 'Track', 'INSERT', TrackId, CONCAT('Name:', Name, ' Price:$', UnitPrice)
        FROM inserted;
    
    -- UPDATE
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        INSERT INTO AuditLog (TableName, Operation, RecordId, OldValue, NewValue)
        SELECT 'Track', 'UPDATE', i.TrackId,
               CONCAT('Price:$', d.UnitPrice), CONCAT('Price:$', i.UnitPrice)
        FROM inserted i JOIN deleted d ON i.TrackId = d.TrackId;
    
    -- DELETE
    IF NOT EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        INSERT INTO AuditLog (TableName, Operation, RecordId, OldValue)
        SELECT 'Track', 'DELETE', TrackId, CONCAT('Name:', Name)
        FROM deleted;
END;
GO

PRINT 'DML Trigger created.';

-- ============================================================
-- PART 2B: DDL TRIGGER (Schema Change Logging)
-- ============================================================

-- Table to log schema changes
IF OBJECT_ID('dbo.SchemaChangeLog', 'U') IS NOT NULL DROP TABLE dbo.SchemaChangeLog;
GO

CREATE TABLE SchemaChangeLog (
    LogId INT IDENTITY(1,1) PRIMARY KEY,
    EventType VARCHAR(50),
    ObjectName VARCHAR(100),
    SQLCommand NVARCHAR(MAX),
    LoginName VARCHAR(100),
    EventDate DATETIME DEFAULT GETDATE()
);
GO

-- DDL Trigger: Logs CREATE, ALTER, DROP events on database
IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'trg_DDL_SchemaChanges')
    DROP TRIGGER trg_DDL_SchemaChanges ON DATABASE;
GO

CREATE TRIGGER trg_DDL_SchemaChanges
ON DATABASE
FOR CREATE_TABLE, ALTER_TABLE, DROP_TABLE, CREATE_PROCEDURE, ALTER_PROCEDURE, DROP_PROCEDURE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @EventData XML = EVENTDATA();
    
    INSERT INTO SchemaChangeLog (EventType, ObjectName, SQLCommand, LoginName)
    VALUES (
        @EventData.value('(/EVENT_INSTANCE/EventType)[1]', 'VARCHAR(50)'),
        @EventData.value('(/EVENT_INSTANCE/ObjectName)[1]', 'VARCHAR(100)'),
        @EventData.value('(/EVENT_INSTANCE/TSQLCommand)[1]', 'NVARCHAR(MAX)'),
        @EventData.value('(/EVENT_INSTANCE/LoginName)[1]', 'VARCHAR(100)')
    );
    
    PRINT 'Schema change logged by DDL trigger.';
END;
GO

PRINT 'DDL Trigger created.';

-- ============================================================
-- PART 2C: INSTEAD OF TRIGGER (Block Unauthorized Deletes)
-- ============================================================

-- Table to log blocked delete attempts
IF OBJECT_ID('dbo.BlockedActionLog', 'U') IS NOT NULL DROP TABLE dbo.BlockedActionLog;
GO

CREATE TABLE BlockedActionLog (
    LogId INT IDENTITY(1,1) PRIMARY KEY,
    TableName VARCHAR(50),
    AttemptedAction VARCHAR(20),
    RecordId INT,
    AttemptedBy VARCHAR(100) DEFAULT SYSTEM_USER,
    AttemptedAt DATETIME DEFAULT GETDATE(),
    Reason VARCHAR(200)
);
GO

-- Create a view on Artist to apply INSTEAD OF trigger
-- (INSTEAD OF triggers on base tables with FKs can be complex, so we use a view)
IF OBJECT_ID('dbo.vw_Artist', 'V') IS NOT NULL DROP VIEW dbo.vw_Artist;
GO

CREATE VIEW vw_Artist AS
SELECT ArtistId, Name FROM Artist;
GO

-- INSTEAD OF DELETE trigger: Blocks deletes and logs the attempt
IF OBJECT_ID('trg_Artist_BlockDelete', 'TR') IS NOT NULL DROP TRIGGER trg_Artist_BlockDelete;
GO

CREATE TRIGGER trg_Artist_BlockDelete
ON vw_Artist
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Log the blocked attempt
    INSERT INTO BlockedActionLog (TableName, AttemptedAction, RecordId, Reason)
    SELECT 'Artist', 'DELETE', ArtistId, 'Unauthorized: Artist deletion not allowed via standard access'
    FROM deleted;
    
    -- Do NOT perform the actual delete - just raise an error
    RAISERROR('DELETE blocked: You are not authorized to delete artists. This attempt has been logged.', 16, 1);
END;
GO

PRINT 'INSTEAD OF Trigger created.';

-- ============================================================
-- PART 3: STORED PROCEDURES (Requirement 4)
-- ============================================================

-- MODULE 1: Catalog Management
-- -----------------------------

-- Add Artist
IF OBJECT_ID('sp_AddArtist', 'P') IS NOT NULL DROP PROCEDURE sp_AddArtist;
GO
CREATE PROCEDURE sp_AddArtist @Name NVARCHAR(120), @ArtistId INT OUTPUT
AS
BEGIN
    -- Chinook Artist table doesn't have IDENTITY, so we manually get next ID
    SELECT @ArtistId = ISNULL(MAX(ArtistId), 0) + 1 FROM Artist;
    INSERT INTO Artist (ArtistId, Name) VALUES (@ArtistId, @Name);
END;
GO

-- Update Track Price
IF OBJECT_ID('sp_UpdateTrackPrice', 'P') IS NOT NULL DROP PROCEDURE sp_UpdateTrackPrice;
GO
CREATE PROCEDURE sp_UpdateTrackPrice @TrackId INT, @NewPrice DECIMAL(10,2)
AS
BEGIN
    UPDATE Track SET UnitPrice = @NewPrice WHERE TrackId = @TrackId;
END;
GO

-- MODULE 2: Sales Processing
-- ---------------------------

-- Complete Purchase (with Transaction & Isolation Level)
IF OBJECT_ID('sp_CompletePurchase', 'P') IS NOT NULL DROP PROCEDURE sp_CompletePurchase;
GO
CREATE PROCEDURE sp_CompletePurchase
    @CustomerId INT,
    @TrackIds VARCHAR(MAX),
    @InvoiceId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;  -- Highest isolation
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Get next Invoice ID manually (Chinook doesn't have IDENTITY)
        SELECT @InvoiceId = ISNULL(MAX(InvoiceId), 0) + 1 FROM Invoice;
        
        -- Get customer info
        DECLARE @Address NVARCHAR(70), @City NVARCHAR(40), @Country NVARCHAR(40);
        SELECT @Address = Address, @City = City, @Country = Country
        FROM Customer WHERE CustomerId = @CustomerId;
        
        -- Create invoice with manual ID
        INSERT INTO Invoice (InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity, BillingCountry, Total)
        VALUES (@InvoiceId, @CustomerId, GETDATE(), @Address, @City, @Country, 0);
        
        -- Get next InvoiceLine ID
        DECLARE @NextLineId INT;
        SELECT @NextLineId = ISNULL(MAX(InvoiceLineId), 0) FROM InvoiceLine;
        
        -- Add tracks with manual IDs
        INSERT INTO InvoiceLine (InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity)
        SELECT @NextLineId + ROW_NUMBER() OVER (ORDER BY t.TrackId), @InvoiceId, t.TrackId, t.UnitPrice, 1
        FROM Track t
        JOIN STRING_SPLIT(@TrackIds, ',') s ON t.TrackId = CAST(TRIM(s.value) AS INT);
        
        -- Update total
        UPDATE Invoice SET Total = (SELECT SUM(UnitPrice * Quantity) FROM InvoiceLine WHERE InvoiceId = @InvoiceId)
        WHERE InvoiceId = @InvoiceId;
        
        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH
END;
GO

-- MODULE 3: Support Portal
-- -------------------------

-- Create Ticket
IF OBJECT_ID('sp_CreateTicket', 'P') IS NOT NULL DROP PROCEDURE sp_CreateTicket;
GO
CREATE PROCEDURE sp_CreateTicket @CustomerId INT, @Subject VARCHAR(200), @TicketId INT OUTPUT
AS
BEGIN
    INSERT INTO SupportTicket (CustomerId, Subject) VALUES (@CustomerId, @Subject);
    SET @TicketId = SCOPE_IDENTITY();
END;
GO

-- Claim Ticket (with Concurrency Control)
IF OBJECT_ID('sp_ClaimTicket', 'P') IS NOT NULL DROP PROCEDURE sp_ClaimTicket;
GO
CREATE PROCEDURE sp_ClaimTicket @TicketId INT, @EmployeeId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        DECLARE @Status VARCHAR(20);
        SELECT @Status = Status FROM SupportTicket WITH (UPDLOCK, ROWLOCK) WHERE TicketId = @TicketId;
        
        IF @Status = 'Open'
        BEGIN
            UPDATE SupportTicket SET Status = 'In Progress', AssignedTo = @EmployeeId WHERE TicketId = @TicketId;
            COMMIT;
            SELECT 'SUCCESS' AS Result, 'Ticket claimed' AS Message;
        END
        ELSE
        BEGIN
            ROLLBACK;
            SELECT 'FAILED' AS Result, 'Already claimed' AS Message;
        END
    END TRY
    BEGIN CATCH
        ROLLBACK;
        SELECT 'ERROR' AS Result, ERROR_MESSAGE() AS Message;
    END CATCH
END;
GO

-- Resolve Ticket (with Deadlock Handling)
IF OBJECT_ID('sp_ResolveTicket', 'P') IS NOT NULL DROP PROCEDURE sp_ResolveTicket;
GO
CREATE PROCEDURE sp_ResolveTicket @TicketId INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Retries INT = 3;
    
    WHILE @Retries > 0
    BEGIN
        BEGIN TRY
            BEGIN TRANSACTION;
            UPDATE SupportTicket SET Status = 'Resolved' WHERE TicketId = @TicketId;
            COMMIT;
            SELECT 'SUCCESS' AS Result;
            RETURN;
        END TRY
        BEGIN CATCH
            ROLLBACK;
            IF ERROR_NUMBER() = 1205  -- Deadlock
            BEGIN
                SET @Retries = @Retries - 1;
                WAITFOR DELAY '00:00:01';
            END
            ELSE THROW;
        END CATCH
    END
    SELECT 'FAILED' AS Result, 'Max retries' AS Message;
END;
GO

-- Get Open Tickets
IF OBJECT_ID('sp_GetOpenTickets', 'P') IS NOT NULL DROP PROCEDURE sp_GetOpenTickets;
GO
CREATE PROCEDURE sp_GetOpenTickets
AS
BEGIN
    SELECT t.TicketId, c.FirstName + ' ' + c.LastName AS Customer, t.Subject, t.Status,
           ISNULL(e.FirstName, 'Unassigned') AS AssignedTo
    FROM SupportTicket t
    JOIN Customer c ON t.CustomerId = c.CustomerId
    LEFT JOIN Employee e ON t.AssignedTo = e.EmployeeId
    WHERE t.Status != 'Resolved';
END;
GO

PRINT 'Stored procedures created.';

-- ============================================================
-- PART 4: INDEX (Requirement 6 - Simple Example)
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Track_GenreId')
    CREATE NONCLUSTERED INDEX IX_Track_GenreId ON Track(GenreId);
GO

PRINT 'Index created.';

-- ============================================================
-- PART 5: TEST THE SETUP
-- ============================================================

PRINT '';
PRINT '=== TESTING ===';

-- Test trigger
UPDATE Track SET UnitPrice = 1.29 WHERE TrackId = 1;
SELECT TOP 3 * FROM AuditLog ORDER BY LogId DESC;

-- Test stored procedure
EXEC sp_GetOpenTickets;

PRINT '';
PRINT '=== SETUP COMPLETE ===';
PRINT 'Modules: Catalog Management, Sales Processing, Support Portal';
PRINT 'Requirements covered: Triggers, Stored Procedures, Concurrency, Isolation, Deadlocks, Indexing';
