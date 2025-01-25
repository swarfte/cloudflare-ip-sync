# cloudflare-ip-sync
automatically update the domain ip address in cloudflare , when the ip address of the server changes

## Setup

### Install dependencies
```
python cloudflare_dns_update.py
```

### setup config file
1. create a new file named config.json
2. copy config.example.yaml to config.json
3. create the api token in cloudflare and get the zone id
4. set the permission of the api token
   - Zone Permissions: **Zone DNS: Edit, Zone DNS: Read**
   - Zone Resources: **Include: All Zones**
5. fill the config.json with the api token and zone id, and the domain you want to update
