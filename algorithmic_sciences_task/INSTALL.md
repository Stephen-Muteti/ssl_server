# Running the Server as a Linux Daemon

To install and run the TCP file search server as a background Linux service using systemd:

---

**Important**:
The code gracefully handles the mode in which the server runs and so no changes to the code are needed for this guide.

**NOTE**: It is assumed in this deployment that you have placed the project in the `/opt/algorithmic_sciences_task` directory.


## Prerequisites

### 1. Python Virtual Environment

Ensure you have Python 3.9+ installed.

Create and activate a Python virtual environment inside the project root directory. Install
the required python libraries as below:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### SSL SETUP
Follow [SSL SETUP GUIDE](./SSL_SETUP.md) to geberate the ssl files for the server.

---


## 1. Set the Correct Directory Permissions

**Important**
Ensure that the user `stephen_algorithmic_sciences` exists on the system.
You can create it using:

```bash
sudo useradd -m stephen_algorithmic_sciences
```

Ensure that the server files are owned by the correct system user (replace `stephen_algorithmic_sciences` if needed):

```bash
sudo chown -R stephen_algorithmic_sciences:stephen_algorithmic_sciences /opt/algorithmic_sciences_task
sudo chmod -R 755 /opt/algorithmic_sciences_task
```


## 2. Create a systemd service file:
```bash
sudo nano /etc/systemd/system/tcpserver.service
```

Paste the following content(edit the user and paths accordingly depending on how you have set up the project
in the previous steps):

We use the python installation in our Python virtual environment that has been installed with all the requirements from
prerequisites.

`WorkingDirectory=/opt/algorithmic_sciences_task` points to the project's root directory. You can replace it with the
actual root directory of the project.

`/opt/algorithmic_sciences_task/run_server.py` refers to the server's entry script. If this has not been changed then leave it as is.

`StandardOutput=append:/var/log/tcpserver.log`
`StandardError=append:/var/log/tcpserver_error.log`

The above lines dictate where our server's logs will be stored. We ensure the correct permissions of these files in **step 3**

```bash
[Unit]
Description=Algorithmic Sciences Python TCP Server
After=network.target

[Service]
Type=simple
User=stephen_algorithmic_sciences
WorkingDirectory=/opt/algorithmic_sciences_task
ExecStart=/opt/algorithmic_sciences_task/.venv/bin/python /opt/algorithmic_sciences_task/run_server.py
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/tcpserver.log
StandardError=append:/var/log/tcpserver_error.log

[Install]
WantedBy=multi-user.target
```

**NB**: Ensure that /var/log/tcpserver.log and /var/log/tcpserver_error.log are writable by the specified user, or create them manually if needed.


## 3. Set permissions and reload systemd:

1. **For the service file**
```bash
sudo chmod 744 /etc/systemd/system/tcpserver.service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
```

2. **Entire project**

Make sure the entire project is owned by the user `stephen_algorithmic_sciences`.

```bash
sudo chown -R stephen_algorithmic_sciences:stephen_algorithmic_sciences /opt/algorithmic_sciences_task
```

3. **`run_server.py` and `client.py`**

Allow the daemon user to read, write, and execute, while others can only read `run_server.py` and `client.py`

```bash
sudo chmod 744 /opt/algorithmic_sciences_task/server/run_server.py
sudo chmod 744 /opt/algorithmic_sciences_task/client/client.py
```

4. **Config file**

Only the daemon user should be able to read/write these files, others cannot access them.
```bash
sudo chmod 640 /opt/algorithmic_sciences_task/config/server_config.yaml
```

5. **SSL Private Keys**

Restrict access strictly to the daemon user, preventing security risks.

```bash
sudo chmod 600 /opt/algorithmic_sciences_task/certs/server.key
sudo chmod 600 /opt/algorithmic_sciences_task/certs/client.key
```

6. **SSL Certificates**

Certificates are public and used for authentication, so they must be readable by other processes.

```bash
sudo chmod 644 /opt/algorithmic_sciences_task/certs/server.crt
sudo chmod 644 /opt/algorithmic_sciences_task/certs/client.crt
```

7. **Log files**

Ensure the daemon user owns the log files.

```bash
sudo chown stephen_algorithmic_sciences:stephen_algorithmic_sciences /var/log/tcpserver.log
sudo chown stephen_algorithmic_sciences:stephen_algorithmic_sciences /var/log/tcpserver_error.log
```

Allow the daemon user to write logs while preventing unauthorized modifications.

```bash
sudo chmod 640 /var/log/tcpserver.log
sudo chmod 640 /var/log/tcpserver_error.log
```

For frequent logging, allow append-only mode to prevent accidental modifications or deletions, allowing only appending.

```bash
sudo chattr +a /var/log/tcpserver.log
sudo chattr +a /var/log/tcpserver_error.log
```

## 4. Enable and start the service:
```bash
sudo systemctl enable tcpserver.service
sudo systemctl start tcpserver.service
```

Once enabled, the server will automatically start on system boot.

## 5. Check service status and Logs:

Status

```bash
sudo systemctl status tcpserver.service
```

Logs
```bash
tail -f /var/log/tcpserver.log
tail -f /var/log/tcpserver_error.log
```


## 6. Connecting a Client to the Running Server

Once the server is running as a background service, you can connect a client to it using the provided client module.

Ensure you're in the project root directory and that the virtual environment is activated:
```bash
cd /opt/algorithmic_sciences_task
source .venv/bin/activate
python -m client.client
```

This will initiate a secure SSL connection to the daemonized server, allowing you to issue search queries from the client interface.

The line `Algorithmic Sciences loves speed` exists in the search file. Try it!

## Author

Stephen Muteti
