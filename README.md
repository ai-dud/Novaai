# AI Voice Assistant

A Hindi voice assistant that can help you with various tasks. This assistant can open websites, play YouTube videos, and answer questions in Hindi.

### Installation On Windows

1. Install git from https://git-scm.com/
2. install python 3.10 from Microsoft store
3. Visit [Ollama's website](https://ollama.ai)
4. Download and install Ollama for Windows
5. open terminal and paste this command
```bash
ollama pull llama3.2
```

6. Clone the Repository
```bash
git clone https://github.com/ai-dud/Novaai.git
cd Novaai
```

7. Change the policy
```bash
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

8. Create and Activate Virtual Environment:
```bash
python -m venv venv
venv\Scripts\activate
```
9. Install Dependencies:
```bash
pip install -r requirements.txt
pip install pyaudio
```

10. Run the code
```bash
 python ai_assistant.py
```

11. if you want to run the code again from starting
```bash
cd Echoai
python -m venv venv
venv\Scripts\activate
python ai_assistant.py
```
