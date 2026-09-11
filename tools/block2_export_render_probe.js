"use strict";

const fs = require("node:fs");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

function browserLaunchOptions() {
  const candidates = [
    process.env.SICTRA_A11Y_BROWSER,
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  ].filter(Boolean);
  const executablePath = candidates.find((candidate) => fs.existsSync(candidate));
  return executablePath ? { headless: true, executablePath } : { headless: true };
}

async function inspectHtml(browser, filePath) {
  const page = await browser.newPage({ viewport: { width: 600, height: 800 } });
  try {
    await page.goto(pathToFileURL(filePath).href, { waitUntil: "load" });
    return await page.evaluate(() => ({
      mainCount: document.querySelectorAll("main").length,
      headingCount: document.querySelectorAll("h1").length,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      text: document.body.innerText.trim(),
    }));
  } finally {
    await page.close();
  }
}

async function inspectSvg(browser, filePath) {
  const page = await browser.newPage({ viewport: { width: 600, height: 800 } });
  try {
    await page.goto(pathToFileURL(filePath).href, { waitUntil: "load" });
    return await page.evaluate(() => {
      const svg = document.querySelector("svg");
      const viewBox = svg.viewBox.baseVal;
      const textBoxes = [...svg.querySelectorAll("text")].map((item) => {
        const box = item.getBBox();
        return { x: box.x, y: box.y, right: box.x + box.width, bottom: box.y + box.height };
      });
      return {
        role: svg.getAttribute("role"),
        labelledby: svg.getAttribute("aria-labelledby"),
        title: svg.querySelector("title")?.textContent.trim() || "",
        description: svg.querySelector("desc")?.textContent.trim() || "",
        tspanCount: svg.querySelectorAll("tspan").length,
        viewBox: { width: viewBox.width, height: viewBox.height },
        overflowingText: textBoxes.filter((box) =>
          box.x < 0 || box.y < 0 || box.right > viewBox.width || box.bottom > viewBox.height
        ),
      };
    });
  } finally {
    await page.close();
  }
}

async function main() {
  const [htmlPath, svgPath] = process.argv.slice(2);
  if (!htmlPath || !svgPath) throw new Error("usage: node block2_export_render_probe.js <html> <svg>");
  const browser = await chromium.launch(browserLaunchOptions());
  try {
    const result = { html: await inspectHtml(browser, htmlPath), svg: await inspectSvg(browser, svgPath) };
    console.log(JSON.stringify(result, null, 2));
    if (
      result.html.mainCount !== 1 || result.html.headingCount < 1 || result.html.overflow !== 0 || !result.html.text ||
      result.svg.role !== "img" || result.svg.labelledby !== "title desc" || !result.svg.title ||
      !result.svg.description || result.svg.tspanCount < 1 || result.svg.overflowingText.length
    ) process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
