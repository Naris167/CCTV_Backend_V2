```bash
npm init -y
npm install express axios node-cron p-limit date-fns
```

```bash
git filter-branch --index-filter "git rm -rf --cached --ignore-unmatch ./.env.prod" HEAD
git push origin --force --all
```

```bash
npm install -g bun
```