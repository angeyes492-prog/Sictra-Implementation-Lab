"use strict";

const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

async function main() {
  const [block2Url, block3Url, outputDirectory] = process.argv.slice(2);
  if (!block2Url || !block3Url || !outputDirectory) {
    throw new Error("Block 2 URL, Block 3 URL, and output directory are required");
  }
  fs.mkdirSync(outputDirectory, { recursive: true });
  const candidates = [
    process.env.SICTRA_A11Y_BROWSER,
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  ].filter(Boolean);
  const executablePath = candidates.find((candidate) => fs.existsSync(candidate));
  const browser = await chromium.launch(executablePath ? { headless: true, executablePath } : { headless: true });
  try {
    for (const [name, url] of [["block2", block2Url], ["block3", block3Url]]) {
      for (const viewport of [{ label: "desktop", width: 1440, height: 1000 }, { label: "narrow", width: 640, height: 900 }]) {
        const page = await browser.newPage({ viewport });
        const errors = [];
        page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
        page.on("pageerror", (error) => errors.push(error.message));
        await page.goto(url, { waitUntil: "networkidle" });
        await page.screenshot({ path: path.join(outputDirectory, `${name}-${viewport.label}.png`), fullPage: true });
        if (viewport.label === "desktop") {
          const views = name === "block2" ? ["create", "ops"] : ["admission", "signals", "control"];
          for (const view of views) {
            await page.locator(`[data-view="${view}"]`).click();
            await page.screenshot({ path: path.join(outputDirectory, `${name}-${view}.png`), fullPage: true });
          }
        }
        if (errors.length) throw new Error(`${name}/${viewport.label} console errors: ${errors.join(" | ")}`);
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
