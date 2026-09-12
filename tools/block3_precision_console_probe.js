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

async function main() {
  const normalUrl = process.argv[2];
  const emptyUrl = process.argv[3];
  if (!normalUrl || !emptyUrl) throw new Error("normal and empty fixture URLs are required");
  const browser = await chromium.launch(browserLaunchOptions());
  try {
    const page = await browser.newPage({ viewport: { width: 640, height: 720 } });
    await page.goto(normalUrl, { waitUntil: "networkidle" });
    const normal = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      evidence: document.querySelector("#context-evidence").textContent,
      disposition: document.querySelector("#context-disposition").textContent,
      busy: document.querySelector("main").getAttribute("aria-busy"),
      undersized: [...document.querySelectorAll("button")]
        .filter((button) => button.getClientRects().length && !button.disabled)
        .map((button) => ({ text: button.innerText, box: button.getBoundingClientRect() }))
        .filter((item) => item.box.width < 44 || item.box.height < 44)
        .map((item) => item.text),
    }));

    await page.getByRole("button", { name: /Admisión/ }).click();
    const admissionFocus = await page.evaluate(() => document.activeElement.id);
    const admission = await page.locator("#admission-card").innerText();
    await page.getByRole("button", { name: /Señales/ }).click();
    const signalFocus = await page.evaluate(() => document.activeElement.id);
    const signals = await page.locator("#signals-list").innerText();
    await page.getByRole("button", { name: /Control/ }).click();
    const controlFocus = await page.evaluate(() => document.activeElement.id);
    const controls = await page.locator("#controls-list").innerText();

    await page.route("**/api/workspace", (route) => route.fulfill({
      status: 409,
      contentType: "application/json",
      body: JSON.stringify({ error: "Fallo acotado de prueba" }),
    }));
    await page.getByRole("button", { name: "Actualizar evidencia" }).click();
    await page.locator("#error").waitFor({ state: "visible" });
    const failure = await page.evaluate(() => ({
      stale: document.querySelector("main").dataset.evidenceState,
      disposition: document.querySelector("#context-disposition").textContent,
      error: document.querySelector("#error").innerText,
      visiblePanels: [...document.querySelectorAll("[data-panel]")].filter((panel) => !panel.hidden).length,
    }));

    const emptyPage = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await emptyPage.goto(emptyUrl, { waitUntil: "networkidle" });
    await emptyPage.getByRole("button", { name: /Señales/ }).click();
    const emptySignals = await emptyPage.locator("#signals-list").innerText();
    await emptyPage.getByRole("button", { name: /Control/ }).click();
    const emptyControls = await emptyPage.locator("#controls-list").innerText();

    const result = { normal, admissionFocus, admission, signalFocus, signals, controlFocus, controls, failure, emptySignals, emptyControls };
    console.log(JSON.stringify(result, null, 2));
    if (
      normal.overflow !== 0 ||
      normal.undersized.length ||
      normal.evidence !== "SYNTHETIC_DETERMINISTIC_NOT_EVIDENCE" ||
      normal.disposition !== "CONTINUE" ||
      normal.busy !== "false" ||
      admissionFocus !== "admission-heading" ||
      !admission.includes("SIN_BLOQUEOS_DECLARADOS") ||
      signalFocus !== "signals-heading" ||
      !signals.includes("Hipótesis") ||
      !signals.includes("Señales gobernadas") ||
      controlFocus !== "control-heading" ||
      !controls.includes("Acciones prohibidas") ||
      failure.stale !== "stale" ||
      failure.disposition !== "RETURN_UPSTREAM" ||
      failure.visiblePanels !== 0 ||
      !failure.error.includes("No se realizó contacto, delivery ni escritura en CRM") ||
      !emptySignals.includes("Sin señales gobernadas") ||
      !emptyControls.includes("Sin controles declarados")
    ) process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
