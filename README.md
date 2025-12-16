Create venv
python3.11 -m venv memvix


macOS/Linux (Bash/Zsh):
bash
source memvix/bin/activate
Windows (Command Prompt):
bash
memvix\Scripts\activate.bat


Windows (PowerShell):
powershell
.\memvix\Scripts\Activate.ps1


pip install -r requirements.txt




running
uvicorn app.main:app --reload

python -m app.workers.reminder_worker


From your project root (remindz):

docker compose up -d


To stop:

docker compose down



---
source venv/bin/activate     

ngrok http --url=barotropic-unsportful-may.ngrok-free.dev 8080