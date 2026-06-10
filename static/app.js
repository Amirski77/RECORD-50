const input = document.querySelector("#search-input");
const results = document.querySelector("#search-results");
const statusEl = document.querySelector("#search-status");

if (input) {
    let debounceTimer;
    let abortController = null;
    let selectedTrack = null;

    input.addEventListener("input", () => {
        clearTimeout(debounceTimer);

        debounceTimer = setTimeout(async () => {
            const query = input.value.trim();
        // 1. ALWAYS cancel previous pending requests first, regardless of what the query is
            if (abortController) {
                abortController.abort();
            }
        // 2. Now handle the empty input state safely
            if (!query) {
                results.innerHTML = "";
                statusEl.textContent = "";
                selectedTrack = null;
                const panel = document.querySelector("#post-panel");
                if (panel) panel.hidden = true;
                return;
            }
        // 3. Now create a new abort controller for the new request
            abortController = new AbortController();
        // 4. Update the status text to indicate that we're searching
            statusEl.textContent = "Searching...";
            selectedTrack = null;
            const panel = document.querySelector("#post-panel");
            if (panel) panel.hidden = true;

            try {
                // 5. Make the actual API request
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
                    signal: abortController.signal
                });

                // 6. Handle errors
                if (!response.ok) {
                    throw new Error("Server error");
                }

                // 7. Parse the response
                const data = await response.json();

                // 8. Update the status text to indicate that we're done searching
                statusEl.textContent = "";

                if (!data.results || data.results.length === 0) {
                    statusEl.textContent = "No results found.";
                    results.innerHTML = "";
                    abortController = null;
                    return;
                }

                // 10. Create a document fragment to hold the results
                const fragment = document.createDocumentFragment();

                for (const track of data.results) {
                    const tile = document.createElement("div");
                    tile.className = "search-tile";

                    const img = document.createElement("img");
                    img.src = track.album_art_url;
                    img.alt = `${track.track_name} album art`;

                    const info = document.createElement("div");
                    info.className = "search-tile-info";

                    const trackName = document.createElement("div");
                    trackName.className = "search-tile-name";
                    trackName.textContent = track.track_name;

                    const artistName = document.createElement("div");
                    artistName.className = "search-tile-artist";
                    artistName.textContent = track.artist_name;

                    info.appendChild(trackName);
                    info.appendChild(artistName);
                    tile.appendChild(img);
                    tile.appendChild(info);

                    tile.addEventListener("click", () => {
                        document.querySelectorAll(".search-tile").forEach(el => {
                            el.classList.remove("selected");
                        });
                        // 12. Update the selected track and add the selected class to the clicked tile
                        tile.classList.add("selected");
                        selectedTrack = track;
                        showPostPanel(track);
                    });
                    // 13. Append the tile to the fragment
                    fragment.appendChild(tile);
                }
                results.replaceChildren(fragment);
                abortController = null;
                // 11. Reset the abort controller for the next request
            } catch (error) {
                if (error.name !== "AbortError") {
                    abortController = null;
                    console.error("Search failed:", error);
                    statusEl.textContent = "Something went wrong. Please try again.";
                    results.innerHTML = "";
                }
            }
        }, 300);
    });
}
function showPostPanel(track) {
    const panel = document.querySelector("#post-panel");
    if (!panel) return;

    document.querySelector("#preview-art").src = track.album_art_url;
    document.querySelector("#preview-art").alt = `${track.track_name} album art`;
    document.querySelector("#preview-name").textContent = track.track_name;
    document.querySelector("#preview-artist").textContent = track.artist_name;

    document.querySelector("#form-track-id").value = track.track_id;
    document.querySelector("#form-track-name").value = track.track_name;
    document.querySelector("#form-artist-name").value = track.artist_name;
    document.querySelector("#form-album-art-url").value = track.album_art_url;
    document.querySelector("#form-preview-url").value = track.preview_url ||"";

    panel.hidden = false;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

const noteInput = document.querySelector("#form-note");
const charCount = document.querySelector("#char-count");
if (noteInput && charCount) {
    noteInput.addEventListener("input", () => {
        charCount.textContent = `${noteInput.value.length} / 280`;
    });
}

let currentAudio = null;
let currentButton = null;

function playPreview(button) {
    const url = button.dataset.preview;
    if (!url) return;

    if (currentButton === button) {
        currentAudio.pause();
        resetButton(button);
        currentAudio = null;
        currentButton = null;
        return;
    }

    if (currentAudio) {
        currentAudio.pause();
        if (currentButton) resetButton(currentButton);
    }

    const audio = new Audio(url);
    audio.play().catch(err => {
        console.error("Audio playback failed:", err);
        resetButton(button);
    });

    audio.addEventListener("ended", () => {
        resetButton(button);
        currentAudio = null;
        currentButton = null;
    });

    button.classList.add("playing");
    button.querySelector(".play-icon").textContent = "⏸";

    currentAudio = audio;
    currentButton = button;
}

function resetButton(button) {
    button.classList.remove("playing");
    const icon = button.querySelector(".play-icon");
    if (icon) icon.textContent = "▶";
}

document.querySelectorAll(".play-btn").forEach(btn => {
    btn.addEventListener("click", () => playPreview(btn));
});

document.querySelectorAll(".reaction-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const bar = btn.closest(".reactions");
      const postId = bar.dataset.postId;
      const type = btn.dataset.type;
  
      try {
        const res = await fetch("/react", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ post_id: postId, type: type }),
        });
        if (!res.ok) return;
        const data = await res.json();
  
        // update every button's count in this bar
        bar.querySelectorAll(".reaction-btn").forEach((b) => {
          const t = b.dataset.type;
          const count = data.counts[t] || 0;
          const span = b.querySelector(".rcount");
          if (span) span.textContent = count;
        });
      } catch (e) {
        // network error — just ignore for now
      }
    });
  });