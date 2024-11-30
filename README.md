# GymProof

`sudo nano /etc/systemd/system/github-runner.service`
`sudo nano /etc/systemd/system/gym_proof.service`
[Unit]
Description=GymPRoof Bot
After=network.target

[Service]
ExecStart=/bin/bash /home/pi/GymPRoof/run.sh
WorkingDirectory=/home/pi/GymPRoof
Restart=always
User=pi

[Install]
WantedBy=multi-user.target


[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
ExecStart=/bin/bash /home/pi/actions-runner/run.sh
WorkingDirectory=/home/pi/actions-runner
Restart=always
User=pi

[Install]
WantedBy=multi-user.target



# Reload systemd to register new services
sudo systemctl daemon-reload

# Enable services to start at boot
sudo systemctl enable github-runner.service
sudo systemctl enable gym_proof.service

# Start services immediately
sudo systemctl restart github-runner.service
sudo systemctl restart gym_proof.service

# Check the status of each service
sudo systemctl status github-runner.service
sudo systemctl status gym_proof.service