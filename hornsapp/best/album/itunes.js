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
 * Lookup strategy (free-text album search is unreliable for famous titles):
 *   1. Resolve artist via entity=musicArtist
 *   2. lookup?id=…&entity=album and match title on that artist's catalog
 *   3. Fall back to term search, still requiring an artist name match
 * Optional data-cover-year nudges remasters vs original editions.
 *
 * Not in this file:
 *   - Spotify links — built at generate time (scripts/hornsapp/spotify.py)
 *   - Cover HTML slots / Apple placeholders — scripts/hornsapp/itunes.py
 */
(function () {
  var FALLBACK_COVER = "/images/hornsapp.png";
  var ARTIST_CACHE = {};

  function coverKey(artist, album) {
    return "ha-cover-v5:" + artist + "|" + album;
  }

  function norm(s) {
    s = String(s || "").toLowerCase();
    var repl = {
      ö: "o",
      ü: "u",
      ä: "a",
      ß: "ss",
      ø: "o",
      é: "e",
      è: "e",
      ê: "e",
      á: "a",
      à: "a",
      í: "i",
      ó: "o",
      ú: "u",
      ñ: "n",
      ç: "c",
      "\u2019": "'",
      "\u2018": "'",
      "\u02bc": "'",
      "`": "'"
    };
    Object.keys(repl).forEach(function (k) {
      s = s.split(k).join(repl[k]);
    });
    return s
      .replace(/[^a-z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function isSingle(name) {
    var n = String(name || "").toLowerCase();
    return n.indexOf(" - single") !== -1 || n.indexOf("(single)") !== -1;
  }

  function parseYear(y) {
    if (y == null || y === "" || y === "?") return null;
    var n = parseInt(String(y).slice(0, 4), 10);
    return n >= 1900 && n <= 2100 ? n : null;
  }

  function artistMatches(want, got) {
    if (!want) return true;
    return got.indexOf(want) !== -1 || want.indexOf(got) !== -1;
  }

  function titleMatches(want, got) {
    if (!want || !got) return false;
    return got.indexOf(want) !== -1 || want.indexOf(got) !== -1;
  }

  function scoreAlbum(hit, artist, title, year) {
    var name = hit.collectionName || "";
    var art = hit.artistName || "";
    var wantTitle = norm(title);
    var wantArtist = norm(artist);
    var gotTitle = norm(name);
    var gotArtist = norm(art);
    if (!titleMatches(wantTitle, gotTitle)) return null;
    if (!artistMatches(wantArtist, gotArtist)) return null;
    if (isSingle(name)) return null;
    var exact = gotTitle === wantTitle ? 2 : 1;
    var brevity = -gotTitle.length;
    var yearScore = 0;
    if (year) {
      var rd = String(hit.releaseDate || "").slice(0, 4);
      if (/^\d{4}$/.test(rd)) {
        var delta = Math.abs(parseInt(rd, 10) - year);
        yearScore = -delta;
        if (delta === 0) yearScore += 2;
      }
    }
    return { exact: exact, yearScore: yearScore, brevity: brevity, hit: hit };
  }

  function pickAlbum(results, artist, title, year) {
    var best = null;
    (results || []).forEach(function (hit) {
      var s = scoreAlbum(hit, artist, title, year);
      if (!s) return;
      if (
        !best ||
        s.exact > best.exact ||
        (s.exact === best.exact && s.yearScore > best.yearScore) ||
        (s.exact === best.exact &&
          s.yearScore === best.yearScore &&
          s.brevity > best.brevity)
      ) {
        best = s;
      }
    });
    return best ? best.hit : null;
  }

  function artworkFrom(hit) {
    if (!hit) return { cover: "", apple: "" };
    var art = hit.artworkUrl100 || "";
    return {
      cover: art
        ? art.replace("100x100bb", "600x600bb").replace("100x100", "600x600")
        : "",
      apple: hit.collectionViewUrl || ""
    };
  }

  function resolveArtistId(artist) {
    var key = norm(artist);
    if (Object.prototype.hasOwnProperty.call(ARTIST_CACHE, key)) {
      return Promise.resolve(ARTIST_CACHE[key]);
    }
    return fetch(
      "https://itunes.apple.com/search?term=" +
        encodeURIComponent(artist) +
        "&entity=musicArtist&limit=8"
    )
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        var want = norm(artist);
        var bestId = null;
        var bestScore = -1;
        (data.results || []).forEach(function (hit) {
          var got = norm(hit.artistName || "");
          var id = hit.artistId;
          if (!id) return;
          if (got === want) {
            bestId = id;
            bestScore = 1e9;
            return;
          }
          var score = 0;
          if (got.indexOf(want) !== -1 || want.indexOf(got) !== -1) {
            score = Math.min(want.length, got.length);
          }
          if (score > bestScore) {
            bestScore = score;
            bestId = id;
          }
        });
        var id = bestScore > 0 ? bestId : null;
        ARTIST_CACHE[key] = id;
        return id;
      })
      .catch(function () {
        ARTIST_CACHE[key] = null;
        return null;
      });
  }

  function lookupViaArtist(artist, title, year) {
    return resolveArtistId(artist).then(function (aid) {
      if (!aid) return null;
      return fetch(
        "https://itunes.apple.com/lookup?id=" + aid + "&entity=album&limit=200"
      )
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          var albums = (data.results || []).filter(function (h) {
            return h.collectionType === "Album" || h.wrapperType === "collection";
          });
          return pickAlbum(albums, artist, title, year);
        });
    });
  }

  function lookupViaSearch(artist, title, year) {
    return fetch(
      "https://itunes.apple.com/search?term=" +
        encodeURIComponent(artist + " " + title) +
        "&entity=album&limit=15"
    )
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        return pickAlbum(data.results || [], artist, title, year);
      });
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
    var year = parseYear(img.getAttribute("data-cover-year"));
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

    return lookupViaArtist(artist, album, year)
      .then(function (hit) {
        if (hit) return hit;
        return lookupViaSearch(artist, album, year);
      })
      .then(function (hit) {
        if (!hit) {
          applyFallback(img);
          return;
        }
        var urls = artworkFrom(hit);
        try {
          sessionStorage.setItem(key, JSON.stringify(urls));
        } catch (e) {}
        applyCover(img, urls.cover, urls.apple);
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
