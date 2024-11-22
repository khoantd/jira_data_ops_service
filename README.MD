git init
git add .
git commit -m "my commit"
git remote set-url main https://github.com/khoantd/jira_data_ops_service.git
git push main main

docker build -t jira_data_ops .