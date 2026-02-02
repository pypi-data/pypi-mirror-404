chmod -R 777 /kcwebps
cd /kcwebps
sleep 1
pkill kcwebps
nohup kcwebps --host 0.0.0.0 --port 39001 --processcount 4 --timeout 3600 server -start > app/runtime/log/server.log 2>&1 &