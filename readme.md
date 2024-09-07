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






'''
if jsut fetching the image ican keep session ID alive, Then we can do this like every 10 minute. So we don't have to fetch session ID again.
But if there are any image the less than 5120 bytes, we have to fetch the session ID 

But we have to think more for this approach as some cctv might come back online but we did not fetch the session ID (maybe we can fetch session ID every 30 minute or 1 hours)

Now we have to test if this will work or not, or we have to play video to keep session alive.

Also, if this way can keep it alive. How long can session ID last? 


And if we did not do anything with t he session ID, how long it will last?

Even we can keep session ID alive, we still have to fetch from bmatraffic to make sure that cctv list in DB is updated.

Conclusion:
1. It has been tested that getting image every 1 minutes for 80 minutes can keep session alive
2. It has been tested that play video every 1 minutes for 80 minutes can keep session alive.
3. Expired session ID cannot be recover.
4. Session ID will be expried after 20 minutes if there is no play video or getting image.
5. Test it to see if playing video every 18 minutes for whole day can still keep sesssion ID alive or not.
'''