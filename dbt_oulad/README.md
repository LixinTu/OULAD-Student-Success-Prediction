# dbt_oulad

Create a local dbt profile named `dbt_oulad` (usually in `~/.dbt/profiles.yml`):

```yaml
dbt_oulad:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: oulad
      password: oulad
      port: 5432
      dbname: oulad_analytics
      schema: public
      threads: 4
```

Then run:

```bash
cd dbt_oulad
dbt run
dbt test
```
