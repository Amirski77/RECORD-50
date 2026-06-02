# RECORD

#### Video Demo: <YOUTUBE_URL_HERE>

#### Description:

RECORD is a web app where each user posts one song per day. That single
rule is the whole point. The feed shows what everyone is listening to
today, and your profile shows all your past records as a music diary.

I had the idea when I wanted to share one Clipse song with my friends.
Instagram stories felt cheap. Spotify share got lost in chats. So I
built a place for one song, one day, one note.

## How it works

### One song per day

Every user can post only one record per day. "Day" means UTC, so the
feed resets at midnight UTC for everyone. The check happens on the
server in the `/post` route. It looks at the `posts` table and asks:
does this user already have a row with today's date? If yes, block.
If no, allow. I keep this check in Python and not in the database so
the error message is friendly ("come back tomorrow") instead of a SQL
crash.

### Search

When you type in the search box, JavaScript sends your query to my
Flask route `/api/search`. That route calls the iTunes Search API,
trims the response down to five fields (track id, name, artist,
album art, preview URL), and sends clean JSON back.

The search has a few details I am proud of:

- Debouncing with a 300ms timer, so I don't hit iTunes on every keystroke
- AbortController, so a slow old request can't overwrite a fast new one
- DocumentFragment, so all 25 result tiles appear at once instead of one by one
- Clear error and empty states

### Posting

Click a search tile. A preview panel shows the album art bigger, the
track info, and a text box for an optional note (max 280 chars). Hit
post. The server validates everything, checks the one-per-day rule,
and writes a new row.

### Feed and profile

The home page is the global feed for today. It joins `posts` with
`users` so I can show who posted each record. Newest first.

Each album cover has a play button that shows on hover. Clicking it
plays the 30-second iTunes preview right there. Only one preview can
play at a time.

The profile page `/user/<username>` shows that user's records, newest
first, with no date filter. It is the music diary.

## Files

- `app.py` — All routes: auth, search, post, feed, profile
- `db.py` — SQLite helper. Opens connections per request, auto-creates the DB on first boot
- `schema.sql` — Three tables: users, posts, reactions (reactions are for v2)
- `templates/` — All Jinja templates
- `static/styles.css` — Dark theme, Spotify-style
- `static/app.js` — Search-as-you-type, click to select, audio preview logic
- `Procfile` — Tells Render to run gunicorn
- `requirements.txt` — Python dependencies

## Design choices

**Track info is copied into each post.** I save the track name, artist,
and image URL right on the post row. I don't just save the iTunes id
and re-fetch later. This way the feed loads fast and still works when
iTunes is down.

**No follows.** Everyone sees everyone's records. With small group of
friends this feels alive. A follow system on an empty app feels dead.
Follows are for future v2.

## Future ideas

- Hearts on records (the table already exists)
- Follows and a friends-only feed
- iOS app — the real product lives on mobile
- Concert mode — connect users going to the same show

This was my first real full-stack project. I learned more from it
than from any tutorial.