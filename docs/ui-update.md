# UI update

The dashboard now places **Price forecast** and **Recent price history** side by side on wide screens and stacks them on narrow screens. The forecast horizon selector is in the page header and updates both the forecast horizon and the matching number of recent historical months. Summary cards for last observation, forecasting method and data freshness remain at the top.

Run from `frontend`:
```powershell
npm run dev
```
If the Next.js server is already running, save the file and refresh the browser. If it does not reload, stop it with Ctrl+C and run `npm run dev` again.
