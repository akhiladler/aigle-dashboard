/* Presentation translations only. The approved source Map stays immutable. */
var MondayLanguage = (function () {
  'use strict';
  var original, dictionary, renderMap, language = 'en', sourceHash = '', serial = 0;
  function translated(value) {
    if (typeof value === 'string') return dictionary[value] || value;
    if (Array.isArray(value)) return value.map(translated);
    if (value && typeof value === 'object') {
      var out = {}; Object.keys(value).forEach(function (k) { out[k] = translated(value[k]); }); return out;
    }
    return value;
  }
  function choose(next) {
    if (!original || (next === 'id' && !dictionary)) return;
    language = next;
    var model = next === 'id' ? translated(original) : JSON.parse(JSON.stringify(original));
    model.presentation_language = next;
    renderMap(model);
    if (next === 'id') {
      var walker = document.createTreeWalker(document.querySelector('section.panel[data-panel="map"]'), NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) { var node = walker.currentNode; if (dictionary[node.textContent]) node.textContent = dictionary[node.textContent]; }
    }
    document.documentElement.lang = next;
    var week = document.querySelector('.tab[data-go="map"]');
    if (week) week.textContent = next === 'id' ? 'Pekan Ini' : 'This Week';
    var live = document.getElementById('live');
    if (live && next === 'id') live.textContent = live.textContent.replace('Meeting prep - September 13, 2026', 'Persiapan rapat - 13 September 2026');
    document.querySelectorAll('[data-map-language]').forEach(function (button) {
      var active = button.dataset.mapLanguage === next;
      button.classList.toggle('on', active); button.setAttribute('aria-pressed', String(active));
    });
    var url = new URL(location.href); url.searchParams.set('lang', next); history.replaceState(null, '', url);
  }
  async function load(raw, model, base, render, staticMode) {
    var version = ++serial;
    original = JSON.parse(JSON.stringify(model)); dictionary = null; renderMap = render;
    renderMap(JSON.parse(JSON.stringify(original))); document.documentElement.lang = model.presentation_language || 'en';
    if (staticMode) return; // Preserve frozen album rendering.
    try {
      var hash = await crypto.subtle.digest('SHA-256', raw);
      sourceHash = Array.from(new Uint8Array(hash)).map(function (x) {return x.toString(16).padStart(2, '0');}).join('');
      var response = await fetch(base + 'indonesian.json', {cache:'no-store'});
      if (!response.ok) return;
      var bundle = await response.json();
      if (version !== serial || bundle.source_sha256 !== sourceHash || bundle.cycle_id !== model.cycle_id) return;
      dictionary = bundle.translations;
      if (!dictionary || typeof dictionary !== 'object') return;
      var bar = document.createElement('div'); bar.className = 'langbar'; bar.setAttribute('aria-label', 'Map language');
      [['en','English'],['id','Bahasa Indonesia']].forEach(function (item) {
        var button = document.createElement('button'); button.type = 'button'; button.className = 'lang';
        button.textContent = item[1]; button.dataset.mapLanguage = item[0];
        button.addEventListener('click', function () { choose(item[0]); }); bar.appendChild(button);
      });
      var old = document.querySelector('[aria-label="Map language"]'); if (old) old.remove();
      document.querySelector('.topright').appendChild(bar);
      choose(new URLSearchParams(location.search).get('lang') === 'id' ? 'id' : 'en');
    } catch (error) { console.warn('Map translation unavailable; original edition retained.'); }
  }
  return {load:load};
}());
