"use strict";

const { chromium } = require("playwright");
const fs = require("node:fs");

function browserLaunchOptions() {
  const candidates = [
    process.env.SICTRA_A11Y_BROWSER,
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  ].filter(Boolean);
  const executablePath = candidates.find((candidate) => fs.existsSync(candidate));
  return executablePath ? { headless: true, executablePath } : { headless: true };
}

async function visibleControls(page, view) {
  return page.locator("button,input,select,textarea").evaluateAll((elements, currentView) =>
    elements
      .filter((element) => element.getClientRects().length > 0)
      .map((element) => {
        const label = element.labels?.[0]?.innerText.trim() || "";
        const name = (
          element.getAttribute("aria-label") || label || element.innerText || element.value || ""
        ).trim();
        const bounds = element.getBoundingClientRect();
        return {
          view: currentView,
          tag: element.tagName,
          type: element.type || "",
          name,
          width: Math.round(bounds.width),
          height: Math.round(bounds.height),
          disabled: element.disabled,
        };
      }), view
  );
}

async function keyboardTrail(page, view) {
  await page.locator("body").focus();
  const trail = [];
  const seen = new Set();
  for (let index = 0; index < 120; index += 1) {
    await page.keyboard.press("Tab");
    const current = await page.evaluate(() => {
      const element = document.activeElement;
      const bounds = element.getBoundingClientRect();
      const name = (
        element.getAttribute("aria-label") || element.labels?.[0]?.innerText ||
        element.innerText || element.value || ""
      ).trim();
      return {
        tag: element.tagName,
        name,
        visible: element.getClientRects().length > 0 && bounds.width > 0 && bounds.height > 0,
        disabled: element.disabled || false,
        key: `${element.tagName}:${element.id}:${element.name}:${name}`,
      };
    });
    if (current.tag === "BODY") break;
    if (seen.has(current.key)) break;
    seen.add(current.key);
    trail.push({ view, ...current });
  }
  return trail;
}

async function main() {
  const url = process.argv[2] || "http://127.0.0.1:8766/";
  const browser = await chromium.launch(browserLaunchOptions());
  try {
    const page = await browser.newPage({ viewport: { width: 640, height: 720 } });
    await page.goto(url, { waitUntil: "networkidle" });

    const reflow = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    }));
    const studioControls = await visibleControls(page, "studio");

    await page.keyboard.press("Tab");
    const firstFocus = await page.evaluate(() => ({
      tag: document.activeElement.tagName,
      text: (document.activeElement.innerText || "").trim(),
      href: document.activeElement.getAttribute("href"),
    }));
    await page.keyboard.press("Enter");
    const skipTarget = await page.evaluate(() => document.activeElement.id);
    await page.getByRole("button", { name: /Create/ }).click();
    const createVisible = await page.locator("#create-view").isVisible();
    const createControls = await visibleControls(page, "create");
    const createTrail = await keyboardTrail(page, "create");
    await page.getByRole("button", { name: /Ops/ }).click();
    const opsVisible = await page.locator("#ops-view").isVisible();
    const opsControls = await visibleControls(page, "ops");
    const opsTrail = await keyboardTrail(page, "ops");
    await page.getByRole("button", { name: /Studio/ }).click();
    const studioTrail = await keyboardTrail(page, "studio");
    const controls = [...studioControls, ...createControls, ...opsControls];
    await page.emulateMedia({ reducedMotion: "reduce" });
    const reducedMotionDuration = await page.evaluate(
      () => getComputedStyle(document.querySelector(".compile-button")).transitionDuration
    );

    const result = {
      url,
      viewport: "640x720 (1280px at 200% equivalent)",
      reflow,
      controlCount: controls.length,
      namelessControls: controls.filter((control) => !control.name),
      undersizedControls: controls.filter(
        (control) =>
          control.type !== "checkbox" &&
          !control.disabled &&
          (control.width < 44 || control.height < 44)
      ),
      firstFocus,
      skipTarget,
      createVisible,
      opsVisible,
      reducedMotionDuration,
      keyboardTrail: [...studioTrail, ...createTrail, ...opsTrail],
    };
    result.hiddenFocusStops = result.keyboardTrail.filter((item) => !item.visible && !item.disabled);
    result.namelessFocusStops = result.keyboardTrail.filter(
      (item) => !item.name && !item.disabled && item.tag !== "MAIN"
    );
    result.lineageFocusStop = result.keyboardTrail.find(
      (item) => item.tag === "OL" && item.key.includes("lineage-ribbon")
    ) || null;
    console.log(JSON.stringify(result, null, 2));
    if (
      result.reflow.overflow !== 0 ||
      result.namelessControls.length ||
      result.undersizedControls.length ||
      result.hiddenFocusStops.length ||
      result.namelessFocusStops.length ||
      !result.lineageFocusStop ||
      result.lineageFocusStop.name !== "Progreso de los motores de diseño" ||
      result.skipTarget !== "studio" ||
      !result.createVisible ||
      !result.opsVisible
    ) {
      process.exitCode = 1;
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
