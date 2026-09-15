const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async()=>{
 const urls=process.argv.slice(2);
 assert.equal(urls.length,4);
 const edge=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(fs.existsSync);
 const browser=await chromium.launch({headless:true,...(edge?{executablePath:edge}:{})});
 const context=await browser.newContext({viewport:{width:1440,height:1050}});
 const page=await context.newPage();
 const errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 try{
  await page.goto(urls[3]);
  for(const block of [1,2,3,4]){
   // Isolated servers use ephemeral ports; change only href, never target.
   const link=await page.locator('a[href="http://127.0.0.1:'+ (8764+block) +'/"]').first().elementHandle();
   await link.evaluate((element,url)=>element.href=url,urls[block-1]);
   await Promise.all([page.waitForURL(url=>url.origin===urls[block-1],{waitUntil:'domcontentloaded'}),link.click()]);
   assert.equal(context.pages().length,1,'block navigation must not open a popup');
   assert.equal(await page.locator('body').getAttribute('data-telecare-block'),String(block));
   for(const asset of ['/suite.css','/suite-icons.svg','/suite-hero.png']){
    const response=await page.request.get(urls[block-1]+asset);
    assert.equal(response.status(),200);
   }
  }
  await page.goBack();
  assert.equal(await page.locator('body').getAttribute('data-telecare-block'),'3');
  await page.goto(urls[0]);
  await page.locator('#loading').waitFor({state:'hidden'});
  for(const width of [1440,1024,390]){
   await page.setViewportSize({width,height:1050});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'B1 overflow '+width);
   assert.equal(await page.locator('.suite-links a').first().isVisible(),true);
   assert.equal(await page.locator('[data-view="overview"] .suite-icon').isVisible(),true);
   await page.screenshot({path:path.resolve('.runtime/console-review/block1-'+width+'.png'),fullPage:true});
  }
  assert.deepEqual(errors,[]);
  console.log('PASS: 4→1→2→3→4 in one tab, history, assets and Block 1 responsive icons');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
