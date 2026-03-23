# Yesferal Page

## Setup Custom Domain
First, we have to set up the yesferal.github.io page:
 - We go to Settings → Pages (GitHub Pages)
 - Under Source:
   - Select: Deploy from a branch
   - Branch: main
   - Folder: / (root)

In GoDaddy DNS we should have:
```
Type: A   Name: @   Value: 185.199.108.153
Type: A   Name: @   Value: 185.199.109.153
Type: A   Name: @   Value: 185.199.110.153
Type: A   Name: @   Value: 185.199.111.153
```
We should add this record as well:
```
Type: CNAME
Name: www
Value: yesferal.github.io
```
After that we:
  - Set the Custom domain (yesferal.com)
  - Enable HTTPS
    - Check Enforce HTTPS
## Setup AdMobs
Create a file:
```
app-ads.txt
```
With content:
```
google.com, pub-2957187797569353, DIRECT, f08c47fec0942fa0
```
This content can be obtained from our AdMobs account
