/*
=============================================================
DEMO SCRIPTS - DAM Semester Project
=============================================================
Run each demo section by section in SSMS
=============================================================
*/

USE Chinook;
GO

-- ============================================================
-- DEMO 1: DML TRIGGER - Audit Trail
-- ============================================================
-- WHAT IT SHOWS: Track table changes are auto-logged

-- Step 1: Check audit log before
SELECT * FROM AuditLog ORDER BY LogId DESC;

-- Step 2: Update a track price
UPDATE Track SET UnitPrice = 0.99 WHERE TrackId = 2;

-- Step 3: Check audit log after - new entry appears!
SELECT TOP 5 * FROM AuditLog ORDER BY LogId DESC;

GO

-- ============================================================
-- DEMO 2: DDL TRIGGER - Schema Change Logging  
-- ============================================================
-- WHAT IT SHOWS: CREATE/ALTER/DROP statements are logged

-- Step 1: Check schema log before
SELECT * FROM SchemaChangeLog ORDER BY LogId DESC;

-- Step 2: Create a test table
CREATE TABLE TestTable (Id INT);

-- Step 3: Check log - CREATE was recorded
SELECT TOP 3 * FROM SchemaChangeLog ORDER BY LogId DESC;

-- Step 4: Drop the test table
DROP TABLE TestTable;

-- Step 5: Check log - DROP was also recorded
SELECT TOP 3 * FROM SchemaChangeLog ORDER BY LogId DESC;

GO

-- ============================================================
-- DEMO 3: INSTEAD OF TRIGGER - Block Unauthorized Deletes
-- ============================================================
-- WHAT IT SHOWS: Delete attempts are blocked and logged

-- Step 1: Check blocked log before
SELECT * FROM BlockedActionLog;

