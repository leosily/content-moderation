# AI内容审核系统

## 使用前环境配置
```
cd front
npm build
cd ..
python -m venv 虚拟环境名(如myvenv)
.\myvenv\Scripts\activate
cd backend
pip intall -r requirement.txt
下载docker desktop,然后docker run -d -p 6379:6379 --name 镜像名(如myRedis) -v redis-data:/data redis redis-server --appendonly yes
```

## 使用方法
```
#新建powershell
.\myvenv\Scripts\activate
cd backend
docker start myRedis
uvicorn main:app

#新建powershell
cd front
npm run dev

#新建powershell
celery -A celery_apps.celery_app.celery_app worker --loglevel=info --pool=solo
```