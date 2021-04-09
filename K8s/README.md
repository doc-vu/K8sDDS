# K8sDashboard
 
```sh
mkdir /certs
openssl req -nodes -newkey rsa:2048 \
     -keyout certs/dashboard.key \
     -out certs/dashboard.csr -subj "/C=/ST=/L=/O=/OU=/CN=kubernetes-dashboard"
## 利用 key 和私钥生成证书
openssl x509 -req -sha256 \
     -days 365 \
     -in certs/dashboard.csr \
     -signkey certs/dashboard.key \
     -out certs/dashboard.crt

# --- alternative
openssl x509 -req -in certs/dashboard.csr \
     -CA /etc/kubernetes/pki/ca.crt \
     -CAkey /etc/kubernetes/pki/ca.key \
     -CAcreateserial \
     -out certs/dashboard.crt \
     -days 365

# 证书签发完成后，查看 /certs :
ls /certs/
dashboard.crt  dashboard.csr  dashboard.key

# 在 K8S 集群中创建 kubernetes-dashboard 命名空间并创建相应的 secret
kubectl create ns kubernetes-dashboard
kubectl create secret generic kubernetes-dashboard-certs --from-file=/certs -n kubernetes-dashboard

cd kubernetes-dashboard/deploy
kubectl apply -f .

cd kubernetes-dashboard/access
kubectl apply -f .

# get token
kubectl -n kubernetes-dashboard get secret \
     -o jsonpath='{range .items[?(@.metadata.annotations.kubernetes\.io/service-account\.name=="dashboard-admin-sa")].data}{.token}{end}' | base64 -d


# Google CAdvisor:
VERSION=v0.36.0 # use the latest release version from https://github.com/google/cadvisor/releases
sudo docker run \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=8080:8080 \
  --detach=true \
  --name=cadvisor \
  --privileged \
  --device=/dev/kmsg \
  gcr.io/cadvisor/cadvisor:$VERSION
```
