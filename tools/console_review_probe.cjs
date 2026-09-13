const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const output = path.resolve('.runtime/console-review');
  fs.mkdirSync(output, {recursive:true});
  const edge = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(fs.existsSync);
  const browser = await chromium.launch({headless:true, ...(edge ? {executablePath:edge} : {})});
  const results = [];
  try {
    for (const [index, url] of process.argv.slice(2).entries()) {
      const block = index + 2;
      const page = await browser.newPage({viewport:{width:1440,height:1100}});
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      await page.locator('main[aria-busy="false"]').waitFor();
      assert.equal(await page.locator('#error').isVisible(), false, `B${block} initial load`);
      if (block === 4) {
        await page.locator('#audit-events li').first().waitFor();
        assert.equal(await page.locator('#case-count').innerText(), '2');
        await page.locator('#state-filter').selectOption('blocked');
        assert.equal(await page.locator('.case').count(), 1);
        assert.match(await page.locator('#case-detail').innerText(), /Devuelto al origen/);
        assert.doesNotMatch(await page.locator('#case-detail').innerText(), /El recorrido se detuvo para revisión humana/);
        await page.locator('#search').fill('no-match');
        assert.equal(await page.locator('.case').count(), 0);
        assert.equal(await page.locator('#audit-events li').count(), 0);
        await page.locator('#search').fill('');
        await page.locator('#state-filter').selectOption('review');
        await page.locator('#audit-events li').first().waitFor();
        assert.equal(await page.locator('#audit-events li').count(), 4);
        await page.locator('#state-filter').selectOption('all');
      } else {
        for (const view of block === 2 ? ['create','ops','studio'] : ['admission','signals','control','accounts']) {
          await page.locator(`[data-view="${view}"]`).click();
          assert.equal(await page.locator(`[data-view="${view}"]`).getAttribute('aria-current'), 'page');
        }
      }
      await page.screenshot({path:path.join(output,`block${block}-desktop.png`), fullPage:true});
      for (const width of [1024, 390]) {
        await page.setViewportSize({width,height:900});
        const overflow = await page.evaluate(()=>document.documentElement.scrollWidth > window.innerWidth);
        if (overflow) {
          console.log(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>window.innerWidth && getComputedStyle(e).position!=='absolute').map(e=>({tag:e.tagName,cls:e.className,width:e.getBoundingClientRect().width})).slice(0,18)));
          await page.screenshot({path:path.join(output,`block${block}-overflow.png`),fullPage:true});
        }
        assert.equal(overflow,false,`B${block} overflow at ${width}`);
        const suiteSelector = block===2 ? '.suite-links a' : block===3 ? '.suite a' : '.rail nav a';
        assert.equal(await page.locator(suiteSelector).first().isVisible(), true, `B${block} suite navigation at ${width}`);
        if(width===390) await page.screenshot({path:path.join(output,`block${block}-mobile.png`),fullPage:true});
      }
      if(block===4) {
        await page.route('**/api/cases', route=>route.fulfill({status:409,contentType:'application/json',body:'{"error":"JOURNAL_INTEGRITY_ERROR"}'}));
        await page.locator('#refresh').click();
        await page.locator('#error').waitFor();
        assert.equal(await page.locator('#case-count').innerText(),'—');
        assert.equal(await page.locator('#review-count').innerText(),'—');
        assert.equal(await page.locator('.case').count(),0);
        assert.equal(await page.locator('#audit-events li').count(),0);
        await page.unroute('**/api/cases');
        await page.locator('#retry').click();
        await page.locator('.case').first().waitFor();
        assert.equal(await page.locator('#error').isVisible(),false);
      }
      assert.deepEqual(errors,[],`B${block} JavaScript errors`);
      results.push({block, result:'PASS', sizes:[1440,1024,390]});
      await page.close();
    }
    console.log(JSON.stringify(results,null,2));
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
