# setup (one time)

1. Push everything to `Sp2736/Sp2736` (repo root). Enable Actions.
2. Secret `PROFILE_TOKEN` - classic PAT (`repo`, `read:user`) so private contributions count and gh-pages branches are readable.
3. Quotes: add secret `ANTHROPIC_API_KEY`, run **generate-quotes** once. It writes 366 morning + 366 night quotes. Edit the JSON by hand any time.
4. Run **update-profile** once (Actions tab) to create the SVGs. After that it runs at 06:00 IST, 21:00 IST and every 6 hours.
5. masteryOS: set repo variable `MASTERYOS_STATS_URL` (and optional secret `MASTERYOS_STATS_TOKEN`). Expected JSON:
   `{"title":"masteryOS utilisation","metrics":[{"label":"active users","value":128}],"series":{"label":"sessions / day","points":[{"date":"2026-11-01","value":12}]}}`
6. Instant deploy updates (optional): in each project's deploy workflow, after the gh-pages deploy step add
```yaml
      - name: notify profile
        if: success()
        run: >
          curl -s -X POST -H "Authorization: Bearer ${{ secrets.PROFILE_TOKEN }}"
          -H "Accept: application/vnd.github+json"
          https://api.github.com/repos/Sp2736/Sp2736/dispatches
          -d '{"event_type":"project-deployed"}'
```
Without it the 6-hourly scan still picks up every repo that has a `gh-pages` branch.
