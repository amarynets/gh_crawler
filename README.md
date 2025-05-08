# gh_crawler

To install project and all dependencies use `make install`

Create `input.json` file for crawler args, e.g. Make sure that proxy list has working proxy as there no error handling for bad proxy
```
{
 "keywords": ["openstack", "nova", "css"],
 "proxies": ["194.126.37.94:8080", "13.78.125.167:8080"],
 "type": "Repositories"
}
```
Run crawler with command `make crawl`

Result will be presented in `output.json`

TODO
1. Retry handling
2. Error handling
3. Queue lock handling in case of error
3. Middlewares
4. Maybe add test for parser itself, but as it changed dynamically, not sure