-- Step 2: Try to delete (this will show an error - that's expected!)
DELETE FROM vw_Artist WHERE ArtistId = 1;

-- Step 3: Check blocked log - attempt was recorded
SELECT * FROM BlockedActionLog ORDER BY LogId DESC;

-- Step 4: Verify artist still exists (was not deleted)
SELECT * FROM Artist WHERE ArtistId = 1;

GO

-- ============================================================
-- DEMO 4: CONCURRENCY CONTROL
-- ============================================================
-- WHAT IT SHOWS: Two people can't claim the same ticket

-- Step 1: Reset ticket to Open status
UPDATE SupportTicket SET Status = 'Open', AssignedTo = NULL WHERE TicketId = 1;

-- Step 2: First employee claims the ticket
EXEC sp_ClaimTicket @TicketId = 1, @EmployeeId = 1;
-- Result shows: SUCCESS

-- Step 3: Second employee tries to claim SAME ticket
EXEC sp_ClaimTicket @TicketId = 1, @EmployeeId = 2;
-- Result shows: FAILED - Already claimed

-- Step 4: Check ticket - only first employee got it
SELECT * FROM SupportTicket WHERE TicketId = 1;

GO

-- ============================================================
-- DEMO 5: ISOLATION LEVELS (SERIALIZABLE Transaction)
-- ============================================================
-- WHAT IT SHOWS: Purchase is atomic - all steps succeed or all fail

-- Step 1: Check current invoice count
SELECT COUNT(*) AS InvoiceCountBefore FROM Invoice;

-- Step 2: Make a purchase (uses SERIALIZABLE isolation)
DECLARE @NewInvoiceId INT;
EXEC sp_CompletePurchase 
    @CustomerId = 1, 
    @TrackIds = '10,11,12', 
    @InvoiceId = @NewInvoiceId OUTPUT;
PRINT 'Created Invoice ID: ' + CAST(@NewInvoiceId AS VARCHAR);

-- Step 3: Check invoice was created
SELECT COUNT(*) AS InvoiceCountAfter FROM Invoice;

-- Step 4: View the invoice and its line items
SELECT TOP 1 * FROM Invoice ORDER BY InvoiceId DESC;
SELECT TOP 3 * FROM InvoiceLine ORDER BY InvoiceLineId DESC;

GO

-- ============================================================
-- DEMO 6: DEADLOCK HANDLING
-- ============================================================
-- WHAT IT SHOWS: Two transactions block each other, SQL Server 
-- kills one as "deadlock victim", our procedure retries automatically

-- IMPORTANT: This demo requires TWO SSMS query windows!
-- Follow these steps exactly:

-- =====================
-- PREPARATION (run once)
-- =====================
UPDATE SupportTicket SET Status = 'Open' WHERE TicketId IN (1, 2);
SELECT * FROM SupportTicket WHERE TicketId IN (1, 2);

GO

-- =====================
-- WINDOW 1: Copy this, paste in first SSMS window, but DON'T run yet
-- =====================
/*
USE Chinook;
BEGIN TRANSACTION;
PRINT 'Window 1: Locking Ticket 1...';
UPDATE SupportTicket SET Status = 'Locked by Window 1' WHERE TicketId = 1;
PRINT 'Window 1: Waiting 5 seconds...';
WAITFOR DELAY '00:00:05';
PRINT 'Window 1: Now trying to lock Ticket 2...';
UPDATE SupportTicket SET Status = 'Locked by Window 1' WHERE TicketId = 2;
COMMIT;
PRINT 'Window 1: Done!';
*/

-- =====================
-- WINDOW 2: Copy this, paste in second SSMS window
-- =====================
/*
USE Chinook;
BEGIN TRANSACTION;
PRINT 'Window 2: Locking Ticket 2...';
UPDATE SupportTicket SET Status = 'Locked by Window 2' WHERE TicketId = 2;
PRINT 'Window 2: Waiting 5 seconds...';
WAITFOR DELAY '00:00:05';
PRINT 'Window 2: Now trying to lock Ticket 1...';
UPDATE SupportTicket SET Status = 'Locked by Window 2' WHERE TicketId = 1;
COMMIT;
PRINT 'Window 2: Done!';
*/

-- =====================
-- HOW TO RUN:
-- =====================
-- 1. Run PREPARATION above first
-- 2. Open TWO separate query windows in SSMS
-- 3. Copy Window 1 code (without /* */) into first window
-- 4. Copy Window 2 code (without /* */) into second window
-- 5. Click Execute on Window 1
-- 6. IMMEDIATELY click Execute on Window 2 (within 1-2 seconds)
-- 7. Wait 5-10 seconds
-- 8. One window will show: "Transaction was deadlocked on lock resources"
--    The OTHER window will complete successfully

-- =====================
-- WHY sp_ResolveTicket HANDLES THIS:
-- =====================
-- Our stored procedure has this logic:
--   IF ERROR_NUMBER() = 1205  (deadlock error code)
--      Wait 1 second, then RETRY (up to 3 times)
-- So even if it becomes a deadlock victim, it tries again automatically!

/*
QUICK REFERENCE - Shorter version:

=== WINDOW 1 ===
BEGIN TRANSACTION;
UPDATE SupportTicket SET Status = 'X' WHERE TicketId = 1;
WAITFOR DELAY '00:00:05';
UPDATE SupportTicket SET Status = 'X' WHERE TicketId = 2;
COMMIT;

=== WINDOW 2 ===
BEGIN TRANSACTION;
UPDATE SupportTicket SET Status = 'Y' WHERE TicketId = 2;
WAITFOR DELAY '00:00:05';
UPDATE SupportTicket SET Status = 'Y' WHERE TicketId = 1;
COMMIT;

One window will show error: "Transaction was deadlocked on lock resources"
*/

GO

-- ============================================================
-- DEMO 7: INDEX PERFORMANCE
-- ============================================================
-- WHAT IT SHOWS: Index makes queries faster

-- Step 1: Turn on Execution Plan (press Ctrl+M or click toolbar button)

-- Step 2: Run this query
SELECT TrackId, Name, UnitPrice 
FROM Track 
WHERE GenreId = 1;

-- Step 3: Look at Execution Plan tab at bottom
-- You should see "Index Seek [IX_Track_GenreId]" 
-- This means the index is being used (fast!)

-- Without index, you would see "Table Scan" (slow)

GO

-- ============================================================
-- QUICK TEST: Run all stored procedures
-- ============================================================

-- Test sp_AddArtist
DECLARE @ArtistId INT;
EXEC sp_AddArtist @Name = 'Test Artist', @ArtistId = @ArtistId OUTPUT;
PRINT 'Added Artist ID: ' + CAST(@ArtistId AS VARCHAR);

-- Test sp_CreateTicket
DECLARE @TicketId INT;
EXEC sp_CreateTicket @CustomerId = 1, @Subject = 'Test Ticket', @TicketId = @TicketId OUTPUT;
PRINT 'Created Ticket ID: ' + CAST(@TicketId AS VARCHAR);

-- Test sp_GetOpenTickets
EXEC sp_GetOpenTickets;

GO

PRINT '=== ALL DEMOS COMPLETE ===';
