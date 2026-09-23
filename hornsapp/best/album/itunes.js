/**
 * iTunes Search API client for HornsApp best-albums pages (browser / runtime).
 *
 * Loaded by generated year pages via <script src="/hornsapp/best/album/itunes.js">.
 * This file talks to Apple's public Search API from the visitor's browser.
 *
 * Responsibilities:
 *   - Load album cover images into [data-cover-artist][data-cover-album] slots
 *   - On miss/error, show a gray HornsApp logo fallback (/images/hornsapp.png)
 *   - Fill .album-listen-apple href with collectionViewUrl (Apple Music)
 *   - Make the cover <a> open that Apple Music album when available
 *
 * Not in this file:
 *   - Spotify links — built at generate time (scripts/hornsapp/spotify.py)
 *   - Cover HTML slots / Apple placeholders — scripts/hornsapp/itunes.py
 */
(function () {
  var FALLBACK_COVER = "/images/hornsapp.png";

  function coverKey(artist, album) {
    return "ha-cover-v2:" + artist + "|" + album;
  }

  function applyAppleLink(root, appleUrl) {
    if (!root || !appleUrl) return;
    var apple = root.querySelector(".album-listen-apple");
    if (apple) {
      apple.href = appleUrl;
      apple.hidden = false;
    }
    var cover = root.querySelector(".album-cover, .year-featured-cover");
    if (cover && cover.tagName === "A") {
      cover.href = appleUrl;
      cover.target = "_blank";
      cover.rel = "noopener noreferrer";
      cover.removeAttribute("aria-hidden");
      cover.setAttribute("aria-label", "Open in Apple Music");
      cover.removeAttribute("tabindex");
    }
  }

  function applyFallback(img) {
    var wrap = img.closest(".album-cover, .year-featured-cover");
    img.src = FALLBACK_COVER;
    img.alt = "";
    if (wrap) {
      wrap.classList.add("has-cover", "is-fallback");
    }
  }

  function applyCover(img, coverUrl, appleUrl) {
    var root = img.closest(".album-item, .year-featured");
    var wrap = img.closest(".album-cover, .year-featured-cover");
    if (coverUrl) {
      img.src = coverUrl;
      img.onload = function () {
        if (wrap) {
          wrap.classList.add("has-cover");
          wrap.classList.remove("is-fallback");
        }
      };
      img.onerror = function () {
        applyFallback(img);
      };
    } else {
      applyFallback(img);
    }
    applyAppleLink(root, appleUrl);
  }

  function fetchCover(img) {
    var artist = img.getAttribute("data-cover-artist") || "";
    var album = img.getAttribute("data-cover-album") || "";
    if (!artist || !album) {
      applyFallback(img);
      return Promise.resolve();
    }
    var key = coverKey(artist, album);
    try {
      var cached = sessionStorage.getItem(key);
      if (cached) {
        var parsed = JSON.parse(cached);
        applyCover(img, parsed.cover, parsed.apple);
        return Promise.resolve();
      }
    } catch (e) {}

    var term = encodeURIComponent(artist + " " + album);
    return fetch("https://itunes.apple.com/search?term=" + term + "&entity=album&limit=1")
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        var hit = data && data.results && data.results[0];
        if (!hit) {
          applyFallback(img);
          return;
        }
        var art = hit.artworkUrl100;
        var cover = art
          ? art.replace("100x100bb", "600x600bb").replace("100x100", "600x600")
          : "";
        var apple = hit.collectionViewUrl || "";
        try {
          sessionStorage.setItem(key, JSON.stringify({ cover: cover, apple: apple }));
        } catch (e) {}
        applyCover(img, cover, apple);
      })
      .catch(function () {
        applyFallback(img);
      });
  }

  function loadCovers() {
    var imgs = document.querySelectorAll("img[data-cover-artist]");
    var i = 0;
    function next() {
      if (i >= imgs.length) return;
      fetchCover(imgs[i++]).then(next);
    }
    next();
    next();
    next();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadCovers);
  } else {
    loadCovers();
  }
})();
