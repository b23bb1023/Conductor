/* The Excalidraw-look engine. One call per scene:
 *
 *   await EX.ready();  EX.build(sceneEl, tl, DUR);
 *
 * It draws a rough.js outline behind every .bx / .pill / .note / .card, rough
 * underlines, highlights, crosses and arrows, then adds one tween per element
 * that carries data-t (seconds from scene start, written by tools/build.py from
 * the narration's word timings). Everything is seeded, so every render is the
 * same drawing.
 */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const hash = (s) => { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return (h >>> 0) % 100000 + 1; };
  const css = (el, name, fallback) => (getComputedStyle(el).getPropertyValue(name) || "").trim() || fallback;

  function svgFor(el, w, h, pad) {
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "rough");
    svg.setAttribute("width", w + pad * 2); svg.setAttribute("height", h + pad * 2);
    svg.setAttribute("viewBox", `${-pad} ${-pad} ${w + pad * 2} ${h + pad * 2}`);
    svg.style.cssText = `position:absolute;left:${-pad}px;top:${-pad}px;overflow:visible;pointer-events:none;z-index:-1`;
    el.insertBefore(svg, el.firstChild);
    return svg;
  }
  const rrect = (w, h, r) => { r = Math.min(r, w / 2, h / 2); return `M${r} 0H${w - r}Q${w} 0 ${w} ${r}V${h - r}Q${w} ${h} ${w - r} ${h}H${r}Q0 ${h} 0 ${h - r}V${r}Q0 0 ${r} 0Z`; };

  // Hidden scenes report zero sizes: show the ancestors while measuring.
  function unhide(el) {
    const undo = [];
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      if (getComputedStyle(n).display === "none") { undo.push([n, n.style.display]); n.style.setProperty("display", "block", "important"); }
    }
    return () => undo.forEach(([n, v]) => { n.style.display = v; });
  }

  function drawBoxes(scene, sid) {
    scene.querySelectorAll(".bx,.pill,.note,.card,.term,.shot,.stamp,.bar").forEach((el, i) => {
      const w = el.offsetWidth, h = el.offsetHeight;
      if (!w || !h) return;
      const seed = hash(sid + ":" + i);
      const svg = svgFor(el, w, h, 8), rc = rough.svg(svg);
      const stroke = css(el, "--s", "#e9ecef"), fill = css(el, "--f", "none");
      const r = el.classList.contains("pill") ? h / 2 : parseFloat(css(el, "--r", "14"));
      const dashed = el.hasAttribute("data-dashed");
      svg.appendChild(rc.path(rrect(w, h, r), {
        seed, roughness: parseFloat(css(el, "--rough", "1")), bowing: 1, stroke, strokeWidth: parseFloat(css(el, "--sw", "2.6")),
        fill: fill === "none" ? undefined : fill, fillStyle: "solid", strokeLineDash: dashed ? [10, 9] : undefined,
        disableMultiStroke: dashed, preserveVertices: true,
      }));
    });
    // rough underline / marker highlight / strike / cross / ring on any element
    scene.querySelectorAll("[data-mark]").forEach((el, i) => {
      if (getComputedStyle(el).position === "static") { el.style.position = "relative"; if (getComputedStyle(el).display === "inline") el.style.display = "inline-block"; }
      const w = el.offsetWidth, h = el.offsetHeight, seed = hash(sid + "m" + i);
      if (!w || !h) return;
      const svg = svgFor(el, w, h, 14), rc = rough.svg(svg);
      const col = css(el, "--m", "#ffd43b");
      svg.classList.add("mark"); svg.style.zIndex = el.dataset.mark === "hl" ? -1 : 3;
      for (const kind of el.dataset.mark.split(" ")) {
        if (kind === "ul") svg.appendChild(rc.line(-4, h + 4, w + 4, h + 3, { seed, stroke: col, strokeWidth: 3.2, roughness: 1.3 }));
        if (kind === "hl") { const n = rc.line(-6, h * 0.6, w + 6, h * 0.58, { seed, stroke: col, strokeWidth: h * 0.62, roughness: 0.9, disableMultiStroke: true }); n.style.opacity = 0.3; svg.appendChild(n); }
        if (kind === "strike") svg.appendChild(rc.line(-8, h * 0.56, w + 8, h * 0.5, { seed, stroke: col, strokeWidth: 3.6, roughness: 1.4 }));
        if (kind === "x") { svg.appendChild(rc.line(4, 4, w - 4, h - 4, { seed, stroke: col, strokeWidth: 4.5, roughness: 1.4 })); svg.appendChild(rc.line(w - 4, 4, 4, h - 4, { seed: seed + 3, stroke: col, strokeWidth: 4.5, roughness: 1.4 })); }
        if (kind === "ring") svg.appendChild(rc.ellipse(w / 2, h / 2, w + 22, h + 18, { seed, stroke: col, strokeWidth: 3.4, roughness: 1.6 }));
        if (kind === "box") svg.appendChild(rc.rectangle(-6, -5, w + 12, h + 10, { seed, stroke: col, strokeWidth: 3.4, roughness: 1.5 }));
      }
    });
  }

  // <i class="arrow" data-from="#a" data-to="#b" data-fs="r" data-ts="l"> : sides are l r t b
  function drawArrows(scene, sid) {
    const base = scene.getBoundingClientRect();
    const scale = base.width / scene.offsetWidth || 1;
    const pt = (el, side, off) => {
      const r = el.getBoundingClientRect();
      const x0 = (r.left - base.left) / scale, y0 = (r.top - base.top) / scale, w = r.width / scale, h = r.height / scale;
      const g = 10, o = off || 0;
      return { l: [x0 - g, y0 + h / 2 + o], r: [x0 + w + g, y0 + h / 2 + o], t: [x0 + w / 2 + o, y0 - g], b: [x0 + w / 2 + o, y0 + h + g] }[side];
    };
    scene.querySelectorAll("i.arrow").forEach((el, i) => {
      const a = scene.querySelector(el.dataset.from), b = scene.querySelector(el.dataset.to);
      if (!a || !b) { console.error("arrow: missing endpoint", el.dataset.from, el.dataset.to); return; }
      const fs = el.dataset.fs || "r", ts = el.dataset.ts || "l";
      const [x1, y1] = pt(a, fs, +(el.dataset.fo || 0)), [x2, y2] = pt(b, ts, +(el.dataset.to2 || 0));
      const seed = hash(sid + "a" + i), col = css(el, "--s", "#e9ecef");
      const svg = document.createElementNS(NS, "svg");
      svg.setAttribute("width", scene.offsetWidth); svg.setAttribute("height", scene.offsetHeight);
      svg.style.cssText = "position:absolute;left:0;top:0;overflow:visible;pointer-events:none";
      el.style.cssText += ";position:absolute;left:0;top:0;width:100%;height:100%;display:block;pointer-events:none";
      el.appendChild(svg);
      const rc = rough.svg(svg), o = { seed, stroke: col, strokeWidth: 2.6, roughness: 0.9, strokeLineDash: el.hasAttribute("data-dashed") ? [9, 8] : undefined };
      const bend = +(el.dataset.bend || 0);
      const mx = (x1 + x2) / 2, my = (y1 + y2) / 2, dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1;
      const cx = mx - dy / len * bend, cy = my + dx / len * bend;
      svg.appendChild(bend ? rc.path(`M${x1} ${y1}Q${cx} ${cy} ${x2} ${y2}`, o) : rc.line(x1, y1, x2, y2, o));
      const ang = Math.atan2(y2 - cy, x2 - cx), L = 17, sp = 0.48;
      const head = { seed: seed + 1, stroke: col, strokeWidth: 2.6, roughness: 0.6 };
      svg.appendChild(rc.line(x2, y2, x2 - L * Math.cos(ang - sp), y2 - L * Math.sin(ang - sp), head));
      svg.appendChild(rc.line(x2, y2, x2 - L * Math.cos(ang + sp), y2 - L * Math.sin(ang + sp), head));
      // wipe direction for the reveal
      const horiz = Math.abs(dx) >= Math.abs(dy);
      const lo = Math.min(x1, x2) - 24, hi = scene.offsetWidth - Math.max(x1, x2) - 24, to = Math.min(y1, y2) - 24, bo = scene.offsetHeight - Math.max(y1, y2) - 24;
      el._wipe = horiz ? (dx >= 0 ? [`inset(${to}px ${scene.offsetWidth - lo}px ${bo}px ${lo}px)`, `inset(${to}px ${hi}px ${bo}px ${lo}px)`]
                                  : [`inset(${to}px ${hi}px ${bo}px ${scene.offsetWidth - hi}px)`, `inset(${to}px ${hi}px ${bo}px ${lo}px)`])
                       : (dy >= 0 ? [`inset(${to}px ${hi}px ${scene.offsetHeight - to}px ${lo}px)`, `inset(${to}px ${hi}px ${bo}px ${lo}px)`]
                                  : [`inset(${scene.offsetHeight - bo}px ${hi}px ${bo}px ${lo}px)`, `inset(${to}px ${hi}px ${bo}px ${lo}px)`]);
    });
  }

  const FMT = {
    int: (v) => Math.round(v).toLocaleString("en-US"),
    plain: (v) => String(Math.round(v)),
    d1: (v) => v.toFixed(1), d2: (v) => v.toFixed(2),
  };

  function animate(scene, tl, dur) {
    const num = (v, d) => (v === undefined || v === "" ? d : parseFloat(v));
    scene.querySelectorAll("[data-t]").forEach((el) => {
      const t = num(el.dataset.t, 0), kind = el.dataset.in || (el.classList.contains("arrow") ? "wipe" : "pop");
      const rot = num(el.dataset.rot, 0);
      if (kind === "pop") tl.fromTo(el, { opacity: 0, scale: 0.55, rotation: rot }, { opacity: 1, scale: 1, rotation: rot, duration: 0.24, ease: "back.out(2.2)" }, t);
      else if (kind === "stamp") tl.fromTo(el, { opacity: 0, scale: 2.3, rotation: rot - 9 }, { opacity: 1, scale: 1, rotation: rot, duration: 0.17, ease: "power3.in" }, t);
      else if (kind === "fade") tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: num(el.dataset.d, 0.22), ease: "power1.out" }, t);
      else if (kind === "rise") tl.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }, t);
      else if (kind === "wipe") {
        const w = el._wipe || ["inset(-12px 100% -12px -12px)", "inset(-12px -12px -12px -12px)"];
        tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t);
        tl.fromTo(el, { clipPath: w[0] }, { clipPath: w[1], duration: num(el.dataset.d, 0.32), ease: "power2.out" }, t);
      } else if (kind === "type") {
        const n = Math.max(2, (el.textContent || "").length);
        tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t);
        tl.fromTo(el, { clipPath: "inset(-6px 100% -6px 0px)" }, { clipPath: "inset(-6px 0% -6px 0px)", duration: num(el.dataset.d, Math.min(1.4, n * 0.03)), ease: `steps(${n})` }, t);
      } else if (kind === "grow") {
        tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t);
        tl.fromTo(el, { scaleX: 0.001, transformOrigin: "0% 50%" }, { scaleX: 1, transformOrigin: "0% 50%", duration: num(el.dataset.d, 0.6), ease: "power2.out" }, t);
      }
      if (el.dataset.count !== undefined) {
        const f = FMT[el.dataset.fmt || "int"], from = num(el.dataset.from, 0), to = parseFloat(el.dataset.count);
        el.textContent = f(from);
        tl.fromTo(el, { textContent: from }, { textContent: to, duration: num(el.dataset.cd, 0.7), ease: "power2.out", immediateRender: false, modifiers: { textContent: (v) => f(parseFloat(v)) } }, num(el.dataset.ct, t + 0.05));
      }
    });
    scene.querySelectorAll("[data-out]").forEach((el) => tl.to(el, { opacity: 0, duration: 0.14, ease: "power1.in", immediateRender: false }, parseFloat(el.dataset.out)));
    scene.querySelectorAll("[data-dim]").forEach((el) => tl.to(el, { opacity: 0.25, duration: 0.2, immediateRender: false }, parseFloat(el.dataset.dim)));
    // marks (underline, ring, cross) drawn on an element appear with data-mt, or with the element
    scene.querySelectorAll("[data-mark]").forEach((el) => {
      const svg = el.querySelector(":scope > svg.mark"); if (!svg) return;
      const t = el.dataset.mt !== undefined ? parseFloat(el.dataset.mt) : (el.dataset.t !== undefined ? parseFloat(el.dataset.t) + 0.12 : 0);
      tl.fromTo(svg, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t);
      tl.fromTo(svg, { clipPath: "inset(-20px 100% -20px -20px)" }, { clipPath: "inset(-20px -20px -20px -20px)", duration: 0.26, ease: "power2.out" }, t);
    });
    tl.to({}, { duration: 0.001 }, Math.max(0, dur - 0.001));   // pad the timeline to the scene length
  }

  window.EX = {
    async ready() {
      await Promise.all([document.fonts.load('40px "Excalifont"'), document.fonts.load('30px "Comic Shanns"')]);
      await document.fonts.ready;
    },
    build(scene, tl, dur) {
      const sid = scene.id, undo = unhide(scene);
      try { drawBoxes(scene, sid); drawArrows(scene, sid); } finally { undo(); }
      animate(scene, tl, dur);
    },
  };
})();
