# gh_crawler

To install project and all dependencies use `make install`

Create `input.json` file for crawler args, e.g.
```
{
 "keywords": ["openstack", "nova", "css"],
 "proxies": ["194.126.37.94:8080", "13.78.125.167:8080"],
 "type": "Repositories"
}
```
Run crawler with command `make crawl`

Result will be presented in `output.json`