# CareerFlow — Application Manager (Day 1)

## Purpose
CareerFlow helps you collect, organize and track job applications. On Day 1 we implement:
- OOP-based backend structure (models, services)
- Upload and parse LinkedIn "Saved Jobs" HTML file
- Save parsed jobs into MySQL
- Async UI pattern to upload and replace the job list without full page reload with a personal tool.

## Stack
- Python 3.10+ (Flask)
- MySQL (mysql-connector-python)
- BeautifulSoup (HTML parsing)
- Chart.js (future dashboards)
- reportlab / openpyxl (future exports)
- APScheduler (future reminders)

## TODO-TODay
1. Create and activate a virtual environment:
   - `python -m venv .box`
   - `source `.box\Scripts\activate` (Windows)

2. Install dependencies:
   - `pip install -r requirements.txt`

3. Create a `.env` file with:
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=

4. Create MySQL database `DB` and grant privileges to DB_USER.
5. Run the app:
- `python -m app.main`
6. Open `http://127.0.0.1:5000` and upload your saved LinkedIn jobs HTML file (hope you have some!).

## Project conventions (Day 1)
- OOP-first: Model classes for persistence, Services for business logic.
- Clear naming: functions and variables have looong descriptive names.
- Small controllers: routes delegate heavy lifting to services.

## Next steps / future features 
1. **Cover letter generator**: use job description to render templated PDF cover letters (reportlab or HTML to PDF).
2. **Scheduler & reminders**: APScheduler to email reminders for follow-ups. (maybe not)

## Notes
- LinkedIn scraping is not the best option; for reliability require users to upload their HTML export (manually).
