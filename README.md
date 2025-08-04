# Mass Tracking System

A comprehensive web application for Catholic priests to track mass celebrations, manage bulk intentions, and maintain monthly obligations.

## Features

### 🎯 Core Functionality
- **Mass Celebration Tracking**: Record daily mass celebrations with detailed information
- **Bulk Intention Management**: Handle large quantities of mass intentions (30, 100, 300+ masses) with intelligent pause/resume functionality
- **Monthly Personal Masses**: Track 3 required personal masses per month with automatic progress monitoring
- **Fixed Date Intentions**: Manage special masses for specific dates (anniversaries, memorials, etc.)
- **Excel Import**: Import historical mass data from Excel files (supports data from 2000 onwards)

### 🔄 Advanced Bulk Intention Logic
- **Countdown System**: Bulk intentions count down from total (300 → 299 → 298...)
- **Smart Pause/Resume**: Automatically pauses bulk intentions for personal masses, fixed dates, and special occasions
- **Serial Number Preservation**: Resumes from exact position where paused
- **Progress Tracking**: Real-time monitoring of bulk intention completion
- **Low Count Alerts**: Notifications when bulk intentions are running low

### 📊 Dashboard & Analytics
- **Comprehensive Dashboard**: Overview of daily, weekly, and monthly mass statistics
- **Calendar View**: Visual representation of mass celebrations and upcoming obligations
- **Progress Tracking**: Monthly personal mass completion status
- **Alerts & Reminders**: Automated notifications for upcoming deadlines and obligations

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication system
- **Rate Limiting**: Protection against brute force attacks
- **Audit Logging**: Complete audit trail of all system activities
- **Role-based Access**: User-specific data access and permissions

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL with advanced stored procedures
- **Authentication**: JWT tokens with bcrypt password hashing
- **File Processing**: pandas for Excel import functionality
- **API**: RESTful API with comprehensive error handling

### Frontend
- **Framework**: React.js with TypeScript
- **UI Library**: Material-UI for modern, responsive design
- **State Management**: React Context API
- **HTTP Client**: Axios for API communication
- **Routing**: React Router for navigation

### Database
- **Primary Database**: PostgreSQL 13+
- **Caching**: Redis for session management
- **Advanced Features**: Stored procedures for complex business logic
- **Audit Trail**: Comprehensive logging of all data changes

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis (optional, for caching)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/willymsfs/Mass-Track.git
   cd Mass-Track/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

5. **Setup database**
   ```bash
   # Create PostgreSQL database
   createdb mass_tracking_db
   
   # Run database schema
   psql -d mass_tracking_db -f ../database/schema.sql
   psql -d mass_tracking_db -f ../database/seed_data.sql
   ```

6. **Run the backend**
   ```bash
   python src/main.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API endpoint
   ```

4. **Run the frontend**
   ```bash
   npm start
   ```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

### Mass Celebrations
- `GET /api/mass-celebrations` - List mass celebrations
- `POST /api/mass-celebrations` - Create new celebration
- `GET /api/mass-celebrations/{id}` - Get specific celebration
- `PUT /api/mass-celebrations/{id}` - Update celebration
- `DELETE /api/mass-celebrations/{id}` - Delete celebration

### Bulk Intentions
- `GET /api/bulk-intentions` - List bulk intentions
- `POST /api/bulk-intentions` - Create new bulk intention
- `POST /api/bulk-intentions/{id}/celebrate` - Celebrate one mass from bulk
- `POST /api/bulk-intentions/{id}/pause` - Pause bulk intention
- `POST /api/bulk-intentions/{id}/resume` - Resume bulk intention

### Dashboard
- `GET /api/dashboard` - Get dashboard data
- `GET /api/dashboard/summary` - Get quick summary
- `GET /api/dashboard/statistics` - Get detailed statistics
- `GET /api/dashboard/calendar` - Get calendar data

### Excel Import
- `POST /api/excel-import/upload` - Upload Excel file
- `POST /api/excel-import/process/{batch_id}` - Process uploaded file
- `GET /api/excel-import/batches` - List import batches
- `GET /api/excel-import/templates` - Get import templates

## Database Schema

### Key Tables
- **users**: Priest information and authentication
- **mass_intentions**: Individual mass intentions
- **mass_celebrations**: Actual mass celebrations
- **bulk_intentions**: Bulk mass intention management
- **monthly_obligations**: Monthly personal mass tracking
- **notifications**: System notifications and alerts

### Advanced Features
- **Stored Procedures**: Complex business logic for bulk intention management
- **Triggers**: Automatic updates for monthly obligations and notifications
- **Audit Logging**: Complete change tracking for all entities
- **Data Integrity**: Foreign key constraints and validation rules

## Excel Import Templates

### Standard Template
| Column | Field | Format |
|--------|-------|--------|
| A | Date | YYYY-MM-DD |
| B | Time | HH:MM |
| C | Location | Text |
| D | Notes | Text |
| E | Attendees | Number |

### Detailed Template
| Column | Field | Format |
|--------|-------|--------|
| A | Date | YYYY-MM-DD |
| B | Time | HH:MM |
| C | Location | Text |
| D | Intention Type | Text |
| E | Notes | Text |
| F | Attendees | Number |
| G | Special Circumstances | Text |

## Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment
1. Set up PostgreSQL database
2. Configure environment variables
3. Deploy backend to your server
4. Build and deploy frontend
5. Set up reverse proxy (nginx recommended)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation in the `/docs` folder

## Changelog

### Version 1.0.0 (January 2025)
- Initial release
- Complete mass tracking functionality
- Bulk intention management with pause/resume
- Excel import system
- Dashboard and analytics
- Authentication and security features

---

**Built with ❤️ for the Catholic Church community**

