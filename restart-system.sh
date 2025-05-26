#!/bin/bash
echo "Restarting system..."
./stop-system.sh
sleep 5
./start-system.sh
