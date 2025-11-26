# University Course Management System

A Django-based application for managing university course contracts, billings, and payments between Original Equipment Manufacturers (OEMs) and Universities.

## Overview

This system manages the complex relationships between Universities, OEMs (course providers), and their various contracts for educational courses. It handles everything from course offerings to billing and payment tracking.

## Core Features

### 1. Organization Management
- **Universities**: Track universities, their details, and points of contact
- **OEMs (Course Providers)**: Manage course providers and their offerings
- **Streams**: Handle different educational streams within universities

### 2. Course Management
- Track courses offered by OEMs
- Manage course details including duration, prerequisites, and descriptions
- Link courses to specific contracts

### 3. Contract Management
- Create and manage contracts between Universities and OEMs
- Set pricing details (cost per student, tax rates)
- Track contract status and validity periods
- Store contract-related documents
- Support multiple streams per contract

### 4. Batch Management
- Create student batches under contracts
- Track batch details (number of students, dates, status)
- Support cost overrides at batch level
  - Override cost per student
  - Override tax rates
- Track batch progress (planned, ongoing, completed)

### 5. Billing and Payment System
- Generate billings for batches
- Create and track invoices
- Support partial payments
- Track payment status (pending, completed, failed)
- Maintain billing snapshots for historical records
- Calculate and track:
  - Total amount
  - Amount paid
  - Balance due
  - Tax calculations

### 6. User Management
- Role-based access control
- Support for different user types:
  - University POCs
  - Provider POCs
  - Superusers
- User profile management

## Technical Features

1. **Version Control**
   - All models include versioning support
   - Track creation and modification timestamps

2. **Audit Logging**
   - Log model changes
   - Track critical operations

3. **Data Validation**
   - Validate contract-stream relationships
   - Ensure payment amount doesn't exceed invoice amount
   - Validate course-OEM relationships

4. **Transaction Management**
   - Atomic transactions for payment processing
   - Safe handling of concurrent operations

5. **API Support**
   - RESTful API endpoints
   - Serializers for all models
   - Proper validation and error handling

## Models Structure

1. **Base Models**
   - BaseModel (abstract base with versioning)
   - CustomUser (extended user model)

2. **Organization Models**
   - University
   - OEM
   - Stream

3. **Course Models**
   - Course
   - ContractCourse

4. **Contract Models**
   - Contract
   - ContractFile

5. **Batch Models**
   - Batch
   - BatchSnapshot

6. **Financial Models**
   - Billing
   - Invoice
   - Payment
   - TaxRate

### Ledger & Rebuild Command

- Financial activity is persisted in an append-only `ledger_lines` table that stores debit/credit pairs per account.
- Updates or deletions never mutate historical rows; instead, reversing entries are appended automatically.
- To regenerate ledger history (e.g., after fixing legacy data), run:

```bash
python manage.py rebuild_ledger           # Truncate and replay historical data
python manage.py rebuild_ledger --dry-run # Preview counts without changing data
python manage.py rebuild_ledger --truncate-only # Clear the ledger without replaying
```

## Installation

```bash
# Clone the repository
git clone [repository-url] 
```

## Potential Improvements

### 1. Enhanced Financial Features
- **Multi-Currency Support**
  - Handle international contracts with different currencies
  - Currency conversion tracking
  - Exchange rate history
- **Tax System Enhancement**
  - Support for multiple tax components
  - Tax exemption handling
  - Country-specific tax rules
- **Advanced Payment Features**
  - Payment scheduling and reminders
  - Automated payment reconciliation
  - Support for different payment gateways
  - Recurring payment plans

### 2. Reporting and Analytics
- **Financial Reports**
  - Revenue forecasting
  - Payment collection analytics
  - Aging reports for receivables
  - Tax reports
- **Operational Reports**
  - Batch performance metrics
  - Contract utilization reports
  - Student enrollment trends
- **Dashboard**
  - Real-time financial metrics
  - Contract status overview
  - Batch progress tracking
  - Payment status visualization

### 3. Integration Capabilities
- **API Enhancements**
  - GraphQL support for complex queries
  - Webhook support for events
  - API rate limiting and monitoring
- **Third-party Integrations**
  - Payment gateway integration (Stripe, PayPal)
  - Accounting software integration (QuickBooks, Xero)
  - Document management systems
  - Email/SMS notification services

### 4. Document Management
- **Enhanced File Handling**
  - Document versioning
  - Digital signature support
  - Document templates
  - Automated document generation
- **Storage Optimization**
  - Cloud storage integration
  - File compression
  - Archival system

### 5. User Experience
- **Interface Improvements**
  - Mobile-responsive admin interface
  - Custom dashboard for different user roles
  - Bulk operations support
  - Advanced search and filtering
- **Notification System**
  - Email notifications for important events
  - In-app notification center
  - Customizable notification preferences
  - Payment reminders

### 6. Security Enhancements
- **Advanced Authentication**
  - Two-factor authentication
  - SSO integration
  - IP-based access control
- **Audit System**
  - Detailed audit logs
  - User activity tracking
  - Change history visualization
- **Data Protection**
  - Enhanced encryption
  - Data backup system
  - GDPR compliance tools

### 7. Performance Optimization
- **Database Optimization**
  - Query optimization
  - Caching implementation
  - Database partitioning
- **Background Processing**
  - Async task processing
  - Scheduled jobs
  - Queue management

### 8. Business Logic Enhancements
- **Contract Management**
  - Contract templates
  - Auto-renewal handling
  - Contract comparison tools
  - Approval workflows
- **Batch Management**
  - Batch scheduling system
  - Resource allocation tracking
  - Capacity planning tools
- **Student Management**
  - Individual student tracking
  - Attendance management
  - Performance tracking

### 9. Testing and Quality
- **Test Coverage**
  - Unit test expansion
  - Integration tests
  - End-to-end testing
  - Performance testing
- **Code Quality**
  - Code documentation
  - Style guide enforcement
  - Static code analysis
- **Monitoring**
  - Error tracking
  - Performance monitoring
  - Usage analytics

### 10. Deployment and DevOps
- **Infrastructure**
  - Containerization (Docker)
  - CI/CD pipeline
  - Environment management
- **Scalability**
  - Load balancing
  - Microservices architecture
  - Auto-scaling configuration

These improvements would enhance the system's functionality, reliability, and user experience while making it more suitable for enterprise-level deployment.
