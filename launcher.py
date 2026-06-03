import os
import subprocess
import time
import webview
import signal
import sys

def run_launcher():
    # 1. Start the streamlit server in a headless subprocess
    print("Démarrage du serveur Streamlit...")
    
    # We use a context manager or subprocess.Popen to keep a reference to the process
    # so we can kill it later.
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 2. Give Streamlit a second to boot up
    time.sleep(3)

    # 3. Create the native desktop window
    window = webview.create_window(
        title='Market Dashboard',
        url='http://localhost:8501',
        width=1400,
        height=900,
        min_size=(1000, 600)
    )

    # 4. Define what happens when the window closes
    def on_closed():
        print("Fermeture de l'application...")
        streamlit_process.terminate()
        streamlit_process.wait()
        print("Serveur arrêté.")

    window.events.closed += on_closed

    # 5. Start the WebView UI (this blocks until the window is closed)
    webview.start()

if __name__ == '__main__':
    run_launcher()
