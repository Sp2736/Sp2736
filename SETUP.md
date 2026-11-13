# setup

Nothing here needs an LLM or any paid key.

## minimum (works with zero secrets)
1. Push all files to the repo `Sp2736/Sp2736` (root of the repo, same name as your username).
2. Repo -> **Settings -> Actions -> General -> Workflow permissions** -> choose **Read and write permissions** -> Save.
3. Repo -> **Actions** tab -> **update-profile** -> **Run workflow**. This creates the SVGs. After that it runs on its own at 06:00 IST, 21:00 IST and every 6 hours.

## optional: PROFILE_TOKEN (private contributions + faster deploy updates)
Without it, only public activity is counted.
1. GitHub -> profile picture -> **Settings -> Developer settings -> Personal access tokens -> Tokens (classic) -> Generate new token (classic)**.
2. Tick `repo` and `read:user`, set an expiry, generate, copy it.
3. Repo `Sp2736/Sp2736` -> **Settings -> Secrets and variables -> Actions -> Secrets tab -> New repository secret**. Name: `PROFILE_TOKEN`, value: the token.

## masteryOS + leetcode
Nothing to set. They use the same public sources as your portfolio:
- masteryOS: `https://mastery-os-omega.vercel.app/api/public/swayam/stats` (streak + skill progress)
- leetcode: `alfa-leetcode-api.onrender.com`, user `_sp_1`
That leetcode API runs on a free Render server that sleeps, so a run can occasionally show "unavailable"; the next run fixes it.

## optional: instant update after a gh-pages deploy
Without this the 6-hourly scan still picks up any repo that has a `gh-pages` branch.
In each project repo: **Settings -> Secrets and variables -> Actions** -> add secret `PROFILE_TOKEN` (same token as above), then add this step after the deploy step in its workflow:
```yaml
      - name: notify profile
        if: success()
        run: >
          curl -s -X POST -H "Authorization: Bearer ${{ secrets.PROFILE_TOKEN }}"
          -H "Accept: application/vnd.github+json"
          https://api.github.com/repos/Sp2736/Sp2736/dispatches
          -d '{"event_type":"project-deployed"}'
```

## editing
- Projects: `config/projects.json`. Replace the `MARKETPLACE-LINK-…` urls there.
- Quotes: `quotes/day.json` and `quotes/night.json` (366 each, edit freely).
