# Mass Tracking System - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Recording Mass Celebrations](#recording-mass-celebrations)
4. [Managing Bulk Intentions](#managing-bulk-intentions)
5. [Monthly Personal Masses](#monthly-personal-masses)
6. [Excel Import Feature](#excel-import-feature)
7. [Calendar View](#calendar-view)
8. [Notifications](#notifications)
9. [Reports and Statistics](#reports-and-statistics)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### Logging In
1. Open your web browser and navigate to the Mass Tracking System
2. Enter your username and password provided by your administrator
3. Click "Sign In" to access your dashboard

**Demo Credentials for Testing:**
- Username: `demo_priest`
- Password: `demo123`

### First Time Setup
After logging in for the first time:
1. Review your profile information
2. Set up your notification preferences
3. Familiarize yourself with the dashboard layout

## Dashboard Overview

The dashboard is your central hub for managing mass celebrations and tracking your obligations.

### Key Sections

#### Statistics Cards
- **This Month**: Shows masses celebrated this month
- **Personal Masses**: Tracks your 3 monthly personal mass obligations
- **Bulk Intentions**: Displays active bulk intention counts
- **Pending**: Shows any pending or overdue obligations

#### Quick Actions
- **Record Mass**: Quickly log a mass celebration
- **View Calendar**: See your mass schedule
- **Import Data**: Upload historical records
- **View Reports**: Access detailed statistics

#### Recent Activity
- Shows your latest mass celebrations
- Displays recent bulk intention updates
- Lists upcoming fixed-date obligations

#### Charts and Graphs
- Monthly mass celebration trends
- Bulk intention progress tracking
- Personal mass completion status

## Recording Mass Celebrations

### Basic Mass Recording

1. **Navigate to Record Mass**
   - Click "Record Mass" from the dashboard
   - Or use the "+" button in the navigation

2. **Fill in Mass Details**
   - **Date**: Select the celebration date
   - **Time**: Enter the mass time (optional)
   - **Location**: Specify where the mass was celebrated
   - **Type**: Choose the type of mass intention

3. **Select Intention Type**
   - **Personal Mass**: One of your 3 monthly personal masses
   - **Bulk Intention**: From active bulk intention series
   - **Fixed Date**: Province/Generalate assigned masses
   - **Special Occasion**: Birthdays, anniversaries, memorials

4. **Add Intention Details**
   - **For Whom**: Name of the person/intention
   - **Intention Source**: Where the intention came from
   - **Notes**: Additional details (optional)

5. **Save the Record**
   - Review all information
   - Click "Save Mass Celebration"
   - Confirmation will appear

### Mass Types Explained

#### Personal Masses
- Every priest must celebrate 3 personal masses per month
- Dates are flexible within the month
- System automatically tracks completion
- Can be for any personal intention

#### Bulk Intentions
- Large quantities of masses (e.g., 30, 100, 300)
- Each celebration reduces the count by 1
- System tracks progress automatically
- Can be paused for other obligations

#### Fixed Date Masses
- Assigned by Province or Generalate
- Must be celebrated on specific dates
- Usually for deceased members or special occasions
- System sends reminders

#### Special Occasions
- Birthdays, death anniversaries, ordination anniversaries
- Can interrupt bulk intention sequences
- System automatically resumes bulk count after completion

## Managing Bulk Intentions

### Understanding Bulk Intentions

Bulk intentions are large quantities of masses received for specific intentions. The system uses a countdown approach:
- Start with total count (e.g., 300)
- Each mass reduces count by 1 (300 → 299 → 298...)
- System tracks progress and completion

### Creating a New Bulk Intention

1. **Access Bulk Intentions**
   - Go to "Bulk Intentions" in the menu
   - Click "Add New Bulk Intention"

2. **Enter Details**
   - **Total Count**: Number of masses (e.g., 300)
   - **Intention For**: What/whom the masses are for
   - **Source**: Province, Generalate, or other
   - **Start Date**: When to begin celebrating
   - **Priority**: Normal, High, or Low

3. **Save and Activate**
   - Review information
   - Click "Create Bulk Intention"
   - System will activate automatically

### Pause and Resume Functionality

The system automatically handles interruptions:

#### Automatic Pausing
Bulk intentions pause when you celebrate:
- Personal masses (3 monthly)
- Fixed-date masses
- Special occasion masses
- Memorial masses

#### Automatic Resuming
After completing interrupting masses:
- System resumes from exact count where paused
- No manual intervention needed
- Progress tracking continues seamlessly

#### Manual Pause/Resume
You can also manually pause bulk intentions:
1. Go to "Bulk Intentions"
2. Find the active intention
3. Click "Pause" and provide reason
4. Click "Resume" when ready to continue

### Bulk Intention Status Levels

- **Active**: Currently being celebrated
- **Paused**: Temporarily stopped for other obligations
- **Completed**: All masses celebrated
- **Low Count**: Fewer than 10 masses remaining (warning)

## Monthly Personal Masses

### Understanding Personal Mass Obligations

Every priest must celebrate 3 personal masses each month:
- Dates are flexible within the month
- Can be for any personal intention
- Must be completed by month end
- System tracks and reminds automatically

### Recording Personal Masses

1. **Select Personal Mass Type**
   - When recording a mass, choose "Personal Mass"
   - System automatically counts toward monthly obligation

2. **Choose Your Intention**
   - Can be for family, friends, personal needs
   - Or any intention close to your heart
   - Add details in the "For Whom" field

3. **Track Progress**
   - Dashboard shows current month progress
   - Calendar highlights personal mass dates
   - Notifications remind of pending obligations

### Monthly Reset

- Personal mass count resets on the 1st of each month
- Previous month's completion is recorded in history
- System generates monthly reports automatically

## Excel Import Feature

### Importing Historical Data

The Excel import feature allows you to upload historical mass records from 2000 onwards.

#### Preparing Your Excel File

1. **Use Provided Template**
   - Download template from "Import Data" section
   - Three templates available: Standard, Detailed, Simple

2. **Required Columns**
   - **Date**: Mass celebration date (YYYY-MM-DD format)
   - **Type**: Mass type (Personal, Bulk, Fixed, Special)
   - **For Whom**: Intention recipient
   - **Source**: Where intention came from
   - **Notes**: Additional details (optional)

3. **Data Validation**
   - Dates must be between 2000 and current year
   - All required fields must be filled
   - Duplicate entries will be flagged

#### Import Process

1. **Access Import Feature**
   - Go to "Import Data" from dashboard
   - Or navigate to "Data Management" → "Import"

2. **Upload File**
   - Click "Choose File" and select your Excel file
   - Select appropriate template type
   - Click "Upload and Validate"

3. **Review Validation Results**
   - System checks for errors and duplicates
   - Review any warnings or issues
   - Fix problems in Excel file if needed

4. **Confirm Import**
   - Review summary of records to import
   - Click "Confirm Import" to proceed
   - System processes and saves all valid records

5. **View Results**
   - Import summary shows success/failure counts
   - Error log available for troubleshooting
   - Imported data appears in your records immediately

### Import Templates

#### Standard Template
- Date, Type, For Whom, Source, Notes
- Most commonly used format
- Suitable for detailed record keeping

#### Detailed Template
- Includes additional fields like time, location
- Best for comprehensive historical records
- More detailed tracking capabilities

#### Simple Template
- Minimal required fields only
- Quick import for basic records
- Date, Type, For Whom only

## Calendar View

### Accessing Calendar

1. Click "Calendar" in the main navigation
2. Choose view: Month, Week, or Day
3. Navigate between dates using arrow buttons

### Calendar Features

#### Color Coding
- **Blue**: Personal masses
- **Green**: Bulk intention masses
- **Red**: Fixed-date masses
- **Purple**: Special occasion masses
- **Gray**: No masses scheduled

#### Interactive Features
- Click any date to see mass details
- Click "+" to add new mass for that date
- Drag and drop to reschedule (where applicable)
- Filter by mass type using checkboxes

#### Calendar Views

**Month View**
- Shows entire month at a glance
- Color-coded dots indicate mass types
- Quick overview of monthly obligations

**Week View**
- Detailed weekly schedule
- Shows mass times and details
- Better for daily planning

**Day View**
- Detailed daily schedule
- Shows all masses for selected date
- Includes times and full details

## Notifications

### Notification Types

#### Automatic Notifications
- **Monthly Reminders**: Personal mass obligations
- **Bulk Intention Alerts**: When count gets low (< 10)
- **Fixed Date Reminders**: Upcoming required masses
- **Completion Notices**: When bulk intentions are finished

#### Notification Settings

1. **Access Settings**
   - Click your profile icon
   - Select "Notification Settings"

2. **Configure Preferences**
   - Email notifications on/off
   - Reminder timing (1 day, 3 days, 1 week before)
   - Notification types to receive

3. **Save Changes**
   - Click "Save Settings"
   - Changes take effect immediately

### Managing Notifications

#### Viewing Notifications
- Bell icon shows unread count
- Click bell to see all notifications
- Mark as read by clicking notification

#### Notification History
- Access full history in settings
- Filter by type and date
- Export notification log if needed

## Reports and Statistics

### Available Reports

#### Monthly Summary
- Total masses celebrated
- Personal mass completion status
- Bulk intention progress
- Special occasion masses

#### Annual Report
- Year-over-year comparison
- Monthly trends and patterns
- Completion rates and statistics
- Bulk intention summary

#### Bulk Intention Report
- All bulk intentions with status
- Completion dates and duration
- Pause/resume history
- Source breakdown

#### Custom Reports
- Select date ranges
- Filter by mass type
- Export to PDF or Excel
- Email reports to administrators

### Generating Reports

1. **Access Reports**
   - Go to "Reports" in main menu
   - Or click "View Reports" from dashboard

2. **Select Report Type**
   - Choose from available report types
   - Set date range if applicable
   - Select filters as needed

3. **Generate and View**
   - Click "Generate Report"
   - View in browser or download
   - Share or print as needed

### Statistics Dashboard

#### Key Metrics
- **Completion Rate**: Percentage of obligations met
- **Average per Month**: Monthly mass celebration average
- **Bulk Progress**: Current bulk intention status
- **Streak**: Consecutive months with complete obligations

#### Charts and Graphs
- Monthly celebration trends
- Mass type distribution
- Completion rate over time
- Bulk intention progress tracking

## Troubleshooting

### Common Issues

#### Login Problems
**Issue**: Cannot log in
**Solutions**:
- Check username and password spelling
- Ensure Caps Lock is off
- Contact administrator for password reset
- Clear browser cache and cookies

#### Mass Recording Issues
**Issue**: Cannot save mass record
**Solutions**:
- Check all required fields are filled
- Verify date format is correct
- Ensure you're not recording duplicate masses
- Refresh page and try again

#### Bulk Intention Problems
**Issue**: Bulk intention not counting down
**Solutions**:
- Ensure you selected "Bulk Intention" as mass type
- Check that bulk intention is active, not paused
- Verify you have active bulk intentions
- Contact administrator if count seems incorrect

#### Import Issues
**Issue**: Excel import failing
**Solutions**:
- Check file format (must be .xlsx or .xls)
- Verify all required columns are present
- Check date formats (YYYY-MM-DD)
- Remove any empty rows
- Ensure file size is under 10MB

### Getting Help

#### Self-Help Resources
- Check this user manual first
- Review FAQ section
- Watch tutorial videos (if available)
- Check system status page

#### Contacting Support
- Use "Contact Administrator" button on login page
- Email support with detailed problem description
- Include screenshots if helpful
- Provide your username and approximate time of issue

#### Emergency Contacts
- For urgent issues during mass times
- Contact your local IT administrator
- Have backup paper recording method ready

### Best Practices

#### Regular Usage
- Log masses daily rather than weekly
- Review monthly obligations regularly
- Keep bulk intentions active and progressing
- Check notifications frequently

#### Data Management
- Import historical data gradually
- Verify imported data accuracy
- Keep Excel backups of important records
- Export reports regularly for records

#### System Maintenance
- Log out when finished using system
- Keep browser updated
- Clear cache if experiencing issues
- Report bugs or suggestions to administrators

## Conclusion

The Mass Tracking System is designed to simplify and automate the tracking of your mass celebrations and obligations. By following this user manual, you should be able to effectively use all features of the system.

Remember:
- The system automatically handles complex bulk intention pause/resume logic
- Monthly personal mass obligations are tracked automatically
- Historical data can be imported from Excel files
- Reports and statistics help you stay on top of your obligations

For additional help or questions not covered in this manual, please contact your system administrator or use the support resources available within the application.

**Happy celebrating and may your mass intentions bring blessings to all!**

